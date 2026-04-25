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
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

from zhipuai import ZhipuAI

API_KEY = os.environ.get("ZHIPU_API_KEY", "")

# 修复 Windows 编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

MODEL = "glm-4-plus"

if not API_KEY:
    print("❌ 请设置环境变量 ZHIPU_API_KEY")
    print("   或创建 .env 文件（参考 .env.example）")
    sys.exit(1)

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def save_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def clean_content_whitespace(parsed_data):
    """清理 content 字段中多余的换行符和空格"""
    for segment in parsed_data:
        if 'content' in segment and segment['content']:
            # 将换行符和连续空白替换为单个空格
            content = re.sub(r'\s+', ' ', segment['content'])
            segment['content'] = content.strip()
    return parsed_data

def segment_knowledge_points(markdown_content: str) -> str:
    """调用大模型将教材内容切分为知识点段落，返回 JSON 字符串"""

    system_prompt = """你是专业教材结构化解析助手。
任务：将一段 Markdown 格式的教材内容，按**细粒度、语义独立完整**的原则切分为文本段落，并输出可直接用于数据库入库的标准 JSON 数组。

严格遵循数据库表 content_segments 结构与以下规则：

字段要求：
1. textbook_id：固定为 1
2. chapter_id：使用**字符串格式**的章节编号，不从文本标题强行转数字
3. knowledge_node_id：固定为 null
4. segment_type：只能从以下枚举中选择一个 - definition（定义） - theorem（定理） - proof（证明） - example（例题） - note（说明/正文/注释/推导）
5. title：本段小标题或核心名称，无则为空字符串 ""
6. content：必须完整保留原文，不修改、不总结、不缩写，可以去除明确的换行符, - Markdown 中的图片、公式**直接保留在所属段落内**，保留原样，不拆分 - 识别到「图1.1.6」「图2-3」等图表编号时，将其与紧邻图片**绑定在同一段** - 公式不再单独分段，直接并入其所属语义块中
7. alias_names：别名，无则为空字符串 ""
8. tags：1~5个核心关键词，逗号分隔

切分规则：
1. 粒度偏细，一段一个知识点，保证语义独立完整
2. 图片、公式保留在所属段落内，不单独拆分
3. 不破坏原文结构，不新增内容
4. 段落之间边界清晰，不重叠、不遗漏

输出要求：只返回标准 JSON 数组，无多余文字、无解释、无注释、无 Markdown 包裹。"""

    user_prompt = f"""请将以下 Markdown 教材内容按规则切分：

{markdown_content}"""

    client = ZhipuAI(api_key=API_KEY)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        max_tokens=12000,  # 增加输出限制
        timeout=120,  # 添加超时
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
    print("=" * 60)
    print("知识点切分：细粒度语义分段 → JSON 数组")
    print("=" * 60)

    input_path = "二、函数的概念.md"
    output_path = "segments_output.json"

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
        result_json = segment_knowledge_points(content)
        
        elapsed = time.time() - start_time
        print(f"\n⏱️  处理耗时: {elapsed:.1f} 秒")

        # 验证是否为合法 JSON
        parsed = json.loads(result_json)
        
        # 清理 content 中的换行符
        parsed = clean_content_whitespace(parsed)
        
        print(f"\n✅ 切分成功，共生成 {len(parsed)} 个知识点段落")

        # 统计各类型数量
        type_count = {}
        for seg in parsed:
            seg_type = seg.get('segment_type', 'unknown')
            type_count[seg_type] = type_count.get(seg_type, 0) + 1
        
        if type_count:
            print("\n📊 段落类型统计:")
            for seg_type, count in type_count.items():
                print(f"  {seg_type}: {count}")

        # 打印前两个示例
        print("\n📋 示例（前2条）：")
        for i, seg in enumerate(parsed[:2]):
            print(f"\n--- 段落 {i+1} ---")
            print(f"  chapter_id: {seg.get('chapter_id')}")
            print(f"  segment_type: {seg.get('segment_type')}")
            print(f"  title: {seg.get('title')}")
            content_preview = seg.get('content', '')[:100]
            print(f"  content_preview: {content_preview}...")
            print(f"  tags: {seg.get('tags')}")

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