#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
知识点切分模块 - 可直接导入使用

用法:
    from split_segment import split_segment, split_and_append

    # 切分单个文件，返回结果列表
    result = split_segment(
        input_path="path/to/file.md",
        source="源文件路径",
        section="小节名"
    )

    # 追加到现有JSON文件
    split_and_append(
        input_path="path/to/file.md",
        source="源文件路径",
        section="小节名",
        output_path="第一章/segments_output_pretty.json"
    )
"""

import sys
import io
import json
import time
import re
import sqlite3
import os
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not DASHSCOPE_API_KEY:
    raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")
MODEL = "qwen-plus"

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def clean_content_whitespace(parsed_data):
    for segment in parsed_data:
        if 'content' in segment and segment['content']:
            content = re.sub(r'\s+', ' ', segment['content'])
            segment['content'] = content.strip()
    return parsed_data

def _call_llm(markdown_content: str, source: str, section: str, section_id: str = None) -> str:
    """调用GLM切分内容"""
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
4. **图片/公式绑定**：Markdown 图片和 LaTeX 公式不单独分段，直接并入所属语义块
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
    result = result.strip()
    if result.startswith("```json"):
        result = result[7:]
    if result.startswith("```"):
        result = result[3:]
    if result.endswith("```"):
        result = result[:-3]
    return result.strip()


def split_segment(input_path: str, source: str, section: str, section_id: str = None) -> list:
    """
    切分单个Markdown文件，返回知识点列表

    Args:
        input_path: 输入文件路径
        source: source字段值
        section: 小节名
        section_id: 小节ID（可选）

    Returns:
        list: 切分后的知识点列表
    """
    print(f"📖 读取文件: {input_path}")
    content = read_file(input_path)
    print(f"   内容长度: {len(content)} 字符")

    print("🤖 正在调用GLM切分...")
    print("   (可能需要 30-60 秒)")

    start_time = time.time()
    result_json = _call_llm(content, source, section, section_id)
    elapsed = time.time() - start_time
    print(f"   耗时: {elapsed:.1f} 秒")

    parsed = json.loads(result_json)
    parsed = clean_content_whitespace(parsed)

    # 统一补 position 顺序号
    for i, seg in enumerate(parsed, start=1):
        seg['position'] = i

    # 统一填充元信息
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    for seg in parsed:
        seg['created_at'] = now_str
        seg['model'] = MODEL
        seg['version'] = 1

    print(f"✅ 切分成功，生成 {len(parsed)} 个知识点")
    return parsed


def split_and_append(input_path: str, source: str, section: str, output_path: str, section_id: str = None) -> list:
    """
    切分单个文件并追加到现有JSON文件

    Args:
        input_path: 输入文件路径
        source: source字段值
        section: 小节名
        output_path: 输出JSON文件路径（增量追加）
        section_id: 小节ID（可选）

    Returns:
        list: 追加后的完整知识点列表
    """
    import os

    # 加载现有数据
    existing_data = []
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        print(f"📦 已加载 {len(existing_data)} 条已有数据")

    # 检查是否已处理（基于 source + section 判断）
    for item in existing_data:
        if item.get('source') == source and item.get('section') == section:
            print(f"⏭️ 已处理过，跳过: {source}")
            return existing_data

    # 切分新数据
    new_data = split_segment(input_path, source, section, section_id)

    # 追加并保存
    all_data = existing_data + new_data
    save_json(output_path, all_data)
    print(f"💾 已保存到 {output_path}，共 {len(all_data)} 条")

    return all_data


def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description='知识点切分')
    parser.add_argument('--input', '-i', required=True, help='输入Markdown文件')
    parser.add_argument('--source', '-s', required=True, help='source字段')
    parser.add_argument('--section', default=None, help='section字段（小节名）')
    parser.add_argument('--output', '-o', default='第一章/segments_output_pretty.json', help='输出JSON文件')
    parser.add_argument('--section-id', default=None, help='section_id字段')
    args = parser.parse_args()

    section = args.section or args.source.split('/')[-1].replace('.md', '')

    split_and_append(args.input, args.source, section, args.output, args.section_id)


if __name__ == "__main__":
    main()
