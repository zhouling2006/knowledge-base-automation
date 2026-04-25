#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sqlite3
import os

# ========== 可修改变量 ==========
BOOK_TITLE = "高等数学（上）"
JSON_PATH = os.path.join(os.path.dirname(__file__), "chapter_structure.json")
DB_PATH = os.path.join(os.path.dirname(__file__), "chapters.db")
# ================================


def get_title(item):
    return item.get("标题") or item.get("title") or ""


def fix_json_backslashes(text):
    """
    逐字符扫描 JSON 文本，只对字符串值内部的单独反斜杠
    （即后面跟的不是合法 JSON 转义字符的那种）补全为双反斜杠。
    已经是 \\\\ 的不再处理。
    """
    VALID_ESCAPES = set('"' + '\\' + '/' + 'bfnrtu')
    result = []
    in_string = False
    i = 0
    while i < len(text):
        ch = text[i]
        if not in_string:
            result.append(ch)
            if ch == '"':
                in_string = True
            i += 1
        else:
            if ch == '\\':
                next_ch = text[i + 1] if i + 1 < len(text) else ''
                if next_ch in VALID_ESCAPES:
                    # 合法转义，原样保留两个字符
                    result.append(ch)
                    result.append(next_ch)
                    i += 2
                else:
                    # 非法反斜杠，补成双反斜杠
                    result.append('\\\\')
                    i += 1
            elif ch == '"':
                result.append(ch)
                in_string = False
                i += 1
            else:
                result.append(ch)
                i += 1
    return ''.join(result)


def build_chapters_db():
    import re

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        raw = f.read()

    # 只截取 "chapters": [...] 数组部分，跳过 structure_summary（含正则字符串，干扰修复）
    m = re.search(r'"chapters"\s*:\s*(\[.*\])', raw, re.DOTALL)
    if not m:
        raise ValueError("未找到 chapters 字段")
    chapters_raw = m.group(1)

    chapters_fixed = fix_json_backslashes(chapters_raw)
    chapters = json.loads(chapters_fixed)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS chapters")
    cursor.execute("""
        CREATE TABLE chapters (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            level     INTEGER NOT NULL,
            number    TEXT,
            title     TEXT,
            parent_id INTEGER REFERENCES chapters(id)
        )
    """)

    # 插入根节点（书名）
    cursor.execute(
        "INSERT INTO chapters (level, number, title, parent_id) VALUES (?, ?, ?, ?)",
        (0, None, BOOK_TITLE, None)
    )
    root_id = cursor.lastrowid

    # 第一遍：为每个条目分配 id，记录 (编号, level, 索引位置) -> row_id
    # 因为 "第一节" 在每章下都会重复出现，所以父子关系必须按顺序上下文推断
    # 策略：维护一个"当前各层级最近节点"的栈
    # level_stack[level] = (编号, id)
    level_stack = {0: (BOOK_TITLE, root_id)}

    for item in chapters:
        level = item.get("level")
        number = item.get("编号", "")
        title = get_title(item)
        parent_number = item.get("父级编号")

        # 确定 parent_id
        if parent_number is None:
            # 无父级编号 -> 挂到根节点
            parent_id = root_id
        else:
            # 在已有的上下文栈中从 (level-1) 往上找最近匹配的编号
            parent_id = None
            for lv in range(level - 1, -1, -1):
                if lv in level_stack and level_stack[lv][0] == parent_number:
                    parent_id = level_stack[lv][1]
                    break
            if parent_id is None:
                # 找不到匹配编号，挂到上一层级的最近节点
                for lv in range(level - 1, -1, -1):
                    if lv in level_stack:
                        parent_id = level_stack[lv][1]
                        break
            if parent_id is None:
                parent_id = root_id

        cursor.execute(
            "INSERT INTO chapters (level, number, title, parent_id) VALUES (?, ?, ?, ?)",
            (level, number, title, parent_id)
        )
        new_id = cursor.lastrowid

        # 更新当前层级的最近节点
        level_stack[level] = (number, new_id)

        # 插入新节点后，清除所有比当前层级更深的缓存（防止跨章节错误继承）
        for lv in list(level_stack.keys()):
            if lv > level:
                del level_stack[lv]

    conn.commit()

    # 打印验证信息
    cursor.execute("SELECT COUNT(*) FROM chapters")
    total = cursor.fetchone()[0]
    print(f"数据库已创建：{DB_PATH}")
    print(f"总条目数（含根节点）：{total}")

    print("\n前 20 条记录预览：")
    cursor.execute("SELECT id, level, number, title, parent_id FROM chapters LIMIT 20")
    rows = cursor.fetchall()
    print(f"{'id':>4}  {'level':>5}  {'number':<12}  {'title':<30}  {'parent_id'}")
    print("-" * 75)
    for row in rows:
        print(f"{row[0]:>4}  {row[1]:>5}  {str(row[2] or ''):<12}  {str(row[3] or ''):<30}  {row[4]}")

    conn.close()


if __name__ == "__main__":
    build_chapters_db()
