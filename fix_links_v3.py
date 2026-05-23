#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_links_v3.py - 双链引用修复工具 v3（节级 LLM + 重验证）

匹配流程（范围从小到大逐级放宽）：
  1. 字符串匹配（精确→去标点→LCS），三层递进：小节→节→章
  2. exact/depunct唯一命中 → 直接返回（不经过 LLM/verify）
  3. LLM 小节级全量（subsection_stems, 4~21条）
  4. LLM 节级全量（section_stems, ~30~85条）
  5. LLM 全章候选模式（LCS top20，全章范围最后兜底）
  6. LLM 结果均经 llm_verify 二次校验（防完全无关匹配）
  7. verify 失败或全部未命中 → 标记为 unresolved

用法：
  python fix_links_v3.py --build-index           # 生成/更新各层级聚合 memory.json
  python fix_links_v3.py                          # 修复 processed_output_t，写入 processed_output_t_v3
  python fix_links_v3.py --dry-run                # 只报告，不写文件
  python fix_links_v3.py --no-llm                 # 禁用 LLM
  python fix_links_v3.py --no-verify              # 禁用重验证
  python fix_links_v3.py --in-place               # 直接覆盖原文件（慎用）
"""

import sys
import io
import os
import re
import json
import argparse
from pathlib import Path
from typing import Optional

# 模块化导入
from llm_section import (
    HierarchyIndex, find_match_with_scope, get_scope_stems,
    WIKILINK_RE, extract_context,
    build_indexes, discover_hierarchy,
)
from llm_prompt import llm_pick, llm_verify, format_candidates, _extract_numbered_prefix

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# =============================================================================
# LLM 递进匹配（核心改进）
# =============================================================================

def llm_cascade_match(
    link_text: str, idx: HierarchyIndex, context: str = "",
    use_llm: bool = True, use_verify: bool = True,
    source_stem: str = "",
) -> tuple[Optional[str], str, bool, list[str]]:
    """
    递进式 LLM 匹配：候选模式 → 节级全量 → 章级全量，每步都带验证。

    返回 (matched_stem, method_str, verified, candidates)
    - matched_stem: 匹配到的 stem 或 None
    - method_str: 匹配方法描述
    - verified: 是否通过验证
    - candidates: 字符串匹配阶段的候选列表（用于调试报告）
    - source_stem: 当前源文件的 stem，用于排除自引用
    """
    if not use_llm:
        return None, "no_llm", False, []

    # 首先做字符串匹配，获取初始 candidates 和 scope_level
    matched, method, candidates, scope_level = find_match_with_scope(link_text, idx)

    # 字符串精确匹配（直接返回）
    if matched == link_text:
        return matched, method, True, []

    if matched is not None and matched != link_text:
        # 字符串匹配（depunct 唯一命中）→ 不验证，直接返回
        return matched, method, True, []

    # ---- 编号前缀匹配（确定性规则，不走 LLM） ----
    # 例1.6.10/定理1.4.3 等，编号唯一确定文档，文件名去标点也不影响
    numbered_prefix = _extract_numbered_prefix(link_text)
    if numbered_prefix:
        chapter_stems = get_scope_stems(idx, "chapter")
        prefix_matches = [s for s in chapter_stems
                          if s.startswith(numbered_prefix) and s != source_stem]
        if len(prefix_matches) == 1:
            return prefix_matches[0], "numbered_prefix", True, []

    # ---- 以下进入 LLM 流程（范围从小到大逐级放宽） ----

    # 步骤 1: LLM 小节级全量（范围最小，最相关，4~21条）
    subsection_stems = [s for s in get_scope_stems(idx, "subsection") if s != source_stem]
    if subsection_stems:
        picked = llm_pick(link_text, subsection_stems, idx, context, full_list=True)
        if picked:
            if use_verify:
                ok, reason = llm_verify(link_text, picked, idx, context, source_stem)
                if ok:
                    return picked, "[subsec]full_llm+verified", True, candidates
                else:
                    print(f"      ! verify REJECT: [{link_text}] -> [{picked}] ({reason})")
            else:
                return picked, "[subsec]full_llm", False, candidates

    # 步骤 2: LLM 节级全量（范围扩大，~30~85条）
    section_stems = [s for s in get_scope_stems(idx, "section") if s != source_stem]
    if section_stems:
        picked = llm_pick(link_text, section_stems, idx, context, full_list=True)
        if picked:
            if use_verify:
                ok, reason = llm_verify(link_text, picked, idx, context, source_stem)
                if ok:
                    return picked, "[sec]full_llm+verified", True, candidates
                else:
                    print(f"      ! verify REJECT: [{link_text}] -> [{picked}] ({reason})")
            else:
                return picked, "[sec]full_llm", False, candidates

    # 步骤 3: LLM 全章候选模式（最后兜底，从 LCS 候选 top20 中精选）
    if candidates:
        # 过滤自引用
        filtered_cands = [c for c in candidates if c != source_stem]
        picked = llm_pick(link_text, filtered_cands, idx, context, full_list=False)
        if picked:
            if use_verify:
                ok, reason = llm_verify(link_text, picked, idx, context, source_stem)
                if ok:
                    return picked, f"{method}+llm_cand+verified", True, candidates
                else:
                    print(f"      ! verify REJECT: [{link_text}] -> [{picked}] ({reason})")
                    return None, f"{method}+llm_cand+verify_reject", False, candidates
            else:
                return picked, f"{method}+llm_cand", False, candidates

    return None, "unresolved", False, candidates


# =============================================================================
# 处理单个文件
# =============================================================================

def process_file(
    md_path: Path, idx: HierarchyIndex, use_llm: bool, use_verify: bool,
    report: list[dict],
) -> str:
    content = md_path.read_text(encoding='utf-8')

    # 收集所有待处理链接
    pending: list[tuple[re.Match, str, str]] = []  # (match, link_text, attrs)
    for m in WIKILINK_RE.finditer(content):
        link_text = m.group(1).strip()
        attrs = m.group(2) or ""
        pending.append((m, link_text, attrs))

    new_content = content

    for match_obj, link_text, attrs in pending:
        _candidates: list[str] = []
        if use_llm:
            ctx = extract_context(content, link_text)
            picked, method, verified, _candidates = llm_cascade_match(
                link_text, idx, ctx, use_llm=True, use_verify=use_verify,
                source_stem=md_path.stem,
            )
        else:
            matched, method, candidates_no_llm, scope_level = find_match_with_scope(link_text, idx)
            if matched == link_text:
                report.append({'file': md_path.name, 'link': link_text,
                               'result': 'ok_exact', 'method': method, 'new': None})
                continue
            if matched and matched != link_text:
                entry = idx.entries.get(matched, {})
                report.append({'file': md_path.name, 'link': link_text,
                               'result': 'fixed', 'method': method, 'new': matched,
                               'source': entry.get('source', '')})
                repl_text = f"[[{matched}]]{attrs}"
                new_content = re.sub(re.escape(match_obj.group(0)), lambda m: repl_text, new_content, count=1)
                continue
            picked, method, verified, _candidates = None, method, False, candidates_no_llm

        if picked:
            entry = idx.entries.get(picked, {})
            source = entry.get('source', '?')
            verify_tag = "+V" if verified else ""
            print(f"      + [{link_text}] -> [{picked}] ({method}{verify_tag}, src:{source})")
            report.append({'file': md_path.name, 'link': link_text,
                           'result': 'fixed_llm', 'method': method,
                           'new': picked, 'source': source, 'verified': verified})
            repl_text = f"[[{picked}]]{attrs}"
            new_content = re.sub(re.escape(match_obj.group(0)), lambda m: repl_text, new_content, count=1)
        else:
            # 检查是否精确匹配（在 llm_cascade_match 中直接返回的）
            # 先单独检查精确匹配
            if link_text in idx.entries or link_text in idx.subsection_stems or link_text in idx.section_stems or link_text in idx.chapter_stems:
                report.append({'file': md_path.name, 'link': link_text,
                               'result': 'ok_exact', 'method': 'exact', 'new': None})
                continue

            report.append({'file': md_path.name, 'link': link_text,
                           'result': 'unresolved', 'method': method, 'new': None,
                           'candidates': _candidates})
            print(f"      - [{link_text}]  ({method})")

    return new_content


# =============================================================================
# 主流程
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="双链引用修复工具 v3（节级 LLM + 重验证）",
        epilog="""
示例：
  python fix_links_v3.py --build-index
  python fix_links_v3.py
  python fix_links_v3.py --dry-run
  python fix_links_v3.py --no-llm
  python fix_links_v3.py --no-verify
  python fix_links_v3.py --in-place
""",
    )
    parser.add_argument("--input-dir", "-i", default=None)
    parser.add_argument("--output-dir", "-o", default=None)
    parser.add_argument("--build-index", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--no-verify", action="store_true", help="禁用重验证")
    parser.add_argument("--in-place", action="store_true")
    args = parser.parse_args()

    BASE = Path(__file__).parent.resolve()
    input_dir = Path(args.input_dir) if args.input_dir else BASE / "processed_output_t"
    output_dir = (
        Path(input_dir) if args.in_place
        else (Path(args.output_dir) if args.output_dir else BASE / "processed_output_t_v3")
    )
    use_llm = not args.no_llm
    use_verify = not args.no_verify and use_llm

    print(f"\n{'=' * 60}")
    print(f"fix_links_v3 - 节级 LLM + 重验证")
    print(f"{'=' * 60}")
    print(f"  input:  {input_dir}")
    print(f"  output: {'(in-place)' if args.in_place else output_dir}")
    print(f"  mode:   {'dry-run' if args.dry_run else 'write'}")
    print(f"  LLM:    {'off' if not use_llm else 'on'}")
    print(f"  verify: {'off' if not use_verify else 'on'}")
    print(f"{'=' * 60}\n")

    if not input_dir.exists():
        print(f"error: input dir not found: {input_dir}")
        sys.exit(1)

    if args.build_index:
        build_indexes(input_dir)
        return

    hierarchy = discover_hierarchy(input_dir)
    if not hierarchy:
        print("error: no _*_memory.json found")
        sys.exit(1)

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
    total_verified_ok = 0
    total_verified_reject = 0

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
            new_content = process_file(md, idx, use_llm, use_verify, sec_report)
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
        verified_ok = [r for r in sec_report if r.get('verified') is True]
        verified_reject = [r for r in sec_report if r['method'] and 'verify_reject' in r['method']]

        total_fixed += len(fixed)
        total_unresolved += len(unresolved)
        total_verified_ok += len(verified_ok)
        total_verified_reject += len(verified_reject)
        all_report.extend(sec_report)

        print(f"   fixed: {len(fixed)} | exact: {len(ok)} | unresolved: {len(unresolved)} | verified_ok: {len(verified_ok)} | verified_reject: {len(verified_reject)}")

        for r in fixed:
            src = r.get('source', '')
            v = "+V" if r.get('verified') else ""
            print(f"      fix: [{r['link']}] -> [{r['new']}]  ({r['method']}{v}, src:{src})")
        for r in unresolved:
            cands = r.get('candidates', [])
            cand_str = ', '.join(cands) if cands else '(none)'
            print(f"      ??? : [{r['link']}]  ({r.get('method','')})  candidates: {cand_str}")
        print()

    # summary
    print(f"{'=' * 60}")
    print(f"summary")
    print(f"{'=' * 60}")
    print(f"  files:            {total_files}")
    print(f"  fixed:            {total_fixed}")
    print(f"  unresolved:       {total_unresolved}")
    print(f"  verified_ok:      {total_verified_ok}")
    print(f"  verified_reject:  {total_verified_reject}")

    unresolved_all = [r for r in all_report if r['result'] == 'unresolved']
    log_path = (input_dir if args.in_place else output_dir) / "fix_links_v3_unresolved.log"

    if not args.dry_run:
        if not args.in_place:
            output_dir.mkdir(parents=True, exist_ok=True)

        if unresolved_all:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write("# fix_links_v3 未解决链接\n\n")
                agg: dict[str, dict] = {}
                for r in unresolved_all:
                    key = r['link']
                    if key not in agg:
                        agg[key] = {'count': 0, 'files': [], 'method': r.get('method', '')}
                    agg[key]['count'] += 1
                    if len(agg[key]['files']) < 5:
                        agg[key]['files'].append(r['file'])

                for link, info in sorted(agg.items(), key=lambda x: x[1]['count'], reverse=True):
                    f.write(f"- `[[{link}]]`  x{info['count']}  method: {info['method']}\n")
                    f.write(f"  sources: {', '.join(info['files'])}\n")
                f.write(f"\n---\n{len(agg)} unique links, {len(unresolved_all)} total references\n")
            print(f"\n  unresolved log: {log_path}")

        report_path = (input_dir if args.in_place else output_dir) / "fix_links_v3_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                'stats': {
                    'total_files': total_files,
                    'total_links': len(all_report),
                    'fixed': total_fixed,
                    'unresolved': total_unresolved,
                    'ok_exact': len([r for r in all_report if r['result'] == 'ok_exact']),
                    'verified_ok': total_verified_ok,
                    'verified_reject': total_verified_reject,
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
                print(f"  [{r['file']}] [[{r['link']}]]  ({r.get('method','')})")


if __name__ == "__main__":
    main()
