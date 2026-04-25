#!/usr/bin/env python3
"""
标题标准化脚本 - 基于 structure_summary 动态规则
"""

import re
import json
import os
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ==================== 配置区（改这里） ====================
INPUT_PATH = "高等数学（上）.md"
OUTPUT_PATH = "全文_标准化.md"
RULES_JSON = "chapter_structure.json"
# ==================== 配置区结束 ====================


def load_and_build_rules(json_path):
    """从 JSON 加载 structure_summary，构建规则"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rules = []
    for defn in data.get('structure_summary', {}).get('层级定义', []):
        level = defn.get('level', 1)
        fmt = defn.get('编号格式', '')
        if fmt:
            rules.append((level, re.compile('^' + fmt)))
    return rules


def process_title_line(line, rules):
    """处理标题行，返回标准化后的行"""
    stripped = line.strip()
    leading = re.match(r'^#+', stripped)
    content = re.sub(r'^#+\s*', '', stripped)
    content = re.sub(r'^\*+\s*', '', content)
    content = re.sub(r'\s*\*+$', '', content)

    for level, pattern in rules:
        if pattern.match(content):
            if leading:
                print(f"  [标准化] {leading.group(0)} -> {'#' * level}: {content}")
            return f"{'#' * level} {content}"

    if leading:
        print(f"  [去格式] {stripped} -> {content}")
    return content


def process_markdown(content, rules):
    """处理 Markdown 内容"""
    lines = content.split('\n')
    result = []

    for line in lines:
        stripped = re.sub(r'^\s*', '', line)

        if re.match(r'^#+', stripped):
            new_line = process_title_line(stripped, rules)
            result.append(new_line)
        else:
            result.append(line)

    return '\n'.join(result)


def main():
    print(f"\n{'='*50}")
    print(f"标题标准化")
    print(f"  输入: {INPUT_PATH}")
    print(f"  输出: {OUTPUT_PATH}")
    print(f"  规则: {RULES_JSON}")
    print(f"{'='*50}")

    if not os.path.exists(RULES_JSON):
        print(f"❌ JSON 文件不存在: {RULES_JSON}")
        return

    rules = load_and_build_rules(RULES_JSON)
    print(f"加载 {len(rules)} 条规则")

    if not os.path.exists(INPUT_PATH):
        print(f"❌ 输入文件不存在: {INPUT_PATH}")
        return

    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    normalized = process_markdown(content, rules)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(normalized)

    print(f"✅ 完成: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
