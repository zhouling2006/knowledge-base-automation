#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二次加工原文程序
将原始教材片段 + 结构化信息转换成多个独立 Markdown 知识文档

用法：
  python reprocess_original.py --input-md "二、函数的概念.md" --input-json segments_output.json
  python reprocess_original.py --dry-run              # 只生成提示词，不调用API
  python reprocess_original.py --batch-size 5         # 每批5个segment
  python reprocess_original.py --output-dir ./output   # 指定输出目录
"""

import sys
import io
import json
import os
import re
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

# ==================== 配置区 ====================

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not DASHSCOPE_API_KEY:
    raise ValueError("请设置环境变量 DASHSCOPE_API_KEY（在 .env 中或系统环境变量）")

MODEL = os.environ.get("LLM_MODEL", "qwen-plus")

DEFAULT_INPUT_MD = "二、函数的概念.md"
DEFAULT_INPUT_JSON = "segments_output.json"
DEFAULT_SPEC_FILE = r"E:\Downloads\markdown-hack规范.md"
DEFAULT_SAMPLES_DIR = r"F:\schem\samples"
DEFAULT_OUTPUT_DIR = "processed_output"

SPLIT_SEPARATOR = "---SPLIT---"

# ==================== 配置区结束 ====================


def read_file(filepath: str) -> str:
    """读取文本文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def read_samples(samples_dir: str) -> list[tuple[str, str]]:
    """读取 samples 目录下的 .md 示例文件，返回 [(name, content), ...]"""
    p = Path(samples_dir)
    if not p.exists():
        print(f"⚠️ 示例目录不存在：{samples_dir}")
        return []
    samples = sorted(p.glob("*.md"))
    result = []
    for f in samples:
        try:
            content = read_file(str(f))
            result.append((f.stem, content))
            print(f"  📄 已加载示例：{f.name}")
        except Exception as e:
            print(f"⚠️ 无法读取示例 {f}: {e}")
    return result


# =============================================================================
# 提示词模板（来自用户提供）
# =============================================================================

SYSTEM_PROMPT = """你是一个专业的数学文档转换助手。用户会提供两类输入：
1. 原始教材的 Markdown 文本，其中包含定义、例子、图示、表格等内容。
2. 对应的结构化摘要文件，其中将原文切分成多个逻辑块（每个块包含 title, content, type, aliases, entities, references 等字段）。

你的任务是基于这两部分输入，生成 **一组独立的 Markdown 文件**，每个文件对应一个逻辑块（例如"函数的定义.md"、"例1.1.5.md"等）。**每个文件之间用单独一行 ---SPLIT--- 分隔**。


## 输出要求

1. **每个文件都是一个完整的 Markdown 文档**，必须包含：
   - 顶部的 frontmatter（YAML 格式），至少包含 `title`, `aliases`（数组）, `tags`（数组）。其他可选字段（description, author 等）根据需要添加。
   - 正文：以一级标题 `# 标题` 开始。
   - 正文中可包含：文字说明、公式、列表、表格、图片（图片路径保持原样或按规范调整到 `./assets/`）、**语义块（Pandoc fenced div）** 等。

2. **引用关系**：
   - 在不同文件之间添加合理的双向引用。例如在"函数的定义"中引用"多值函数与单值分支"，在例子中引用相关的概念。
   - 引用格式遵循 [[目标文件名]]{type=..., label=..., render=link, tags=...} 的扩展语法（参考 markdown-hack规范.md）。
   - 对于证明、推导、注释等内容，使用 ::: {#块ID .proof label="..." type=proof} ... ::: 块包裹，并赋予 #块ID、label、type 等属性。

3. **图片处理**：
   - 原文档中的图片（通常有图注，如"图1.1.6"）应放在对应描述文字的下方，而不是堆在文件末尾。
   - 图片链接原样保留（可使用原始 URL 或改为相对路径 ./assets/xxx.png，若未提供本地文件则保留 URL）。

4. **内容组织**：
   - 尽量保留原文的关键信息，但可以重新组织语言，使其更清晰、更符合独立文档的阅读习惯。
   - 从结构化数据中提取 title、content、aliases、entities、summary 等作为创作素材，但不要机械复制 JSON，要写成自然连贯的 Markdown。
   - 对于 "example" 类型的块，建议用 ::: {.example label="..." type=example} ... ::: 包裹。
   - 对于 "concept" 类型的块，可以用普通段落 + ::: {.note} 作为补充说明。

5. **输出格式**：
   - 所有生成的 Markdown 文件依次输出，**每个文件之间用单独一行 ---SPLIT--- 分隔**。
   - 不要在文件内部出现 ---SPLIT---。
   - 第一个文件之前不要加分隔符，最后一个文件之后不要加分隔符。


## 注意事项

- 不要改变原文中数学公式的 LaTeX 表示（包括行内 $...$ 和行间 $$...$$）。
- 如果原文档中有图片链接，直接保留；若图片有图注（如"图1.1.6"），将其作为 ![图注](url) 的 alt 文本。
- 每个文档应自包含，但通过 [[...]]{...} 引用其他文档形成知识网络。
- 输出的文档数量应与本次输入的逻辑块数量一致（或略有合并，优先拆分）。
- 严格遵守 ---SPLIT--- 分隔格式，以便后期脚本拆分。"""


def build_user_prompt(
    src_md: str,
    segments_batch: list[dict],
    spec_content: str,
    samples: list[tuple[str, str]],
    start_idx: int,
) -> str:
    """
    构建 user prompt，包含规范 + 示例 + 输入数据
    """
    # 组装示例部分
    examples_parts = []
    for name, content in samples:
        examples_parts.append(
            f"### 示例文档：{name}\n\n"
            f"```markdown\n{content}\n```"
        )
    examples_text = "\n\n".join(examples_parts)

    # 组装 segments JSON（只传关键字段，减少token消耗）
    compact_segments = []
    for seg in segments_batch:
        compact_segments.append({
            "title": seg.get("title", ""),
            "content": seg.get("content", ""),
            "raw_content": seg.get("raw_content", ""),
            "type": seg.get("type", ""),
            "aliases": seg.get("aliases", []),
            "entities": seg.get("entities", ""),
            "references": seg.get("references", []),
            "summary": seg.get("summary", ""),
        })
    segments_json_text = json.dumps(compact_segments, ensure_ascii=False, indent=2)

    user_prompt = (
        "# 任务：将数学教材内容转换为多个独立的 Markdown 知识文档\n\n"
        "请严格按照以下规范和要求生成。\n\n"
        f"---\n\n"
        f"## 参考规范（markdown-hack规范）\n\n"
        f"```\n{spec_content}```\n\n"
        f"---\n\n"
        f"## 参考示例文档\n\n"
        f"以下是可以参考的示例文档的结构和写法：\n\n"
        f"{examples_text}\n\n"
        f"---\n\n"
        f"## 原始教材内容\n\n"
        f"```markdown\n{src_md}\n```\n\n"
        f"---\n\n"
        f"## 本次需要转换的结构化数据 "
        f"(segments_output.json 的第 {start_idx}~{start_idx + len(segments_batch) - 1} 条)\n\n"
        f"```json\n{segments_json_text}\n```\n\n"
        f"\n请按照上述规范和要求，为以上每条结构化数据生成对应的 Markdown 文档，"
        f"用 {SPLIT_SEPARATOR} 分隔。\n"
    )
    return user_prompt


# =============================================================================
# LLM 调用
# =============================================================================

def call_llm(system_prompt: str, user_prompt: str,
              max_retries: int = 3) -> str:
    """调用 DashScope API（OpenAI 兼容接口）"""
    client = OpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    for attempt in range(1, max_retries + 1):
        try:
            print(f"  🔄 正在调用 LLM ({MODEL})，第 {attempt}/{max_retries} 次...")
            start_time = time.time()

            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=16000,
            )

            elapsed = time.time() - start_time
            content = response.choices[0].message.content
            usage = response.usage

            print(f"  ✅ LLM 返回完成")
            print(f"     字符数：{len(content)} | tokens：input={usage.prompt_tokens}, output={usage.completion_tokens}")
            print(f"     耗时：{elapsed:.1f}s")

            # 统计 token 用量
            if usage.total_tokens > 0:
                cost_estimate = (usage.prompt_tokens * 0.0004 + usage.completion_tokens * 0.002) / 1000
                print(f"     预估费用：¥{cost_estimate:.3f}")

            return content

        except Exception as e:
            error_type = type(e).__name__
            wait_time = min(30 * attempt, 120)
            print(f"  ⚠️ {error_type}: {e}")
            if attempt < max_retries:
                print(f"     等待 {wait_time}s 后重试...")
                time.sleep(wait_time)
            else:
                print(f"  ❌ 重试 {max_retries} 次均失败")
                raise


# =============================================================================
# 输出解析与保存
# =============================================================================

def parse_output(output_text: str) -> list[str]:
    """
    解析 LLM 输出，按 ---SPLIT--- 分割成多个文档。
    支持大小写不敏感匹配。
    """
    # 使用正则分割，匹配单独一行的分隔符
    parts = re.split(
        r'\n?^---\s*SPLIT\s*---\s*$\n?',
        output_text,
        flags=re.MULTILINE | re.IGNORECASE
    )

    # 过滤空字符串
    result = []
    for p in parts:
        stripped = p.strip()
        if stripped:
            result.append(stripped)

    return result


def extract_title_from_frontmatter(md_text: str) -> Optional[str]:
    """从 frontmatter 中提取 title"""
    fm_match = re.search(r'^---\s*\n(.*?)\n---', md_text, re.DOTALL)
    if fm_match:
        title_match = re.search(r'^title:\s*(.+)$', fm_match.group(1), re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
    return None


def sanitize_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    name = name.strip()
    # 替换中文冒号/括号等
    name = name.replace('：', '-').replace('，', ',')
    name = name.replace('（', '(').replace('）', ')')
    # 移除 Windows 非法字符
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    name = name.replace(' ', '-')
    # 截断过长的名称
    if len(name) > 60:
        name = name[:57] + '...'
    return name or 'untitled'


def save_outputs(parts: list[str], output_dir: str,
                 batch_prefix: str = "") -> list[str]:
    """
    保存每个部分到独立文件。
    返回保存的文件路径列表。
    """
    os.makedirs(output_dir, exist_ok=True)
    saved_files = []

    for i, part in enumerate(parts):
        # 尝试从 frontmatter 提取标题
        title = extract_title_from_frontmatter(part)
        if not title:
            title = f'part_{i + 1}'

        safe_name = sanitize_filename(title)
        filename = f"{batch_prefix}{i + 1:02d}_{safe_name}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(part)

        saved_files.append(filepath)
        print(f"    ✅ 已保存：{filename}")

    return saved_files


# =============================================================================
# 主处理流程
# =============================================================================

def process_all(
    src_md: str,
    segments: list[dict],
    spec_content: str,
    samples: list[tuple[str, str]],
    output_dir: str,
    dry_run: bool = False,
    batch_size: int = 6,
):
    """
    完整的处理流程：
    1. 按 batch_size 分批
    2. 每批调用 LLM
    3. 解析输出并保存为独立文件
    """
    total_segments = len(segments)
    total_batches = (total_segments + batch_size - 1) // batch_size

    print(f"\n{'=' * 60}")
    print(f"📊 二次加工任务概览")
    print(f"{'=' * 60}")
    print(f"  总 segment 数：{total_segments}")
    print(f"  批次大小：{batch_size} 条/批")
    print(f"  总批次数：{total_batches}")
    print(f"  输出目录：{output_dir}")
    print(f"  Dry Run：{'是' if dry_run else '否'}")
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    print(f"{'=' * 60}\n")

    all_saved_files = []

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_segments)
        batch = segments[start_idx:end_idx]
        batch_label = f"batch{batch_num + 1:02d}"

        print(f"\n▶️ 第 {batch_num + 1}/{total_batches} 批：segment [{start_idx + 1} ~ {end_idx}]，共 {len(batch)} 条")
        print(f"{'-' * 50}")

        # 构建 prompt
        user_prompt = build_user_prompt(
            src_md, batch, spec_content, samples,
            start_idx=start_idx + 1  # 1-indexed for display
        )

        # 如果是 dry run，只保存 prompt 不调用 API
        if dry_run:
            debug_file = os.path.join(output_dir, f"_debug_{batch_label}_prompt.txt")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write("=== SYSTEM PROMPT ===\n\n")
                f.write(SYSTEM_PROMPT)
                f.write("\n\n=== USER PROMPT ===\n\n")
                f.write(user_prompt)
            print(f"  💾 Dry run：prompt 已保存到 {debug_file}")
            continue

        # 调用 LLM
        output_text = call_llm(SYSTEM_PROMPT, user_prompt)

        # 保存原始响应（调试用）
        raw_file = os.path.join(output_dir, f"_debug_{batch_label}_raw.txt")
        with open(raw_file, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"    💾 原始响应已保存到 _debug_{batch_label}_raw.txt")

        # 解析输出
        parts = parse_output(output_text)
        expected_count = len(batch)
        actual_count = len(parts)

        print(f"    📋 解析结果：预期 {expected_count} 个文档，实际得到 {actual_count} 个")

        if actual_count != expected_count:
            print(f"    ⚠️ 数量不匹配！可能是 LLM 输出格式异常")

        # 保存文件
        saved = save_outputs(parts, output_dir, batch_prefix=f"{batch_label}-")
        all_saved_files.extend(saved)

        # 批次间隔，避免速率限制
        if batch_num < total_batches - 1 and not dry_run:
            print("\n    ⏳ 等待 2s 后继续下一批...")
            time.sleep(2)

    # 生成汇总报告
    report_path = os.path.join(output_dir, "_report.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"# 二次加工报告\n\n")
        f.write(f"- 时间：{now}\n")
        f.write(f"- 输入文件：{DEFAULT_INPUT_MD} + {DEFAULT_INPUT_JSON}\n")
        f.write(f"- Segment 总数：{total_segments}\n")
        f.write(f"- 批次数：{total_batches}（每批 {batch_size} 条）\n")
        f.write(f"- 生成的文档数量：{len(all_saved_files)}\n")
        f.write(f"- 模型：{MODEL}\n\n")
        f.write("## 生成文件列表\n\n")
        for fp in all_saved_files:
            fname = os.path.basename(fp)
            f.write(f"- `{fname}`\n")

    print(f"\n{'=' * 60}")
    print(f"✅ 全部完成！共生成 {len(all_saved_files)} 个文档")
    print(f"   报告文件：{report_path}")
    print(f"   输出目录：{os.path.abspath(output_dir)}")
    print(f"{'=' * 60}")

    return all_saved_files


# =============================================================================
# 命令行入口
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="二次加工原文程序 — 将原始教材片段转换为符合 markdown-hack 规范的独立 Markdown 文档",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  %(prog)s                                          # 使用默认参数运行
  %(prog)s --dry-run                                # 只生成提示词，不调用API
  %(prog)s --batch-size 4                           # 每批处理4个segment
  %(prog)s --input-md "第一章/1.1 函数.md"           # 指定输入文件
  %(prog)s --output-dir ./my_output                 # 指定输出目录
  %(prog)s --spec-file "规范/markdown-hack规范.md"  # 指定规范文件
"""
    )
    parser.add_argument("--input-md", "-m", default=DEFAULT_INPUT_MD,
                        help="原始教材 Markdown 文件路径 (默认: %s)" % DEFAULT_INPUT_MD)
    parser.add_argument("--input-json", "-j", default=DEFAULT_INPUT_JSON,
                        help="结构化数据 JSON 文件路径 (默认: %s)" % DEFAULT_INPUT_JSON)
    parser.add_argument("--spec-file", "-s", default=DEFAULT_SPEC_FILE,
                        help="markdown-hack 规范文件路径")
    parser.add_argument("--samples-dir", default=DEFAULT_SAMPLES_DIR,
                        help="参考示例目录 (默认: %s)" % DEFAULT_SAMPLES_DIR)
    parser.add_argument("--output-dir", "-o", default=DEFAULT_OUTPUT_DIR,
                        help="输出目录 (默认: %s)" % DEFAULT_OUTPUT_DIR)
    parser.add_argument("--batch-size", "-b", type=int, default=6,
                        help="每批处理的 segment 数量 (默认: 6)")
    parser.add_argument("--dry-run", action="store_true",
                        help="只生成提示词文件，不调用 LLM API")
    args = parser.parse_args()

    # 加载所有输入
    print("📖 加载输入文件...")

    src_md = read_file(args.input_md)
    print(f"  ✅ 原始教材：{args.input_md} ({len(src_md)} 字符)")

    segments = json.loads(read_file(args.input_json))
    print(f"  ✅ 结构化数据：{args.input_json} ({len(segments)} 条 segment)")

    spec_content = read_file(args.spec_file)
    print(f"  ✅ 规范文件：{args.spec_file} ({len(spec_content)} 字符)")

    samples = read_samples(args.samples_dir)
    print(f"  ✅ 参考示例：加载了 {len(samples)} 个示例文档\n")

    # 开始处理
    all_files = process_all(
        src_md=src_md,
        segments=segments,
        spec_content=spec_content,
        samples=samples,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )


if __name__ == "__main__":
    main()
