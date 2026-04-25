#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
让模型自主学习目录结构规律，并按规范格式输出
只给输出框架示例，不强求字段值
"""

import sys
import io
import json
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

def learn_and_extract(full_content: str) -> str:
    """让模型学习规律并按规范格式输出"""
    
    prompt = f"""请分析下面的书籍目录，完成两个任务。

【任务1】总结结构规律
观察这个目录，它使用了什么样的编号体系和层级结构？请总结出：
- 共有几个层级
- 每个层级的编号格式是什么
- 每个层级的名称是什么（根据目录实际叫法，可能是：章、节、讲、单元、模块、部分等）
- 是否有特殊条目（如实验、习题、本章资源等），它们属于哪一层级，允许每个层级有多个可匹配的编号格式

【任务2】按以下格式输出JSON

输出格式参考（字段名固定，但内容根据实际目录填写）：
{{
  "structure_summary": {{
    "层级数量": 数字,
    "层级定义": [
      {{"level": 1, "编号格式": "实际格式", "层级名称": "实际名称"}},
      {{"level": 2, "编号格式": "实际格式", "层级名称": "实际名称"}}，
      {{"level": 2, "编号格式": "实际格式", "层级名称": "实际名称"}}，  # 如果有多个同级编号格式（特殊条目也可以），允许多条
      {{"level": 3, "编号格式": "实际格式", "层级名称": "实际名称"}}，
    ]
  }},
  "chapters": [
    {{
      "level": 1,
      "编号": "原文编号",
      "标题": "标题文字",
      "父级编号": null 或 "父级的原文编号"
    }}
  ]
}}

注意：
- “层级名称”不要照抄示例，要根据目录实际叫法填写
- 如果目录只有2级，就只写2级；如果有4级，就写4级
- “编号格式”写实际的模式，可直接用正则表达式描述，但要清晰易懂
- “父级编号”如果没有就写 null，有就写原文编号

目录内容：
{full_content}
"""

    client = ZhipuAI(api_key=API_KEY)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "你是目录结构分析专家。先观察实际目录，再按格式输出。字段内容由目录决定，不照搬示例。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=8192,
    )
    
    result = response.choices[0].message.content
    
    # 清洗 JSON
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
    print("目录解析：自主学习 + 规范输出")
    print("=" * 60)
    
    content = read_file("目录.md")
    print(f"\n📖 文件大小: {len(content)} 字符")
    
    print("\n🤖 模型学习中...")
    
    try:
        result = learn_and_extract(content)
        
        print("\n📋 输出结果：")
        print("-" * 40)
        
        try:
            parsed = json.loads(result)
            # 打印结构总结
            summary = parsed.get("structure_summary", {})
            print("【结构总结】")
            print(f"  层级数量: {summary.get('层级数量')}")
            print(f"  层级定义: {json.dumps(summary.get('层级定义', []), ensure_ascii=False)}")
            print(f"  父子关系依据: {summary.get('父子关系依据')}")
            print(f"  特殊条目说明: {summary.get('特殊条目说明')}")
            print(f"\n  共提取 {len(parsed.get('chapters', []))} 个条目")
        except:
            print(result[:1000])
        
        print("-" * 40)
        
        save_file("chapter_structure.json", result)
        print("\n✓ 完整结果已保存到 chapter_structure.json")
        
    except Exception as e:
        print(f"\n✗ 出错: {e}")

if __name__ == "__main__":
    main()