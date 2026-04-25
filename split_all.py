#!/usr/bin/env python3
"""
Markdown 多级拆分工具
"""

import re
import os
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ==================== 配置区（改这里） ====================
INPUT_PATH = "全文_标准化.md"
OUTPUT_DIR = "高等数学（上）"
# ==================== 配置区结束 ====================


def sanitize_filename(name):
    """清理文件名，移除非法字符"""
    illegal_chars = r'[<>:"/\\|?*]'
    name = re.sub(illegal_chars, '_', name)
    return name.strip('. ')


# ==================== 一级拆分 ====================
def split_level1(input_path, output_dir):
    """一级拆分：提取目录 + 按一级标题拆分"""
    print(f"\n{'='*50}")
    print(f"一级拆分: {input_path} -> {output_dir}")
    print(f"{'='*50}")

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = re.compile(r'^#\s+第一章', re.MULTILINE)
    matches = list(pattern.finditer(content))

    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    if len(matches) >= 2:
        # 有目录：第二次 # 第一章 之前为目录，之后为正文
        second_chapter_start = matches[1].start()
        dir_content = content[:second_chapter_start].strip()
        main_content = content[second_chapter_start:].strip()

        dir_file = out / "目录.md"
        with open(dir_file, 'w', encoding='utf-8') as f:
            f.write(dir_content)
        print(f"✅ 目录: {dir_file}")
    elif len(matches) >= 1:
        # 无目录：整个文件作为正文
        main_content = content.strip()
        print("⚠️ 未找到目录，直接拆分正文")
    else:
        print("❌ 未找到 # 第一章，无法拆分")
        return False

    chapters = re.split(r'(?=^#\s)', main_content, flags=re.MULTILINE)
    for chap in chapters:
        chap = chap.strip()
        if not chap:
            continue
        first_line = chap.split('\n')[0].strip()
        if first_line.startswith("# "):
            title = first_line[2:].strip()
            filename = sanitize_filename(f"{title}_标准化.md")
            with open(out / filename, 'w', encoding='utf-8') as f:
                f.write(chap)
            print(f"✅ {filename}")

    print(f"\n🎉 一级拆分完成: {output_dir}/")
    return True


# ==================== 二级拆分 ====================
def split_by_h2(content):
    """按二级标题拆分"""
    sections = re.split(r'(?=^##\s+)', content, flags=re.MULTILINE)
    result = []
    for section in sections:
        if not section.strip():
            continue
        lines = section.split('\n')
        first_line = lines[0]
        title_match = re.match(r'^##\s+(.+)$', first_line)
        if title_match:
            title = title_match.group(1).strip()
            section = re.sub(r'^##\s+', '# ', section, count=1)
            result.append((title, section))
    return result


def split_level2(input_dir, output_dir):
    """二级拆分：按二级标题拆分成独立文件"""
    print(f"\n{'='*50}")
    print(f"二级拆分: {input_dir} -> {output_dir}")
    print(f"{'='*50}")

    if not os.path.exists(input_dir):
        print(f"❌ 目录不存在: {input_dir}")
        return False

    processed = 0
    for filename in os.listdir(input_dir):
        if filename.endswith(".md") and "_标准化" in filename:
            file_path = os.path.join(input_dir, filename)
            print(f"\n--- {filename} ---")

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            chapter_name = Path(filename).stem.replace('_标准化', '')
            main_folder = Path(output_dir) / chapter_name
            main_folder.mkdir(parents=True, exist_ok=True)

            source_file = main_folder / f"{chapter_name}_源文件.md"
            with open(source_file, 'w', encoding='utf-8') as f:
                f.write(content)

            sections = split_by_h2(content)
            print(f"  找到 {len(sections)} 个大节")

            for title, section_content in sections:
                folder_name = sanitize_filename(title)
                file_name = folder_name + ".md"
                section_folder = main_folder / folder_name
                section_folder.mkdir(parents=True, exist_ok=True)
                with open(section_folder / file_name, 'w', encoding='utf-8') as f:
                    f.write(section_content)
                print(f"  📄 {folder_name}/{file_name}")

            processed += 1

    if processed > 0:
        print(f"\n🎉 二级拆分完成: {processed} 个文件")
    else:
        print("⚠️ 未找到任何 _标准化.md 文件")
    return True


# ==================== 三级拆分 ====================
def split_md_by_h3(file_path):
    """按三级标题拆分单个文件"""
    if not file_path.exists():
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    sections = re.split(r'(?=^###\s+)', content, flags=re.MULTILINE)
    sections = [s for s in sections if s.strip()]

    if len(sections) <= 1:
        return []

    generated = []
    for section in sections:
        lines = section.split('\n')
        first_line = lines[0]
        h3_match = re.match(r'^###\s+(.+)$', first_line)

        if h3_match:
            title = h3_match.group(1).strip()
            filename = sanitize_filename(title) + ".md"
            output_path = file_path.parent / filename
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(section)
            generated.append(filename)

    return generated


def split_level3(input_dir):
    """三级拆分：按三级标题拆分成小节文件"""
    print(f"\n{'='*50}")
    print(f"三级拆分: {input_dir}")
    print(f"{'='*50}")

    if not os.path.exists(input_dir):
        print(f"❌ 目录不存在: {input_dir}")
        return False

    chapters = [d for d in Path(input_dir).iterdir() if d.is_dir()]
    if not chapters:
        print("⚠️ 未找到章节文件夹")
        return False

    total_files = 0
    for chapter in chapters:
        print(f"\n📁 {chapter.name}")
        subfolders = [d for d in chapter.iterdir() if d.is_dir()]
        for subfolder in subfolders:
            md_files = list(subfolder.glob("*.md"))
            for md_file in md_files:
                files = split_md_by_h3(md_file)
                for f in files:
                    print(f"  ✅ {f}")
                total_files += len(files)

    if total_files > 0:
        print(f"\n🎉 三级拆分完成: 生成 {total_files} 个文件")
    else:
        print("⚠️ 未找到可拆分的小节")
    return True


def main():
    print(f"\n{'='*50}")
    print(f"Markdown 多级拆分")
    print(f"  输入: {INPUT_PATH}")
    print(f"  输出: {OUTPUT_DIR}")
    print(f"{'='*50}")

    step1_out = OUTPUT_DIR + "_temp"
    split_level1(INPUT_PATH, step1_out)
    split_level2(step1_out, OUTPUT_DIR)
    split_level3(OUTPUT_DIR)

    import shutil
    if os.path.exists(step1_out):
        shutil.rmtree(step1_out)

    print(f"\n{'='*50}")
    print(f"🎉 全部完成！输出: {OUTPUT_DIR}/")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
