#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化流水线：将 prograhspilt.py 和 reprocess_original.py 串联执行

用法：
  python run_all.py -i "高等数学改/第一章/二、函数的概念.md"
  python run_all.py -i "高等数学改/第一章"          # 批量处理目录下所有 .md（非习题）
  python run_all.py --dry-run                       # 只生成提示词
"""

import sys
import io
import os
import re
import time
import subprocess
from pathlib import Path

# Windows 编码修复
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ==================== 配置区 ====================
PYTHON = "python"
WORKDIR = Path(__file__).parent.resolve()

# 中间 JSON 文件统一存放目录（切分步骤产出）
SEGMENTS_DIR = WORKDIR / "segments_output"
# 最终文档输出根目录（reprocess 步骤产出，按源文件分目录）
OUTPUT_ROOT = WORKDIR / "processed_output"
BATCH_SIZE = 4
# ============================================


def is_exercise_file(path: Path) -> bool:
    """判断是否为习题类文件（跳过）"""
    name = path.stem
    return bool(re.search(r'习题|练习|作业', name))


def find_markdown_files(target: str) -> list[Path]:
    """
    根据 target 返回要处理的文件列表：
    - 如果是 .md 文件，直接返回
    - 如果是目录，递归列出所有 .md（排除习题）
    """
    # Windows 上把 forward slash 转成 backslash
    if sys.platform == 'win32':
        target = target.replace('/', '\\')

    # 拼成绝对路径
    p = Path(target)
    if not p.is_absolute():
        p = (WORKDIR / target).resolve()

    if p.is_file():
        return [p] if p.suffix == '.md' else []
    elif p.is_dir():
        return sorted([f.resolve() for f in p.rglob("*.md") if not is_exercise_file(f)])

    print(f"❌ 路径不存在: {p}")
    return []


def run(script_name: str, args: list[str], desc: str, cwd: str = None) -> int:
    """执行 Python 脚本，失败则退出"""
    cmd = [PYTHON, str(WORKDIR / script_name)] + args
    print(f"\n{'=' * 50}")
    print(f"[步骤] {desc}")
    print(f"{'=' * 50}")
    print(f"执行: {' '.join(cmd)}\n")

    result = subprocess.run(cmd, cwd=cwd or str(WORKDIR), encoding='utf-8')
    if result.returncode != 0:
        print(f"\n❌ 脚本执行失败（exit {result.returncode}）")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        sys.exit(1)

    if result.stdout:
        print(result.stdout)
    return result.returncode


def extract_json_filename(stdout: str) -> str | None:
    """从 prograhspilt.py 的 stdout 中提取生成的 JSON 文件名"""
    for line in stdout.split('\n'):
        if 'segment.json' in line:
            parts = line.split('：')
            if len(parts) < 2:
                parts = line.split(' ')
            filename = parts[-1].strip()
            if filename.endswith('-segment.json') or filename.endswith('segment.json'):
                return filename
    return None


def process_single_file(input_md: Path, dry_run: bool = False, batch_size: int = 4) -> bool:
    """处理单个 md 文件，返回是否成功"""
    src_stem = re.sub(r'[^\w\u4e00-\u9fff-]', '_', input_md.stem).strip('_')
    seg_dir = SEGMENTS_DIR
    out_dir = OUTPUT_ROOT / src_stem

    print(f"\n{'#' * 60}")
    print(f"# 处理文件：{input_md}")
    print(f"# 中间 JSON：{seg_dir}")
    print(f"# 最终输出：{out_dir}")
    print(f"{'#' * 60}")

    # 确保目录存在
    seg_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ========== 步骤1：生成 JSON ==========
    print(f"\n[步骤1] 调用 prograhspilt.py 切分...")
    result1 = subprocess.run(
        [PYTHON, str(WORKDIR / "prograhspilt.py"), "--input", str(input_md)],
        cwd=str(WORKDIR), encoding='utf-8', capture_output=True, text=True
    )
    if result1.stdout:
        print(result1.stdout)
    if result1.stderr:
        print(result1.stderr)

    if result1.returncode != 0:
        print(f"❌ 步骤1失败：{input_md}")
        return False

    json_filename = extract_json_filename(result1.stdout)
    if not json_filename:
        json_filename = f"{src_stem}-segment.json"
        print(f"⚠️ 无法从输出提取 JSON 名，使用 fallback：{json_filename}")

    seg_json_path = seg_dir / json_filename
    pretty_filename = json_filename.replace('-segment.json', '-segment_pretty.json')
    seg_pretty_path = seg_dir / pretty_filename

    # 优先用已有 JSON，避免重复切分
    if seg_json_path.exists():
        print(f"    ℹ️ JSON 已存在：{seg_json_path.relative_to(WORKDIR)}，跳过切分")
    else:
        json_path = WORKDIR / json_filename
        if json_path.exists():
            if seg_json_path.exists():
                seg_json_path.unlink()
            json_path.rename(seg_json_path)
            print(f"✅ 步骤1完成，JSON：{seg_json_path.relative_to(WORKDIR)}\n")
        else:
            print(f"❌ JSON 文件不存在：{json_path}")
            return False

    # 移动 pretty 版本
    pretty_path = WORKDIR / pretty_filename
    if pretty_path.exists():
        if seg_pretty_path.exists():
            seg_pretty_path.unlink()
        pretty_path.rename(seg_pretty_path)

    # ========== 步骤2：二次加工 ==========
    if not dry_run:
        print(f"[步骤2] 调用 reprocess_original.py 二次加工...")
        reprocess_args = [
            "--input-md", str(input_md),
            "--input-json", str(seg_pretty_path),
            "--output-dir", str(out_dir),
            "--batch-size", str(batch_size),
        ]
        result2 = subprocess.run(
            [PYTHON, str(WORKDIR / "reprocess_original.py")] + reprocess_args,
            cwd=str(WORKDIR), encoding='utf-8'
        )
        if result2.returncode != 0:
            print(f"❌ 步骤2失败：{input_md}（JSON 已保存，可单独重跑）")
            return False
        print(f"✅ 步骤2完成，文档：{out_dir.relative_to(WORKDIR)}\n")
    else:
        print(f"[步骤2] Dry run，跳过 reprocess_original.py\n")

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="高等数学教材自动化流水线：切分 → 二次加工",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例：\n"
            "  %(prog)s -i \"高等数学改/第一章/二、函数的概念.md\"\n"
            "  %(prog)s -i \"高等数学改/第一章/第一节\"\n"
            "  %(prog)s -i \"高等数学改/\"  (批量处理整本教材)\n"
            "  %(prog)s --dry-run                (只生成提示词)\n"
            "  %(prog)s --batch-size 3           (每批处理3个segment)\n"
        )
    )
    parser.add_argument("--input", "-i", default=None,
                        help="输入 .md 文件或目录（必填）")
    parser.add_argument("--output-root", "-o", default=None,
                        help="最终文档输出根目录（默认：processed_output/源文件/）")
    parser.add_argument("--segments-dir", "-s", default=None,
                        help="中间 JSON 目录（默认：segments_output/）")
    parser.add_argument("--batch-size", "-b", type=int, default=BATCH_SIZE,
                        help="每批处理的 segment 数量 (默认: %d)" % BATCH_SIZE)
    parser.add_argument("--dry-run", action="store_true",
                        help="只生成提示词，不调用 LLM API")
    args = parser.parse_args()

    # 输出目录配置
    if args.output_root:
        global OUTPUT_ROOT
        OUTPUT_ROOT = Path(args.output_root)
    if args.segments_dir:
        global SEGMENTS_DIR
        SEGMENTS_DIR = Path(args.segments_dir)

    # 查找要处理的文件
    if args.input:
        files = find_markdown_files(args.input)
        if not files:
            print(f"❌ 未找到 .md 文件：{args.input}")
            sys.exit(1)
    else:
        print("❌ 请使用 -i 参数指定输入文件或目录")
        sys.exit(1)

    total = len(files)
    success = 0
    failed = []

    print(f"\n{'=' * 60}")
    print(f"📋 流水线概览")
    print(f"{'=' * 60}")
    print(f"  待处理文件：{total} 个")
    print(f"  中间 JSON 目录：{SEGMENTS_DIR}")
    print(f"  最终输出目录：{OUTPUT_ROOT}/{{源文件名}}/")
    print(f"  批大小：{args.batch_size} 条/批")
    print(f"  Dry Run：{'是' if args.dry_run else '否'}")
    print(f"{'=' * 60}\n")

    for i, f in enumerate(files, 1):
        print(f"\n{'=' * 60}")
        print(f"▶️ [{i}/{total}] {f.relative_to(WORKDIR)}")
        ok = process_single_file(f, dry_run=args.dry_run, batch_size=args.batch_size)
        if ok:
            success += 1
        else:
            failed.append(str(f))
        if i < total:
            print("    ⏳ 等待 3s 后继续下一个文件...")
            time.sleep(3)

    # 汇总
    print(f"\n{'=' * 60}")
    print(f"📊 流水线执行完毕")
    print(f"{'=' * 60}")
    print(f"  成功：{success}/{total}")
    if failed:
        print(f"  失败：{len(failed)} 个")
        for f in failed:
            print(f"    - {f}")
    else:
        print(f"  失败：0 个")
    print(f"  中间 JSON：{SEGMENTS_DIR}")
    print(f"  最终文档：{OUTPUT_ROOT}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
