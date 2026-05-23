#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_links_v2.py — 双链引用修复工具（节级别）

针对 processed_output 下每一个"节目录"（含 _*_memory.json 的目录），
检查其中所有 .md 文件的 [[链接文本]]{...} 引用是否命中该节的已知文件。

修复逻辑：
  - 索引来源：同节的 _*_memory.json（filename stem 列表 + title + summary）
  - 匹配策略（按优先级）：
      1. 精确匹配（link_text == stem）→ 跳过
      2. 去标点后精确匹配（唯一候选 → 自动选） 
      3. 公共子串匹配（最长公共连续子串 ≥ 短者 50%）→ 收集候选
      4. 以上全部未命中 → 整节全量文档列表交给 LLM
  - 所有不确定的（有候选或无候选）统一交给 LLM 判断，允许返回"确实没有匹配"
  - 无论如何无法匹配 → 记录到 fix_links_v2_unresolved.log

用法：
  python fix_links_v2.py                         # 修复 processed_output，写入 processed_output_v2
  python fix_links_v2.py --dry-run               # 只报告，不写文件
  python fix_links_v2.py --no-llm                # 禁用 LLM 兜底（仅字符串匹配）
  python fix_links_v2.py --in-place              # 直接覆盖原文件（慎用）
  python fix_links_v2.py --input-dir <dir>       # 指定输入目录
  python fix_links_v2.py --output-dir <dir>      # 指定输出目录
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

PUNCT = '：:，,、；;【】[]（）()《》""\'\'「」『』〈〉〖〗·•…⋯—–-‐$（）——\\/+^={}'


def remove_punctuation(s: str) -> str:
    """去除常见标点与空白，保留中英文、数字"""
    result = s
    for p in PUNCT:
        result = result.replace(p, '')
    result = re.sub(r'\s+', '', result)
    return result


# =============================================================================
# 节级索引
# =============================================================================

class SectionIndex:
    """
    从一个节目录的 _*_memory.json 构建索引。
    同时实际扫描目录里的 .md 文件（避免 memory.json 与实际文件不一致）。
    """

    def __init__(self, section_dir: Path):
        self.section_dir = section_dir
        # stem → {"filename", "title", "summary", "path"}
        self.entries: dict[str, dict] = {}
        # 去标点后 stem → set of original stems
        self.no_punct: dict[str, set] = {}
        self._load()

    def _load(self):
        # 1. 从 memory.json 加载 title / summary
        mem_info: dict[str, dict] = {}  # stem → {title, summary}
        for mem_file in self.section_dir.glob("*_memory.json"):
            try:
                data = json.loads(mem_file.read_text(encoding='utf-8'))
                for item in data:
                    fname = item.get('filename', '')
                    stem = Path(fname).stem
                    mem_info[stem] = {
                        'title': item.get('title', stem),
                        'summary': item.get('summary', ''),
                    }
            except Exception as e:
                print(f"  ⚠️ 读取 memory.json 失败: {mem_file} — {e}")

        # 2. 扫描实际存在的 .md 文件
        for md in self.section_dir.glob("*.md"):
            if md.name.startswith('_') or md.name.startswith('.'):
                continue
            stem = md.stem
            info = mem_info.get(stem, {})
            self.entries[stem] = {
                'filename': md.name,
                'title': info.get('title', stem),
                'summary': info.get('summary', ''),
                'path': str(md),
            }

        # 3. 建立去标点索引
        for stem in self.entries:
            np = remove_punctuation(stem)
            if np not in self.no_punct:
                self.no_punct[np] = set()
            self.no_punct[np].add(stem)

    def __len__(self):
        return len(self.entries)

    def stems(self) -> list[str]:
        return list(self.entries.keys())


# =============================================================================
# 匹配引擎
# =============================================================================

TOP_N = 5


def _longest_common_substring(s1: str, s2: str) -> int:
    """返回两字符串的最长公共连续子串长度（动态规划）"""
    m, n = len(s1), len(s2)
    if m == 0 or n == 0:
        return 0
    # 空间优化：只保留上一行
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


def _collect_candidates(
    np_link: str, idx: SectionIndex,
) -> list[tuple[str, float, str]]:
    """
    用公共子串匹配收集候选。
    返回 [(stem, score, reason), ...] 按 score 降序。

    规则：
    - 公共子串长度 >= min(link_len, stem_len) 的 50% → 入选
    - score = 公共子串长度 / max(link_len, stem_len)
    - 去标点后完全包含（一个 ⊂ 另一个）→ score 取较大值
    """
    link_len = len(np_link)
    if link_len == 0:
        return []

    candidates: list[tuple[str, float, str]] = []

    for np_name, stems in idx.no_punct.items():
        if np_name == np_link:
            continue

        stem_len = len(np_name)

        # 完全包含：一个 ⊂ 另一个
        if np_link in np_name:
            score = link_len / stem_len if stem_len > 0 else 1.0
            for s in stems:
                candidates.append((s, score, "包含"))
            continue
        if np_name in np_link:
            score = stem_len / link_len if link_len > 0 else 1.0
            for s in stems:
                candidates.append((s, score, "包含"))
            continue

        # 公共子串匹配
        lcs = _longest_common_substring(np_link, np_name)
        threshold = min(link_len, stem_len) * 0.5
        if lcs >= threshold and lcs >= 2:  # 至少 2 个字符的公共子串
            ml = max(link_len, stem_len)
            score = lcs / ml
            for s in stems:
                candidates.append((s, score, f"公共子串{lcs}字"))

    # 去重（同一 stem 可能被多条规则命中，取最高分）
    best: dict[str, tuple[float, str]] = {}
    for stem, score, reason in candidates:
        if stem not in best or score > best[stem][0]:
            best[stem] = (score, reason)

    result = [(stem, score, reason) for stem, (score, reason) in best.items()]
    result.sort(key=lambda x: x[1], reverse=True)
    return result


def find_match(
    link_text: str,
    idx: SectionIndex,
) -> tuple[Optional[str], str, list[str]]:
    """
    返回 (matched_stem | None, method_desc, candidates_list)

    匹配策略（按优先级）：
      1. 精确匹配（原文 == stem）→ 不动
      2. 去标点后精确匹配（唯一候选 → 自动选）
      3. 公共子串匹配 → 收集候选，交给 LLM
      4. 无候选 → 整节全量列表交给 LLM（允许返回"真的没有"）

    - matched_stem 非 None 且 == link_text → 已精确命中，无需修改
    - matched_stem 非 None 且 != link_text → 可替换
    - matched_stem is None → 需 LLM 判断（candidates 可能非空也可能空）
    """
    # 预处理
    if link_text.endswith('.md'):
        link_text = link_text[:-3]
    link_text = link_text.strip()

    np_link = remove_punctuation(link_text)

    # --- 精确匹配 ---
    if link_text in idx.entries:
        return link_text, "精确命中", []

    # --- 去标点后精确匹配 ---
    if np_link in idx.no_punct:
        hits = idx.no_punct[np_link]
        if len(hits) == 1:
            return next(iter(hits)), "去标点精确", []
        # 多个去标点重名 → LLM
        return None, "去标点多候选", list(hits)

    # --- 公共子串候选收集 ---
    candidates = _collect_candidates(np_link, idx)
    if candidates:
        cand_names = [name for name, _, _ in candidates[:TOP_N]]
        return None, f"字符串候选({len(candidates)})", cand_names

    # --- 完全无候选 → LLM 用全量列表判断 ---
    return None, "无匹配", []


# =============================================================================
# LLM 兜底
# =============================================================================

_LLM_SYSTEM = """你是数学知识点双链修复助手。给定一段双链引用文本和文档列表，
判断该引用最应该指向哪个文档（基于语义相近程度）。

核心规则：
1. 引用文本可能只是文档名的一部分（如"例1.1.13"对应"例1.1.13-直角坐标方程化为极坐标方程"）
2. 引用文本可能是概念的不同表述（如"夹逼准则"对应"例1.6.8续-由夹逼准则得右极限"）
3. 不要选语义范围更宽泛的候选：若引用文本是"导数的几何意义"，不应选"导数的几何意义与物理意义"
4. 优先选范围完全一致或更具体的候选
5. 如没有任何合适的文档，返回 0

输出格式：只输出一个整数，代表选择的候选序号（从 1 开始），或 0 代表无合适候选。
不要输出任何其他内容。"""


def call_llm(user_prompt: str, max_retries: int = 2) -> Optional[str]:
    try:
        from openai import OpenAI
    except ImportError:
        print("    ⚠️ openai 未安装，跳过 LLM")
        return None

    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        print("    ⚠️ DASHSCOPE_API_KEY 未设置，跳过 LLM")
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
            print(f"    ⚠️ LLM 失败({attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(2)
    return None


def _format_candidates(link_text: str, candidates: list[str], idx: SectionIndex,
                       context: str = "") -> str:
    """构造候选列表 prompt"""
    lines = [f"引用文本: 【{link_text}】"]
    if context:
        lines.append(f"上下文: ...{context}...")
    lines.append("候选文档列表：")
    for i, stem in enumerate(candidates, 1):
        entry = idx.entries.get(stem, {})
        title = entry.get('title', stem)
        summary = entry.get('summary', '')
        lines.append(f"  {i}. {stem}")
        if title != stem:
            lines.append(f"     标题: {title}")
        if summary:
            lines.append(f"     摘要: {summary[:120]}")
    return '\n'.join(lines)


def llm_pick(link_text: str, candidates: list[str], idx: SectionIndex,
             context: str = "", full_list: bool = False) -> Optional[str]:
    """
    让 LLM 判断引用指向哪个文档。

    full_list=True 时，candidates 为空列表，LLM 会从整节所有文档中选择（或返回 0）。
    full_list=False 时，candidates 为字符串候选子集。
    """
    if full_list:
        # 全量模式：列出节内所有文档
        all_stems = sorted(idx.stems())
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
            return None  # LLM 认为没有合适的
        target_list = sorted(idx.stems()) if full_list else candidates
        if 1 <= n <= len(target_list):
            return target_list[n - 1]
    return None


# =============================================================================
# 双链正则与上下文提取
# =============================================================================

# 匹配 [[链接文本]] 或 [[链接文本]]{属性}
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
    md_path: Path,
    idx: SectionIndex,
    use_llm: bool,
    report: list[dict],
) -> str:
    """
    处理单个 .md 文件，返回修复后的内容。
    report 中追加每次链接的处理记录。
    """
    content = md_path.read_text(encoding='utf-8')

    # 收集所有链接，先做字符串匹配；需 LLM 的放入队列
    llm_pending: list[dict] = []   # {link_text, attrs, context, candidates, full_list}

    def first_pass(m: re.Match) -> str:
        link_text = m.group(1).strip()
        attrs = m.group(2) or ""

        matched, method, candidates = find_match(link_text, idx)

        # 已精确命中（link_text 本身就是合法 stem）→ 不动
        if matched == link_text:
            report.append({
                'file': md_path.name,
                'link': link_text,
                'result': 'ok_exact',
                'method': method,
                'new': None,
            })
            return m.group(0)

        # 找到唯一匹配 → 记录替换
        if matched is not None and matched != link_text:
            report.append({
                'file': md_path.name,
                'link': link_text,
                'result': 'fixed',
                'method': method,
                'new': matched,
            })
            return f"[[{matched}]]{attrs}"

        # 未匹配 → 一律交给 LLM（有候选用候选列表，无候选用全量列表）
        if use_llm:
            ctx = extract_context(content, link_text)
            full_list = len(candidates) == 0
            llm_pending.append({
                'link_text': link_text,
                'attrs': attrs,
                'candidates': candidates,
                'context': ctx,
                'full_list': full_list,
            })

        report.append({
            'file': md_path.name,
            'link': link_text,
            'result': 'pending_llm' if use_llm else 'unresolved',
            'method': method,
            'new': None,
            'candidates': candidates[:5],
        })
        return m.group(0)

    new_content = WIKILINK_RE.sub(first_pass, content)

    # LLM 批量处理
    if llm_pending:
        print(f"    🤖 LLM 判断 {len(llm_pending)} 个链接 in [{md_path.name}]")
        for item in llm_pending:
            picked = llm_pick(
                item['link_text'],
                item['candidates'],
                idx,
                item['context'],
                full_list=item['full_list'],
            )
            if picked:
                mode = "全量" if item['full_list'] else "候选"
                print(f"      ✅ [{item['link_text']}] → [{picked}] ({mode})")
                # 更新 report
                for r in report:
                    if (r['file'] == md_path.name
                            and r['link'] == item['link_text']
                            and r['result'] == 'pending_llm'):
                        r['result'] = 'fixed_llm'
                        r['new'] = picked
                        break
                # 在 new_content 中做替换
                pattern = re.compile(
                    r'\[\[' + re.escape(item['link_text']) + r'\]\]'
                    + r'(\{[^}]*\})?'
                )
                attrs = item['attrs']

                def make_rep(stem=picked, a=attrs):
                    def rep(mm: re.Match) -> str:
                        real_attrs = mm.group(1) or a
                        return f"[[{stem}]]{real_attrs}"
                    return rep

                new_content = pattern.sub(make_rep(), new_content)
            else:
                # LLM 认为没有合适匹配
                llm_verdict = "LLM确认无匹配" if item['full_list'] else "LLM无结果"
                print(f"      ❌ [{item['link_text']}] {llm_verdict}")
                for r in report:
                    if (r['file'] == md_path.name
                            and r['link'] == item['link_text']
                            and r['result'] == 'pending_llm'):
                        r['result'] = 'unresolved'
                        r['method'] = r['method'].replace('无匹配', f'LLM无匹配') if item['full_list'] else r['method']
                        break

    return new_content


# =============================================================================
# 主流程
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="双链引用修复工具 v2（节级别，基于 memory.json）",
        epilog="""
示例：
  python fix_links_v2.py
  python fix_links_v2.py --dry-run
  python fix_links_v2.py --no-llm
  python fix_links_v2.py --in-place
  python fix_links_v2.py --input-dir ./processed_output --output-dir ./processed_output_fixed
""",
    )
    parser.add_argument("--input-dir", "-i", default=None,
                        help="输入目录（默认：脚本同目录/processed_output）")
    parser.add_argument("--output-dir", "-o", default=None,
                        help="输出目录（默认：processed_output_v2）")
    parser.add_argument("--dry-run", action="store_true",
                        help="只报告，不写文件")
    parser.add_argument("--no-llm", action="store_true",
                        help="禁用 LLM 兜底")
    parser.add_argument("--in-place", action="store_true",
                        help="直接覆盖原文件（慎用）")
    args = parser.parse_args()

    BASE = Path(__file__).parent.resolve()
    input_dir = Path(args.input_dir) if args.input_dir else BASE / "processed_output"
    output_dir = (
        Path(input_dir) if args.in_place
        else (Path(args.output_dir) if args.output_dir else BASE / "processed_output_v2")
    )
    use_llm = not args.no_llm

    print(f"\n{'=' * 60}")
    print(f"🔗 fix_links_v2 — 节级双链修复工具")
    print(f"{'=' * 60}")
    print(f"  输入:   {input_dir}")
    print(f"  输出:   {'(原地覆盖)' if args.in_place else output_dir}")
    print(f"  模式:   {'dry-run' if args.dry_run else '写入'}")
    print(f"  LLM:    {'关闭' if not use_llm else '开启'}")
    print(f"{'=' * 60}\n")

    if not input_dir.exists():
        print(f"❌ 输入目录不存在: {input_dir}")
        sys.exit(1)

    # 发现所有节目录（含 _*_memory.json 的目录）
    section_dirs: list[Path] = []
    for mem in sorted(input_dir.rglob("*_memory.json")):
        section_dirs.append(mem.parent)

    if not section_dirs:
        print("❌ 未找到任何 _*_memory.json，请确认 --input-dir 是否正确")
        sys.exit(1)

    print(f"📂 发现 {len(section_dirs)} 个节目录\n")

    all_report: list[dict] = []
    total_files = 0
    total_fixed = 0
    total_unresolved = 0

    for sec_dir in section_dirs:
        idx = SectionIndex(sec_dir)
        rel_sec = sec_dir.relative_to(input_dir)
        print(f"▶ [{rel_sec}]  ({len(idx)} 个文件索引)")

        md_files = [
            f for f in sec_dir.glob("*.md")
            if not f.name.startswith('_') and not f.name.startswith('.')
        ]

        if not md_files:
            print(f"   (无 .md 文件，跳过)\n")
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

        # 节统计
        fixed = [r for r in sec_report if r['result'].startswith('fixed')]
        unresolved = [r for r in sec_report if r['result'] == 'unresolved']
        ok = [r for r in sec_report if r['result'] == 'ok_exact']

        total_fixed += len(fixed)
        total_unresolved += len(unresolved)
        all_report.extend(sec_report)

        print(f"   ✅ 已修复 {len(fixed)} | ⏭  无需修改 {len(ok)} | ❓ 无匹配 {len(unresolved)}")

        # 打印本节的修复和未解决详情
        for r in fixed:
            print(f"      fix: [{r['link']}] → [{r['new']}]  ({r['method']})")
        for r in unresolved:
            cands = r.get('candidates', [])
            cand_str = ', '.join(cands) if cands else '（无候选）'
            print(f"      ??? : [{r['link']}]  候选: {cand_str}")
        print()

    # 汇总统计
    print(f"{'=' * 60}")
    print(f"📊 汇总")
    print(f"{'=' * 60}")
    print(f"  处理文件:  {total_files}")
    print(f"  ✅ 修复:   {total_fixed}")
    print(f"  ❓ 未解决: {total_unresolved}")

    # 保存未解决日志
    unresolved_all = [r for r in all_report if r['result'] == 'unresolved']
    log_path = (input_dir if args.in_place else output_dir) / "fix_links_v2_unresolved.log"

    if not args.dry_run:
        # 补全 output_dir
        if not args.in_place:
            output_dir.mkdir(parents=True, exist_ok=True)

        if unresolved_all:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("# fix_links_v2 未解决链接\n\n")
                # 按链接文本聚合去重，标注出现次数
                from collections import Counter
                agg: dict[str, dict] = {}
                for r in unresolved_all:
                    key = r['link']
                    if key not in agg:
                        agg[key] = {'count': 0, 'files': [], 'candidates': r.get('candidates', [])}
                    agg[key]['count'] += 1
                    if len(agg[key]['files']) < 5:  # 最多记录 5 个来源文件
                        agg[key]['files'].append(r['file'])

                # 按出现次数降序
                for link, info in sorted(agg.items(), key=lambda x: x[1]['count'], reverse=True):
                    cands = ', '.join(info['candidates']) if info['candidates'] else '（无候选）'
                    f.write(f"- `[[{link}]]`  ×{info['count']}  候选: {cands}\n")
                    f.write(f"  来源: {', '.join(info['files'])}\n")
                f.write(f"\n---\n共 {len(agg)} 条不重复链接，{len(unresolved_all)} 次引用\n")
            print(f"\n📄 未解决日志: {log_path}")

        # 保存完整 JSON 报告
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
        print(f"📄 完整报告: {report_path}")

        if not args.in_place:
            print(f"📁 输出目录: {output_dir}")
    else:
        print(f"\n🔍 Dry-run 完成，未写入任何文件。")
        if unresolved_all:
            print(f"\n未解决链接({len(unresolved_all)})：")
            for r in unresolved_all:
                cands = r.get('candidates', [])
                cand_str = ', '.join(cands) if cands else '（无候选）'
                print(f"  [{r['file']}] [[{r['link']}]]  候选: {cand_str}")


if __name__ == "__main__":
    main()
