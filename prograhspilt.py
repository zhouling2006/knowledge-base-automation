#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
将 Markdown 教材内容按细粒度、语义独立完整的原则切分为知识点段落，
输出符合数据库 content_segments 表结构的 JSON 数组。
"""

import sys
import io
import json
import time
import re
import sqlite3
import argparse
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from openai import OpenAI

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
MODEL = "qwen-plus"

if not DASHSCOPE_API_KEY:
    raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

# 修复 Windows 编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def lookup_section_id(section_name: str, db_path: str = None) -> str | None:
    """从章节数据库中根据小节名查找对应的 id"""
    if db_path is None:
        db_path = "chapters.db"
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # 先精确匹配 title
        cur.execute(
            "SELECT id FROM chapters WHERE title = ? LIMIT 1",
            (section_name,)
        )
        row = cur.fetchone()
        if row:
            conn.close()
            return str(row[0])
        # 再模糊匹配 number（当 section_name 只含编号时）
        cur.execute(
            "SELECT id FROM chapters WHERE number = ? LIMIT 1",
            (section_name,)
        )
        row = cur.fetchone()
        conn.close()
        return str(row[0]) if row else None
    except Exception:
        return None


def clean_content_whitespace(parsed_data):
    """清理 content 字段中多余的换行符和空格"""
    for segment in parsed_data:
        if 'content' in segment and segment['content']:
            # 将换行符和连续空白替换为单个空格
            content = re.sub(r'\s+', ' ', segment['content'])
            segment['content'] = content.strip()
    return parsed_data

def segment_knowledge_points(markdown_content: str, source: str, section: str, section_id: str = None) -> str:
    """调用大模型将教材内容切分为知识点段落，返回 JSON 字符串"""

    system_prompt = """你是专业教材结构化解析助手。
任务：将一段 Markdown 格式的教材内容，按**细粒度、语义独立完整**的原则切分为文本块（segment），并输出可直接用于数据库入库的标准 JSON 数组。

**前置信息（由调用方在 user_prompt 中传入，请直接使用，不要再询问）：**
- source：源文件相对路径，如 "第3章/3.1 导数的定义.md"
- section：所属小节名，如 "3.1 导数的定义"
- section_id：小节在章节表中的 ID（如不知道可填 null）

---

输出格式要求（严格遵循以下每个字段，不得遗漏、不得自创字段）：

{
    "source": "第3章/3.1 导数的定义.md",     // 来源文件路径，从 user_prompt 提取
    "section": "3.1 导数的定义",             // 所属小节名，从 user_prompt 提取
    "section_id": "1",                       // 小节ID，不知道则填 null（字符串）
    "position": 1,                           // 在当前章节内的顺序号（从1开始递增）

    "title": "导数的几何意义",               // 本块标题，无则 ""
    "content": "语义完整、简洁流畅的摘要...",   // LLM 对原文合理简化/压缩后的核心内容，保证语义完整
    "raw_content": "设非空数集 D ⊆ R，则称映射 f: D → R 为定义在 D 上的函数，记作 y = f(x), x ∈ D。其中 x 称为自变量，y 称为因变量，D 称为定义域，记作 Df，即 Df = D。",    // 原文内容，直接填入,保证公式能被json解析

    "type": "concept",                       // concept（概念）/ theorem（定理）/ proof（证明）/ example（例题）/ note（说明/推导）

    "aliases": [                             // 本块中出现的该概念的其他叫法/同义词（从原文提取）
        "切线斜率",
        "导数的几何解释"
    ],

    "entities": "导数,切线,函数",              // 本块中提到的其他关键实体名词，用逗号分隔的字符串

    "references": [                           // 含有关系连接词（如"即""也就是说""也就是""称为""定义为"等）的原文语句
        "导数，即切线的斜率"
    ],

    "confidence": 0.95,                       // LLM 提取置信度，0~1 之间
    "needs_review": false,                    // 置信度 < 0.8 或拿不准时为 true

    "summary": "简短摘要，一句话概括本块核心内容",  // 用于预览/检索

    "created_at": "当前ISO时间字符串，如 2026-01-15T10:30:00",
    "model": "qwen-plus",
    "version": 1,

    "embedding": null                         // 留空，后期扩展向量检索用
}

---

切分规则：
1. **粒度偏细**：一段一个独立知识点，语义完整、不重叠、不遗漏。定义、定理必须单独成段；同类型例题可适当合并，不同类型例题分开
2. **content 合理简化**：LLM 对原文进行语义完整前提下的压缩/精简，保留核心内容，不是逐字保留
3. **raw_content 填原文**：直接填原文内容，不要填位置
4. **图片/公式绑定**：Markdown 图片和 LaTeX 公式不单独分段，直接并入所属语义块，图片需要与其图片名绑定在一起，如 "图1.1.6" 直接并入含有该表标题的内容中，如果多块提及，就复制一份到每块中
5. **图表绑定**：「图1.1.6」「图2-3」等图表编号与紧邻图片绑定在同一段
6. **别名提取范围**：aliases 只针对 type 为 concept（概念）或 theorem（定理）的块提取，其他类型（example/proof/note）aliases 填 [] 即可。尽量找 0~3 个同义/相关名词
7. **实体名词过滤**：entities 只填有实质意义的专有名词（如具体函数名、具体定理名、具体概念名），常见通用符号或无实意词不填（如 "+"、"="、"的"、"与"、"或" 等），用逗号分隔，如 "导数,切线,函数,极限"
8. **references 保留关系语句**：填含有关系词（"即""也就是说""也就是""称为""定义为""也叫""也就是指"等）的原文语句

输出要求：**只返回纯标准 JSON 数组**，无多余文字、无解释、无注释、无 Markdown 包裹。数组内每个对象严格包含上述所有字段。"""

    user_prompt = f"""## 待切分内容

- **source（来源）**: {source}
- **section（小节名）**: {section}
- **section_id（小节ID）**: {section_id if section_id else "null"}

请将以下 Markdown 内容按规则切分为多个 segment 块，输出 JSON 数组：

{markdown_content}"""

    client = OpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=12000,
    )

    result = response.choices[0].message.content

    # 清洗可能出现的 Markdown 包裹
    result = result.strip()
    if result.startswith("```json"):
        result = result[7:]
    if result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]
    result = result.strip()

    return result

def main():
    parser = argparse.ArgumentParser(description='知识点切分')
    parser.add_argument('--input', '-i', default=None, help='输入Markdown文件')
    parser.add_argument('--output', '-o', default=None, help='输出JSON文件')
    parser.add_argument('--source', '-s', default=None, help='source字段')
    parser.add_argument('--section', default=None, help='section字段（小节名）')
    parser.add_argument('--section-id', default=None, help='section_id字段')
    parser.add_argument('--chapter-db', default=None, help='章节数据库路径')
    args = parser.parse_args()

    print("=" * 60)
    print("知识点切分：细粒度语义分段 → JSON 数组")
    print("=" * 60)

    # ========== 配置（命令行参数 > 配置文件） ==========
    # 配置文件默认值
    _input_path   = "二、函数的概念.md"
    _source       = "二、函数的概念.md"
    _section      = "函数的概念"
    _section_id   = None
    _chapter_db   = "chapters.db"

    input_path   = args.input if args.input else _input_path
    output_path  = args.output if args.output else "segments_output.json"
    source       = args.source if args.source else _source
    section      = args.section if args.section else _section
    section_id   = args.section_id if args.section_id else _section_id
    chapter_db   = args.chapter_db if args.chapter_db else _chapter_db
    # =================================================

    try:
        content = read_file(input_path)
        print(f"\n📖 教材大小: {len(content)} 字符")
    except FileNotFoundError:
        print(f"\n❌ 错误：找不到文件 {input_path}")
        return

    print("\n🤖 模型正在切分知识点...")
    print("   (可能需要 30-60 秒，请耐心等待)")
    
    start_time = time.time()

    try:
        result_json = segment_knowledge_points(content, source=source, section=section, section_id=section_id)

        # 自动从章节数据库查找 section_id（若未手动指定）
        if section_id is None:
            resolved = lookup_section_id(section, chapter_db)
            if resolved:
                section_id = resolved
                print(f"🔗 自动从章节库找到 section_id = {section_id}")
            else:
                print(f"⚠️  未在章节库中找到匹配的 section，section_id 将保持 null")

        # 验证是否为合法 JSON
        parsed = json.loads(result_json)

        # 后处理：统一 section_id（统一用查到的值，覆盖 LLM 写的 null）
        for seg in parsed:
            seg['section_id'] = section_id

        # 清理 content 中的换行符
        parsed = clean_content_whitespace(parsed)

        # 统一补 position 顺序号（从1开始，覆盖 LLM 可能乱填的 position）
        for i, seg in enumerate(parsed, start=1):
            seg['position'] = i

        # 统一填充元信息（自动取当前时间和模型信息）
        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        for seg in parsed:
            seg['created_at'] = now_str
            seg['model'] = MODEL
            seg['version'] = 1

        elapsed = time.time() - start_time
        print(f"\n✅ 切分成功，共生成 {len(parsed)} 个知识点段落")
        print(f"⏱️  处理耗时: {elapsed:.1f} 秒")

        # 统计各类型数量
        type_count = {}
        for seg in parsed:
            seg_type = seg.get('type', 'unknown')
            type_count[seg_type] = type_count.get(seg_type, 0) + 1
        
        if type_count:
            print("\n📊 段落类型统计:")
            for seg_type, count in type_count.items():
                print(f"  {seg_type}: {count}")

        # 打印前两个示例
        print("\n📋 示例（前2条）：")
        for i, seg in enumerate(parsed[:2]):
            print(f"\n--- 段落 {i+1} ---")
            print(f"  source:      {seg.get('source')}")
            print(f"  section:     {seg.get('section')}")
            print(f"  section_id:  {seg.get('section_id')}")
            print(f"  position:    {seg.get('position')}")
            print(f"  type:        {seg.get('type')}")
            print(f"  title:       {seg.get('title')}")
            print(f"  content:     {seg.get('content', '')[:80]}...")
            print(f"  raw_content: {seg.get('raw_content')}")
            print(f"  aliases:     {seg.get('aliases')}")
            print(f"  entities:    {seg.get('entities')}")
            print(f"  references: {seg.get('references')}")
            print(f"  confidence:  {seg.get('confidence')}")
            print(f"  summary:     {seg.get('summary')}")

        # 保存原始 JSON（保持模型原始输出）
        save_file(output_path, result_json)
        print(f"\n💾 完整结果已保存到 {output_path}")
        
        # 同时保存清理后的格式化版本
        pretty_path = output_path.replace('.json', '_pretty.json')
        with open(pretty_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        print(f"💾 清理后的格式化版本已保存到 {pretty_path}")

    except json.JSONDecodeError as e:
        print(f"\n❌ JSON 解析失败: {e}")
        print(f"错误位置: line {e.lineno}, column {e.colno}")
        print("\n模型返回的原始内容（前500字符）：")
        # 注意：这里 result_json 可能未定义，需要处理
        if 'result_json' in locals():
            print(result_json[:500])
            print("\n...（后500字符）：")
            print(result_json[-500:])
            # 保存原始响应供调试
            debug_path = "debug_response.txt"
            save_file(debug_path, result_json)
            print(f"\n🔍 完整响应已保存到 {debug_path}")
        else:
            print("无法获取模型返回内容")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

if __name__ == "__main__":
    main()