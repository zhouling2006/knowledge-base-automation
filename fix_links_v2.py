#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_links_v2.py - 双链引用修复工具（三级索引：小节 -> 节 -> 章）

针对 processed_output_t 下的层级目录结构：
  章/   （如 第一章/）
    节/   （如 1-1/）
      小节/  （如 一_集合和映射/，含 _*_memory.json + .md 文件）

修复逻辑：
  - 索引来源：小节 _*_memory.json -> 节级 _section_memory.json -> 章级 _chapter_memory.json
  - 匹配策略（按优先级）：
      1. 精确匹配（link_text == stem）-> 跳过
      2. 去标点后精确匹配（唯一候选 -> 自动选）
      3. 公共子串匹配（最长公共连续子串 >= 短者 50%）-> 收集候选
      4. 以上全部未命中 -> 当前层级全量文档列表交给 LLM
  - 三层递进：先在小节找 -> 没找到扩大到节 -> 还没找到扩大到章（不做跨章）
  - 所有不确定的统一交给 LLM 判断，允许返回"确实没有匹配"
  - 无论如何无法匹配 -> 记录到 fix_links_v2_unresolved.log

用法：
  python fix_links_v2.py --build-index           # 生成/更新各层级聚合 memory.json
  python fix_links_v2.py                          # 修复 processed_output_t，写入 processed_output_t_v2
  python fix_links_v2.py --dry-run                # 只报告，不写文件
  python fix_links_v2.py --no-llm                 # 禁用 LLM 兜底
  python fix_links_v2.py --in-place               # 直接覆盖原文件（慎用）
  python fix_links_v2.py --input-dir <dir>        # 指定输入目录
  python fix_links_v2.py --output-dir <dir>       # 指定输出目录
"""

import sys
import io
import os
import re
import json
import time
import argparse
from pathlib import Path
from typing import Optional
from collections import defaultdict

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# =============================================================================
# 工具函数
# =============================================================================

PUNCT = '：:，,、；;【】[]（）()《》\u201c\u201d\u2018\u2019「」『』〈〉〖〗·•…⋯—–-‐$（）——\\\\/+^={}'


def remove_punctuation(s: str) -> str:
    """去除常见标点与空白，保留中英文、数字"""
    result = s
    for p in PUNCT:
        result = result.replace(p, '')
    result = re.sub(r'\s+', '', result)
    return result


# =============================================================================
# 层级索引
# =============================================================================

class HierarchyIndex:
    """
    三级索引：小节 > 节 > 章。
    每条 entry: stem -> {filename, title, summary, path, source}
    source = "subsection" | "section" | "chapter"
    """

    def __init__(self, subsection_dir: Path, section_dir: Path, chapter_dir: Path):
        self.subsection_dir = subsection_dir
        self.section_dir = section_dir
        self.chapter_dir = chapter_dir

        self.entries: dict[str, dict] = {}
        self.no_punct: dict[str, set] = {}

        self.subsection_stems: set[str] = set()
        self.section_stems: set[str] = set()
        self.chapter_stems: set[str] = set()

        self.subsection_name: str = subsection_dir.name
        self.section_name: str = section_dir.name
        self.chapter_name: str = chapter_dir.name

        self._load()

    def _load_memory_json(self, mem_file: Path) -> list[dict]:
        try:
            data = json.loads(mem_file.read_text(encoding='utf-8'))
            result = []
            for item in data:
                fname = item.get('filename', '')
                stem = Path(fname).stem
                result.append({
                    'stem': stem,
                    'title': item.get('title', stem),
                    'summary': item.get('summary', ''),
                    'subsection': item.get('subsection', ''),
                    'section': item.get('section', ''),
                })
            return result
        except Exception as e:
            print(f"  warning: read {mem_file.name} failed: {e}")
            return []

    def _add_entries(self, items: list[dict], source: str):
        stems_set = {
            'subsection': self.subsection_stems,
            'section': self.section_stems,
            'chapter': self.chapter_stems,
        }[source]

        for item in items:
            stem = item['stem']
            if stem in self.entries:
                continue
            self.entries[stem] = {
                'filename': f"{stem}.md",
                'title': item['title'],
                'summary': item.get('summary', ''),
                'source': source,
                'subsection': item.get('subsection', ''),
                'section': item.get('section', ''),
            }
            stems_set.add(stem)

    def _load(self):
        # 第一层：小节
        mem_info: dict[str, dict] = {}
        for mem_file in self.subsection_dir.glob("*_memory.json"):
            if mem_file.name in ("_section_memory.json", "_chapter_memory.json"):
                continue
            for item in self._load_memory_json(mem_file):
                mem_info[item['stem']] = {
                    'title': item['title'],
                    'summary': item.get('summary', ''),
                }

        for md in self.subsection_dir.glob("*.md"):
            if md.name.startswith('_') or md.name.startswith('.'):
                continue
            stem = md.stem
            info = mem_info.get(stem, {})
            self.entries[stem] = {
                'filename': md.name,
                'title': info.get('title', stem),
                'summary': info.get('summary', ''),
                'source': 'subsection',
                'path': str(md),
                'subsection': self.subsection_name,
                'section': self.section_name,
            }
            self.subsection_stems.add(stem)

        # 第二层：节
        section_mem = self.section_dir / "_section_memory.json"
        if section_mem.exists():
            items = self._load_memory_json(section_mem)
            self._add_entries(items, 'section')

        # 第三层：章
        chapter_mem = self.chapter_dir / "_chapter_memory.json"
        if chapter_mem.exists():
            items = self._load_memory_json(chapter_mem)
            self._add_entries(items, 'chapter')

        # 去标点索引
        for stem in self.entries:
            np = remove_punctuation(stem)
            if np not in self.no_punct:
                self.no_punct[np] = set()
            self.no_punct[np].add(stem)

        # 层级包含关系
        self.section_stems |= self.subsection_stems
        self.chapter_stems |= self.section_stems

    def __len__(self):
        return len(self.entries)

    def stems(self) -> list[str]:
        return list(self.entries.keys())

    def source_label(self, entry: dict) -> str:
        source = entry.get('source', '')
        if source == 'subsection':
            return f"{entry.get('section', '')} > {entry.get('subsection', '')}"
        elif source == 'section':
            ss = entry.get('subsection', '')
            if ss:
                return f"{entry.get('section', '')} > {ss}"
            return f"{entry.get('section', '')}"
        elif source == 'chapter':
            sec = entry.get('section', '')
            ss = entry.get('subsection', '')
            if ss:
                return f"{self.chapter_name} > {sec} > {ss}"
            if sec:
                return f"{self.chapter_name} > {sec}"
            return f"{self.chapter_name}"
        return source


# =============================================================================
# 匹配引擎
# =============================================================================

TOP_N = 5


def _longest_common_substring(s1: str, s2: str) -> int:
    m, n = len(s1), len(s2)
    if m == 0 or n == 0:
        return 0
    prev = [0] * (n + 1)
    best = 0
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                curr[j] = prev[j - 1] + 1
                if curr[j] > best:
                    best = curr[j]
        prev = curr
    return best


def _collect_candidates(np_link: str, idx: HierarchyIndex) -> list[tuple[str, float, str]]:
    link_len = len(np_link)
    if link_len == 0:
        return []

    candidates: list[tuple[str, float, str]] = []

    for np_name, stems in idx.no_punct.items():
        if np_name == np_link:
            continue
        stem_len = len(np_name)

        if np_link in np_name:
            score = link_len / stem_len if stem_len > 0 else 1.0
            for s in stems:
                candidates.append((s, score, "contains"))
            continue
        if np_name in np_link:
            score = stem_len / link_len if link_len > 0 else 1.0
            for s in stems:
                candidates.append((s, score, "contains"))
            continue

        lcs = _longest_common_substring(np_link, np_name)
        threshold = min(link_len, stem_len) * 0.5
        if lcs >= threshold and lcs >= 2:
            ml = max(link_len, stem_len)
            score = lcs / ml
            for s in stems:
                candidates.append((s, score, f"lcs{lcs}"))

    best: dict[str, tuple[float, str]] = {}
    for stem, score, reason in candidates:
        if stem not in best or score > best[stem][0]:
            best[stem] = (score, reason)

    result = [(stem, score, reason) for stem, (score, reason) in best.items()]
    result.sort(key=lambda x: x[1], reverse=True)
    return result


def _find_in_scope(
    link_text: str, np_link: str, idx: HierarchyIndex, scope: set[str],
) -> tuple[Optional[str], str, list[str]]:
    if link_text in scope:
        return link_text, "exact", []

    if np_link in idx.no_punct:
        hits = idx.no_punct[np_link] & scope
        if len(hits) == 1:
            return next(iter(hits)), "depunct", []
        if len(hits) > 1:
            return None, "depunct_multi", list(hits)

    all_cands = _collect_candidates(np_link, idx)
    scoped_cands = [(s, sc, r) for s, sc, r in all_cands if s in scope]
    if scoped_cands:
        cand_names = [name for name, _, _ in scoped_cands[:TOP_N]]
        return None, f"candidates({len(scoped_cands)})", cand_names

    return None, "no_match", []


def find_match(
    link_text: str, idx: HierarchyIndex,
) -> tuple[Optional[str], str, list[str]]:
    """三层递进匹配：小节 -> 节 -> 章"""
    if link_text.endswith('.md'):
        link_text = link_text[:-3]
    link_text = link_text.strip()
    np_link = remove_punctuation(link_text)

    # 第一层：小节
    matched, method, candidates = _find_in_scope(link_text, np_link, idx, idx.subsection_stems)
    if matched is not None:
        return matched, f"[subsec]{method}", []
    if candidates:
        return None, f"[subsec]{method}", candidates

    # 第二层：节（排除小节已有的）
    section_only = idx.section_stems - idx.subsection_stems
    matched, method, candidates = _find_in_scope(link_text, np_link, idx, section_only)
    if matched is not None:
        return matched, f"[sec]{method}", []
    if candidates:
        return None, f"[sec]{method}", candidates

    # 第三层：章（排除节已有的）
    chapter_only = idx.chapter_stems - idx.section_stems
    matched, method, candidates = _find_in_scope(link_text, np_link, idx, chapter_only)
    if matched is not None:
        return matched, f"[chap]{method}", []
    if candidates:
        return None, f"[chap]{method}", candidates

    return None, "[chap]no_match", []


# =============================================================================
# LLM
# =============================================================================

_LLM_SYSTEM = "你是数学知识点双链修复助手。给定一段双链引用文本和文档列表，\n判断该引用最应该指向哪个文档（基于语义相近程度）。\n\n核心规则：\n1. 引用文本可能只是文档名的一部分（如\"例1.1.13\"对应\"例1.1.13-直角坐标方程化为极坐标方程\"）\n2. 引用文本可能是概念的不同表述（如\"夹逼准则\"对应\"例1.6.8续-由夹逼准则得右极限\"）\n3. 不要选语义范围更宽泛的候选：若引用文本是\"导数的几何意义\"，不应选\"导数的几何意义与物理意义\"\n4. 优先选范围完全一致或更具体的候选\n5. 优先选来源层级更近的候选（同小节 > 同节 > 同章）\n6. 如没有任何合适的文档，返回 0\n\n输出格式：只输出一个整数，代表选择的候选序号（从 1 开始），或 0 代表无合适候选。\n不要输出任何其他内容。"


def call_llm(user_prompt: str, max_retries: int = 2) -> Optional[str]:
    try:
        from openai import OpenAI
    except ImportError:
        print("    warning: openai not installed, skip LLM")
        return None

    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        print("    warning: DASHSCOPE_API_KEY not set, skip LLM")
        return None

    model = os.environ.get("LLM_MODEL", "qwen-plus")
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _LLM_SYSTEM},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=16,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"    warning: LLM failed({attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(2)
    return None


def _format_candidates(link_text: str, candidates: list[str], idx: HierarchyIndex,
                       context: str = "") -> str:
    lines = [f"引用文本: 【{link_text}】"]
    if context:
        lines.append(f"上下文: ...{context}...")
    lines.append("候选文档列表：")
    for i, stem in enumerate(candidates, 1):
        entry = idx.entries.get(stem, {})
        title = entry.get('title', stem)
        summary = entry.get('summary', '')
        source_label = idx.source_label(entry)
        lines.append(f"  {i}. {stem}")
        if title != stem:
            lines.append(f"     标题: {title}")
        if source_label:
            lines.append(f"     来源: {source_label}")
        if summary:
            lines.append(f"     摘要: {summary[:120]}")
    return '\n'.join(lines)


def llm_pick(link_text: str, candidates: list[str], idx: HierarchyIndex,
             context: str = "", full_list: bool = False) -> Optional[str]:
    if full_list:
        source_order = {'subsection': 0, 'section': 1, 'chapter': 2}
        all_stems = sorted(
            idx.stems(),
            key=lambda s: source_order.get(idx.entries.get(s, {}).get('source', 'chapter'), 9),
        )
        prompt = _format_candidates(link_text, all_stems, idx, context)
    else:
        prompt = _format_candidates(link_text, candidates, idx, context)

    result = call_llm(prompt)
    if not result:
        return None

    m = re.search(r'\d+', result)
    if m:
        n = int(m.group())
        if n == 0:
            return None
        target_list = sorted(idx.stems()) if full_list else candidates
        if 1 <= n <= len(target_list):
            return target_list[n - 1]
    return None


# =============================================================================
# 双链正则与上下文提取
# =============================================================================

WIKILINK_RE = re.compile(r'\[\[([^\]|]+)\]\](\{[^}]*\})?')


def extract_context(content: str, link_text: str, window: int = 80) -> str:
    pattern = re.compile(re.escape(f'[[{link_text}]]'))
    m = pattern.search(content)
    if not m:
        return ""
    start = max(0, m.start() - window)
    end = min(len(content), m.end() + window)
    return content[start:end].replace('\n', ' ').strip()


# =============================================================================
# 处理单个文件
# =============================================================================

def process_file(
    md_path: Path, idx: HierarchyIndex, use_llm: bool, report: list[dict],
) -> str:
    content = md_path.read_text(encoding='utf-8')
    llm_pending: list[dict] = []

    def first_pass(m: re.Match) -> str:
        link_text = m.group(1).strip()
        attrs = m.group(2) or ""

        matched, method, candidates = find_match(link_text, idx)

        if matched == link_text:
            report.append({'file': md_path.name, 'link': link_text, 'result': 'ok_exact', 'method': method, 'new': None})
            return m.group(0)

        if matched is not None and matched != link_text:
            entry = idx.entries.get(matched, {})
            report.append({'file': md_path.name, 'link': link_text, 'result': 'fixed', 'method': method, 'new': matched, 'source': entry.get('source', '')})
            return f"[[{matched}]]{attrs}"

        if use_llm:
            ctx = extract_context(content, link_text)
            full_list = len(candidates) == 0
            llm_pending.append({'link_text': link_text, 'attrs': attrs, 'candidates': candidates, 'context': ctx, 'full_list': full_list})

        report.append({'file': md_path.name, 'link': link_text, 'result': 'pending_llm' if use_llm else 'unresolved', 'method': method, 'new': None, 'candidates': candidates[:5]})
        return m.group(0)

    new_content = WIKILINK_RE.sub(first_pass, content)

    if llm_pending:
        print(f"    LLM: {len(llm_pending)} links in [{md_path.name}]")
        for item in llm_pending:
            picked = llm_pick(item['link_text'], item['candidates'], idx, item['context'], full_list=item['full_list'])
            if picked:
                mode = "full" if item['full_list'] else "candidates"
                entry = idx.entries.get(picked, {})
                source = entry.get('source', '?')
                print(f"      + [{item['link_text']}] -> [{picked}] ({mode}, src:{source})")
                for r in report:
                    if r['file'] == md_path.name and r['link'] == item['link_text'] and r['result'] == 'pending_llm':
                        r['result'] = 'fixed_llm'
                        r['new'] = picked
                        r['source'] = source
                        break
                pattern = re.compile(r'\[\[' + re.escape(item['link_text']) + r'\]\]' + r'(\{[^}]*\})?')
                attrs = item['attrs']
                def make_rep(stem=picked, a=attrs):
                    def rep(mm):
                        return f"[[{stem}]]{mm.group(1) or a}"
                    return rep
                new_content = pattern.sub(make_rep(), new_content)
            else:
                verdict = "LLM: no match" if item['full_list'] else "LLM: no result"
                print(f"      - [{item['link_text']}] {verdict}")
                for r in report:
                    if r['file'] == md_path.name and r['link'] == item['link_text'] and r['result'] == 'pending_llm':
                        r['result'] = 'unresolved'
                        break

    return new_content


# =============================================================================
# 索引构建
# =============================================================================

def build_indexes(input_dir: Path):
    subsection_dirs: list[Path] = []
    for mem in sorted(input_dir.rglob("*_memory.json")):
        if mem.name in ("_section_memory.json", "_chapter_memory.json"):
            continue
        subsection_dirs.append(mem.parent)

    if not subsection_dirs:
        print("error: no _*_memory.json found")
        return

    sections: dict[Path, list[Path]] = defaultdict(list)
    chapters: dict[Path, list[Path]] = defaultdict(list)

    for ss_dir in subsection_dirs:
        try:
            rel = ss_dir.relative_to(input_dir)
            parts = rel.parts
            if len(parts) >= 3:
                chapter_dir = input_dir / parts[0]
                section_dir = input_dir / parts[0] / parts[1]
                sections[section_dir].append(ss_dir)
                chapters[chapter_dir].append(section_dir)
            elif len(parts) == 2:
                section_dir = input_dir / parts[0]
                sections[section_dir].append(ss_dir)
        except ValueError:
            print(f"  warning: cannot parse path: {ss_dir}")

    print(f"found {len(subsection_dirs)} subsections, {len(sections)} sections, {len(chapters)} chapters\n")

    # section indexes
    print("=== generating section indexes ===")
    for sec_dir in sorted(sections.keys()):
        all_items = []
        for ss_dir in sections[sec_dir]:
            for mem_file in ss_dir.glob("*_memory.json"):
                if mem_file.name in ("_section_memory.json", "_chapter_memory.json"):
                    continue
                try:
                    data = json.loads(mem_file.read_text(encoding='utf-8'))
                    for item in data:
                        item['subsection'] = ss_dir.name
                        all_items.append(item)
                except Exception:
                    pass
        out = sec_dir / "_section_memory.json"
        out.write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding='utf-8')
        rel = sec_dir.relative_to(input_dir)
        print(f"  + {rel}/_section_memory.json  ({len(all_items)} entries)")

    # chapter indexes
    print("\n=== generating chapter indexes ===")
    for chap_dir in sorted(chapters.keys()):
        all_items = []
        for s_dir in chapters[chap_dir]:
            sec_mem = s_dir / "_section_memory.json"
            if sec_mem.exists():
                try:
                    data = json.loads(sec_mem.read_text(encoding='utf-8'))
                    for item in data:
                        item['section'] = s_dir.name
                        all_items.append(item)
                except Exception:
                    pass
        out = chap_dir / "_chapter_memory.json"
        out.write_text(json.dumps(all_items, ensure_ascii=False, indent=2), encoding='utf-8')
        rel = chap_dir.relative_to(input_dir)
        print(f"  + {rel}/_chapter_memory.json  ({len(all_items)} entries)")

    print(f"\ndone: indexes built")


# =============================================================================
# 目录结构发现
# =============================================================================

def discover_hierarchy(input_dir: Path) -> list[dict]:
    result = []
    for mem in sorted(input_dir.rglob("*_memory.json")):
        if mem.name in ("_section_memory.json", "_chapter_memory.json"):
            continue
        ss_dir = mem.parent
        try:
            rel = ss_dir.relative_to(input_dir)
            parts = rel.parts
            if len(parts) >= 3:
                chapter_dir = input_dir / parts[0]
                section_dir = input_dir / parts[0] / parts[1]
                result.append({'subsection_dir': ss_dir, 'section_dir': section_dir, 'chapter_dir': chapter_dir})
            elif len(parts) == 2:
                section_dir = input_dir / parts[0]
                result.append({'subsection_dir': ss_dir, 'section_dir': section_dir, 'chapter_dir': input_dir})
        except ValueError:
            pass
    return result


# =============================================================================
# 主流程
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="双链引用修复工具 v2（三级索引：小节 -> 节 -> 章）",
        epilog="""
示例：
  python fix_links_v2.py --build-index
  python fix_links_v2.py
  python fix_links_v2.py --dry-run
  python fix_links_v2.py --no-llm
  python fix_links_v2.py --in-place
  python fix_links_v2.py --input-dir ./processed_output_t --output-dir ./processed_output_t_v2
""",
    )
    parser.add_argument("--input-dir", "-i", default=None, help="输入目录（默认：processed_output_t）")
    parser.add_argument("--output-dir", "-o", default=None, help="输出目录（默认：processed_output_t_v2）")
    parser.add_argument("--build-index", action="store_true", help="仅生成/更新各层级聚合 memory.json")
    parser.add_argument("--dry-run", action="store_true", help="只报告，不写文件")
    parser.add_argument("--no-llm", action="store_true", help="禁用 LLM 兜底")
    parser.add_argument("--in-place", action="store_true", help="直接覆盖原文件（慎用）")
    args = parser.parse_args()

    BASE = Path(__file__).parent.resolve()
    input_dir = Path(args.input_dir) if args.input_dir else BASE / "processed_output_t"
    output_dir = (
        Path(input_dir) if args.in_place
        else (Path(args.output_dir) if args.output_dir else BASE / "processed_output_t_v2")
    )
    use_llm = not args.no_llm

    print(f"\n{'=' * 60}")
    print(f"fix_links_v2 - 三级索引双链修复工具")
    print(f"{'=' * 60}")
    print(f"  input:  {input_dir}")
    print(f"  output: {'(in-place)' if args.in_place else output_dir}")
    print(f"  mode:   {'dry-run' if args.dry_run else 'write'}")
    print(f"  LLM:    {'off' if not use_llm else 'on'}")
    print(f"{'=' * 60}\n")

    if not input_dir.exists():
        print(f"error: input dir not found: {input_dir}")
        sys.exit(1)

    # --build-index 模式
    if args.build_index:
        build_indexes(input_dir)
        return

    # 发现层级结构
    hierarchy = discover_hierarchy(input_dir)

    if not hierarchy:
        print("error: no _*_memory.json found, check --input-dir")
        sys.exit(1)

    # 检查是否已生成聚合索引，没有则自动生成
    has_section_mem = any((h['section_dir'] / "_section_memory.json").exists() for h in hierarchy)
    has_chapter_mem = any((h['chapter_dir'] / "_chapter_memory.json").exists() for h in hierarchy)

    if not has_section_mem or not has_chapter_mem:
        print("  聚合索引不存在，先自动生成...\n")
        build_indexes(input_dir)
        print()

    print(f"found {len(hierarchy)} subsections\n")

    all_report: list[dict] = []
    total_files = 0
    total_fixed = 0
    total_unresolved = 0

    for h in hierarchy:
        ss_dir = h['subsection_dir']
        sec_dir = h['section_dir']
        chap_dir = h['chapter_dir']

        idx = HierarchyIndex(ss_dir, sec_dir, chap_dir)
        rel_ss = ss_dir.relative_to(input_dir)
        print(f"> [{rel_ss}]  (index: {len(idx)} files)")

        md_files = [f for f in ss_dir.glob("*.md") if not f.name.startswith('_') and not f.name.startswith('.')]

        if not md_files:
            print(f"   (no .md files, skip)\n")
            continue

        sec_report: list[dict] = []

        for md in sorted(md_files):
            new_content = process_file(md, idx, use_llm, sec_report)
            total_files += 1

            if not args.dry_run:
                if args.in_place:
                    out_path = md
                else:
                    rel = md.relative_to(input_dir)
                    out_path = output_dir / rel
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(new_content, encoding='utf-8')

        fixed = [r for r in sec_report if r['result'].startswith('fixed')]
        unresolved = [r for r in sec_report if r['result'] == 'unresolved']
        ok = [r for r in sec_report if r['result'] == 'ok_exact']

        total_fixed += len(fixed)
        total_unresolved += len(unresolved)
        all_report.extend(sec_report)

        print(f"   fixed: {len(fixed)} | exact: {len(ok)} | unresolved: {len(unresolved)}")

        for r in fixed:
            src = r.get('source', '')
            print(f"      fix: [{r['link']}] -> [{r['new']}]  ({r['method']}, src:{src})")
        for r in unresolved:
            cands = r.get('candidates', [])
            cand_str = ', '.join(cands) if cands else '(none)'
            print(f"      ??? : [{r['link']}]  candidates: {cand_str}")
        print()

    # summary
    print(f"{'=' * 60}")
    print(f"summary")
    print(f"{'=' * 60}")
    print(f"  files:      {total_files}")
    print(f"  fixed:      {total_fixed}")
    print(f"  unresolved: {total_unresolved}")

    unresolved_all = [r for r in all_report if r['result'] == 'unresolved']
    log_path = (input_dir if args.in_place else output_dir) / "fix_links_v2_unresolved.log"

    if not args.dry_run:
        if not args.in_place:
            output_dir.mkdir(parents=True, exist_ok=True)

        if unresolved_all:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("# fix_links_v2 未解决链接\n\n")
                agg: dict[str, dict] = {}
                for r in unresolved_all:
                    key = r['link']
                    if key not in agg:
                        agg[key] = {'count': 0, 'files': [], 'candidates': r.get('candidates', [])}
                    agg[key]['count'] += 1
                    if len(agg[key]['files']) < 5:
                        agg[key]['files'].append(r['file'])

                for link, info in sorted(agg.items(), key=lambda x: x[1]['count'], reverse=True):
                    cands = ', '.join(info['candidates']) if info['candidates'] else '(none)'
                    f.write(f"- `[[{link}]]`  x{info['count']}  candidates: {cands}\n")
                    f.write(f"  sources: {', '.join(info['files'])}\n")
                f.write(f"\n---\n{len(agg)} unique links, {len(unresolved_all)} total references\n")
            print(f"\n  unresolved log: {log_path}")

        report_path = (input_dir if args.in_place else output_dir) / "fix_links_v2_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'stats': {
                    'total_files': total_files,
                    'total_links': len(all_report),
                    'fixed': total_fixed,
                    'unresolved': total_unresolved,
                    'ok_exact': len([r for r in all_report if r['result'] == 'ok_exact']),
                },
                'report': all_report,
            }, f, ensure_ascii=False, indent=2)
        print(f"  report: {report_path}")

        if not args.in_place:
            print(f"  output dir: {output_dir}")
    else:
        print(f"\ndry-run done, no files written.")
        if unresolved_all:
            print(f"\nunresolved links({len(unresolved_all)}):")
            for r in unresolved_all:
                cands = r.get('candidates', [])
                cand_str = ', '.join(cands) if cands else '(none)'
                print(f"  [{r['file']}] [[{r['link']}]]  candidates: {cand_str}")


if __name__ == "__main__":
    main()
