#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
概念标注脚本
- 输入：一个 Markdown 文件
- 处理：用 AC 自动机匹配所有已对齐别名，找出文本中出现的概念关联词
- 输出：处理后的 Markdown 文件（文末附注释表，列出匹配详情）

使用方式：
  python annotate_md.py 二、函数的概念.md
  python annotate_md.py 二、函数的概念.md --output 输出.md
  python annotate_md.py 二、函数的概念.md --inline   # 直接在文中用 [[概念名]] 替换
"""

import sys
import io
import re
import sqlite3
import argparse
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

DB_PATH = "concept_base.db"

# 只使用已确认对齐的别名（未对齐/待审核不参与标注）
VALID_STATUSES = {'auto_mapped', 'llm_confirmed'}


# ──────────────────────────────────────────────
# AC 自动机
# ──────────────────────────────────────────────

class AhoCorasick:
    def __init__(self):
        self.goto = [{}]    # 转移表
        self.fail = [0]     # 失败指针
        self.output = [[]]  # 终态输出

    def add_pattern(self, pattern, value):
        cur = 0
        for ch in pattern:
            if ch not in self.goto[cur]:
                self.goto[cur][ch] = len(self.goto)
                self.goto.append({})
                self.fail.append(0)
                self.output.append([])
            cur = self.goto[cur][ch]
        self.output[cur].append(value)

    def build(self):
        from collections import deque
        q = deque()
        for ch, s in self.goto[0].items():
            self.fail[s] = 0
            q.append(s)
        while q:
            cur = q.popleft()
            for ch, nxt in self.goto[cur].items():
                q.append(nxt)
                f = self.fail[cur]
                while f and ch not in self.goto[f]:
                    f = self.fail[f]
                self.fail[nxt] = self.goto[f].get(ch, 0) if f or ch in self.goto[0] else 0
                if self.fail[nxt] == nxt:
                    self.fail[nxt] = 0
                self.output[nxt] = self.output[nxt] + self.output[self.fail[nxt]]

    def search(self, text):
        """返回所有匹配：(start, end, alias, concept_id, concept_name, alias_type, status, confidence) 列表"""
        cur = 0
        results = []
        for i, ch in enumerate(text):
            while cur and ch not in self.goto[cur]:
                cur = self.fail[cur]
            cur = self.goto[cur].get(ch, 0)
            for alias, concept_id, concept_name, alias_type, status, confidence in self.output[cur]:
                start = i - len(alias) + 1
                results.append((start, i + 1, alias, concept_id, concept_name, alias_type, status, confidence))
        return results


# ──────────────────────────────────────────────
# 数据库加载
# ──────────────────────────────────────────────

def load_alias_db(db_path):
    """从数据库加载所有已对齐的别名（含概念名本身）"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 加载别名表（含概念名）
    cursor.execute("""
        SELECT a.alias, a.concept_id, c.name, a.alias_type, a.status, a.confidence
        FROM aliases a
        LEFT JOIN concepts c ON a.concept_id = c.concept_id
        WHERE a.status IN ({})
    """.format(','.join('?' * len(VALID_STATUSES))), list(VALID_STATUSES))

    aliases = cursor.fetchall()
    conn.close()
    print(f"📚 加载 {len(aliases)} 个已对齐别名/实体/概念")
    return aliases


# ──────────────────────────────────────────────
# Markdown 解析 - 识别需要跳过的区域
# ──────────────────────────────────────────────

def find_skip_ranges(text):
    """
    找出不需要匹配的区域：
    - 代码块 ```...```
    - 行内代码 `...`
    - 块级公式 $$...$$
    - 行内公式 $...$
    - 图片 ![](...)
    - 链接 [...](...) 中的 URL 部分
    - HTML 标签
    """
    skip = []

    # 代码块
    for m in re.finditer(r'```[\s\S]*?```', text):
        skip.append((m.start(), m.end()))

    # 块级公式
    for m in re.finditer(r'\$\$[\s\S]*?\$\$', text):
        skip.append((m.start(), m.end()))

    # 行内代码
    for m in re.finditer(r'`[^`]+`', text):
        skip.append((m.start(), m.end()))

    # 行内公式（不在已跳过区域内）
    for m in re.finditer(r'\$[^$\n]+?\$', text):
        skip.append((m.start(), m.end()))

    # 图片
    for m in re.finditer(r'!\[.*?\]\(.*?\)', text):
        skip.append((m.start(), m.end()))

    # Markdown 标题（保留标题文字，但去掉 # 符号影响）
    # 实际上标题文字应该匹配，所以不跳过

    skip.sort()
    return skip


def in_skip(pos, skip_ranges):
    for s, e in skip_ranges:
        if s <= pos < e:
            return True
        if s > pos:
            break
    return False


def filter_matches_by_skip(matches, skip_ranges):
    """过滤掉落在跳过区域内的匹配"""
    result = []
    for m in matches:
        start, end = m[0], m[1]
        if not any(s <= start < e or s < end <= e for s, e in skip_ranges):
            result.append(m)
    return result


# ──────────────────────────────────────────────
# 最长匹配优先 + 去重
# ──────────────────────────────────────────────

def resolve_overlaps(matches):
    """最长匹配优先，去掉重叠的短匹配"""
    # 按长度降序、起始位置升序
    sorted_m = sorted(matches, key=lambda m: (-(m[1] - m[0]), m[0]))
    used = []
    result = []
    for m in sorted_m:
        start, end = m[0], m[1]
        if not any(s < end and start < e for s, e in used):
            result.append(m)
            used.append((start, end))
    # 恢复按位置排序
    result.sort(key=lambda m: m[0])
    return result


# ──────────────────────────────────────────────
# 生成输出 Markdown
# ──────────────────────────────────────────────

def annotate_text_inline(text, matches):
    """将文中匹配词替换为 [[概念名|原词]]"""
    result = list(text)
    offset = 0
    for start, end, alias, concept_id, concept_name, alias_type, status, confidence in matches:
        replacement = f"[[{concept_name}|{alias}]]" if alias != concept_name else f"[[{concept_name}]]"
        s = start + offset
        e = end + offset
        result[s:e] = list(replacement)
        offset += len(replacement) - (end - start)
    return ''.join(result)


def build_annotation_table(all_matches):
    """生成文末注释表"""
    lines = []
    lines.append("\n\n---\n")
    lines.append("## 📌 概念对齐注释\n")
    lines.append("> 本节由程序自动生成，列出文中已与概念库对齐的关键词。\n\n")
    lines.append("| 出现词 | 对齐概念 | 概念ID | 类型 | 置信度 |\n")
    lines.append("|--------|---------|--------|------|--------|\n")

    seen = set()
    for start, end, alias, concept_id, concept_name, alias_type, status, confidence in all_matches:
        key = (alias, concept_id)
        if key in seen:
            continue
        seen.add(key)

        type_label = {
            'concept': '概念本身',
            'alias':   '别名',
            'entity':  '实体词',
        }.get(alias_type, alias_type)

        conf_str = f"{confidence:.3f}" if confidence else "-"
        lines.append(f"| `{alias}` | **{concept_name}** | {concept_id} | {type_label} | {conf_str} |\n")

    return ''.join(lines)


def process_markdown(md_text, ac, inline=False):
    """
    处理 Markdown 全文：
    - inline=False：保持原文不变，文末追加注释表
    - inline=True：文中词替换为 [[概念名|词]]，文末追加注释表
    """
    skip_ranges = find_skip_ranges(md_text)

    raw_matches = ac.search(md_text)
    filtered = filter_matches_by_skip(raw_matches, skip_ranges)
    resolved = resolve_overlaps(filtered)

    print(f"🔍 共找到 {len(resolved)} 个概念关联词（去重后）")

    if not resolved:
        return md_text + "\n\n---\n\n> ℹ️ 未找到与概念库对齐的关键词。\n"

    if inline:
        body = annotate_text_inline(md_text, resolved)
    else:
        body = md_text

    table = build_annotation_table(resolved)
    return body + table


# ──────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Markdown 概念标注')
    parser.add_argument('input', help='输入 Markdown 文件路径')
    parser.add_argument('--output', help='输出文件路径（默认在原文件名后加 _annotated）')
    parser.add_argument('--inline', action='store_true', help='在文中直接替换为 [[概念名|词]]（默认只在文末列表）')
    parser.add_argument('--db', default=DB_PATH, help=f'数据库路径（默认 {DB_PATH}）')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        exit(1)
    if not Path(args.db).exists():
        print(f"❌ 数据库不存在: {args.db}")
        print("   请先运行 build_concept_db.py 和 align_aliases.py")
        exit(1)

    output_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + '_annotated.md')

    print("=" * 60)
    print(f"概念标注: {input_path.name}")
    print("=" * 60)

    # 1. 加载数据库
    aliases = load_alias_db(args.db)

    # 2. 构建 AC 自动机
    print("⚙️  构建 AC 自动机...")
    ac = AhoCorasick()
    for alias, concept_id, concept_name, alias_type, status, confidence in aliases:
        if alias and concept_id and concept_name:
            ac.add_pattern(alias, (alias, concept_id, concept_name, alias_type, status, confidence))
    ac.build()

    # 3. 读取 Markdown
    md_text = input_path.read_text(encoding='utf-8')
    print(f"📖 文件大小: {len(md_text)} 字符")

    # 4. 处理
    result = process_markdown(md_text, ac, inline=args.inline)

    # 5. 输出
    output_path.write_text(result, encoding='utf-8')
    print(f"\n✅ 已输出: {output_path}")
    if args.inline:
        print("   模式：文中内联替换 [[概念名|词]] + 文末注释表")
    else:
        print("   模式：原文不变 + 文末注释表")


if __name__ == "__main__":
    main()
