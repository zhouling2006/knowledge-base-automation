#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_section.py - 节级匹配逻辑模块

从 fix_links_v2.py 抽取的匹配引擎核心：
  - remove_punctuation()      : 去标点
  - HierarchyIndex            : 三级索引类（小节→节→章）
  - _longest_common_substring(): LCS 算法
  - _collect_candidates()     : 基于公共子串收集候选
  - _find_in_scope()          : 在指定 scope 内查找
  - find_match()              : 三层递进匹配（含节级全量 LLM 步骤）
  - WIKILINK_RE / extract_context() : 双链正则与上下文提取
  - build_indexes()           : 生成聚合 memory.json
  - discover_hierarchy()      : 目录结构发现
"""

# stdout encoding 在主脚本 fix_links_v3.py 中统一设置

import re
import json
from pathlib import Path
from typing import Optional
from collections import defaultdict


# =============================================================================
# 标点去除
# =============================================================================

_PUNCT = re.compile(r'[\s\-_：:；;，,。.！!？?（(）)「」【】\[\]{}\'\"'"'"'·～~`#$%^&*@+/\\=|<>《》「」""''…—]')

def remove_punctuation(s: str) -> str:
    return _PUNCT.sub('', s)


# =============================================================================
# 三级索引
# =============================================================================

class HierarchyIndex:
    """
    三级索引：小节 -> 节 -> 章

    维护三个 stem 集合（层级包含关系）：
      chapter_stems ⊇ section_stems ⊇ subsection_stems
    entries 中低层级不覆盖高层级（先到先得）。
    """

    def __init__(self, subsection_dir: Path, section_dir: Path, chapter_dir: Path):
        self.subsection_dir = subsection_dir
        self.section_dir = section_dir
        self.chapter_dir = chapter_dir
        self.subsection_name = subsection_dir.name
        self.section_name = section_dir.name
        self.chapter_name = chapter_dir.name

        self.entries: dict[str, dict] = {}
        self.subsection_stems: set[str] = set()
        self.section_stems: set[str] = set()
        self.chapter_stems: set[str] = set()
        self.no_punct: dict[str, set[str]] = {}

        self._load()

    @staticmethod
    def _load_memory_json(mem_file: Path) -> list[dict]:
        result = []
        try:
            data = json.loads(mem_file.read_text(encoding='utf-8'))
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

TOP_N = 20


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
    """在指定 scope 集合中查找，返回 (matched, method, candidates)"""
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


def find_match_with_scope(
    link_text: str, idx: HierarchyIndex,
) -> tuple[Optional[str], str, list[str], str]:
    """
    三层递进匹配 + 返回当前查到的 scope 层级。

    返回 (matched, method, candidates, scope_level)
    scope_level: 'subsection' | 'section' | 'chapter'
    """
    if link_text.endswith('.md'):
        link_text = link_text[:-3]
    link_text = link_text.strip()
    np_link = remove_punctuation(link_text)

    # 第一层：小节
    matched, method, candidates = _find_in_scope(link_text, np_link, idx, idx.subsection_stems)
    if matched is not None:
        return matched, f"[subsec]{method}", [], "subsection"
    if candidates:
        return None, f"[subsec]{method}", candidates, "subsection"

    # 第二层：节（排除小节已有的）
    section_only = idx.section_stems - idx.subsection_stems
    matched, method, candidates = _find_in_scope(link_text, np_link, idx, section_only)
    if matched is not None:
        return matched, f"[sec]{method}", [], "section"
    if candidates:
        return None, f"[sec]{method}", candidates, "section"

    # 第三层：章（排除节已有的）
    chapter_only = idx.chapter_stems - idx.section_stems
    matched, method, candidates = _find_in_scope(link_text, np_link, idx, chapter_only)
    if matched is not None:
        return matched, f"[chap]{method}", [], "chapter"
    if candidates:
        return None, f"[chap]{method}", candidates, "chapter"

    return None, "[chap]no_match", [], "chapter"


def get_scope_stems(idx: HierarchyIndex, level: str) -> list[str]:
    """获取指定层级的 stem 列表（用于 LLM 全量模式）"""
    if level == "subsection":
        stems = sorted(idx.subsection_stems)
    elif level == "section":
        stems = sorted(idx.section_stems)
    else:
        stems = sorted(idx.chapter_stems)

    source_order = {'subsection': 0, 'section': 1, 'chapter': 2}
    stems.sort(key=lambda s: source_order.get(idx.entries.get(s, {}).get('source', 'chapter'), 9))
    return stems


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
# 索引构建
# =============================================================================

def build_indexes(input_dir: Path):
    """生成/更新各层级聚合 memory.json"""
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
                if section_dir not in (chapters.get(chapter_dir) or []):
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
