#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准概念库查询脚本
- 查询概念
- 查询别名/实体名词
- 语义搜索
"""

import sys
import io
import os
import sqlite3
import numpy as np
from pathlib import Path
import ssl
import warnings
warnings.filterwarnings('ignore')

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_DISABLE_SSL_VERIFICATION'] = '1'
ssl._create_default_https_context = ssl._create_unverified_context

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

DB_PATH = "concept_base.db"
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"
TOP_K = 5

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    print("❌ 请先安装: pip install sentence-transformers")
    exit(1)


def load_model():
    print(f"🤖 加载模型: {EMBEDDING_MODEL}")
    return SentenceTransformer(EMBEDDING_MODEL)


def print_concepts(cursor):
    print("\n" + "=" * 60)
    print("所有概念")
    print("=" * 60)
    cursor.execute("SELECT concept_id, name, concept_type, file_path FROM concepts ORDER BY concept_id")
    for row in cursor.fetchall():
        print(f"  [{row[0]}] {row[1]} ({row[2]}) - {row[3]}")


def print_aliases(cursor, filter_status=None):
    print("\n" + "=" * 60)
    status_text = filter_status if filter_status else "所有"
    print(f"别名/实体（{status_text}）")
    print("=" * 60)
    
    if filter_status:
        cursor.execute("""
            SELECT a.alias, a.alias_type, a.concept_id, c.name, a.confidence, a.status
            FROM aliases a
            LEFT JOIN concepts c ON a.concept_id = c.concept_id
            WHERE a.status = ?
            ORDER BY a.alias
        """, (filter_status,))
    else:
        cursor.execute("""
            SELECT a.alias, a.alias_type, a.concept_id, c.name, a.confidence, a.status
            FROM aliases a
            LEFT JOIN concepts c ON a.concept_id = c.concept_id
            ORDER BY a.alias
        """)
    
    for row in cursor.fetchall():
        alias, alias_type, concept_id, concept_name, confidence, status = row
        status_icon = {'auto_mapped': '✓', 'llm_confirmed': '✓', 'needs_review': '?', 'unmapped': '✗', 'pending': '○'}
        icon = status_icon.get(status, '?')
        concept_str = f"→ [{concept_id}] {concept_name}" if concept_id else "→ (无匹配)"
        print(f"  {icon} '{alias}' ({alias_type}) {concept_str} [{status}] conf={confidence:.3f}")


def print_needs_review(cursor):
    print("\n" + "=" * 60)
    print("待人工审核")
    print("=" * 60)
    cursor.execute("""
        SELECT a.alias, a.alias_type, a.concept_id, c.name, a.confidence, a.llm_reason
        FROM aliases a
        LEFT JOIN concepts c ON a.concept_id = c.concept_id
        WHERE a.status = 'needs_review'
        ORDER BY a.confidence DESC
    """)
    
    rows = cursor.fetchall()
    if not rows:
        print("  ✓ 没有待审核项")
        return
    
    for row in rows:
        alias, alias_type, concept_id, concept_name, confidence, reason = row
        concept_str = f"[{concept_id}] {concept_name}" if concept_id else "无匹配"
        print(f"\n  别名: {alias}")
        print(f"  类型: {alias_type}")
        print(f"  推荐概念: {concept_str}")
        print(f"  置信度: {confidence:.3f}")
        print(f"  原因: {reason}")


def search_by_text(query, cursor, model, top_k=TOP_K):
    print("\n" + "=" * 60)
    print(f"语义搜索: {query}")
    print("=" * 60)

    query_embedding = model.encode(query)

    cursor.execute("SELECT concept_id, name, content, embedding FROM concepts")
    concepts = cursor.fetchall()

    results = []
    for concept_id, name, content, embedding_blob in concepts:
        embedding = np.frombuffer(embedding_blob, dtype=np.float32)
        similarity = util.cos_sim(query_embedding, embedding).item()
        results.append({
            'concept_id': concept_id,
            'name': name,
            'content': content[:200] + '...' if content and len(content) > 200 else content,
            'similarity': similarity
        })

    results.sort(key=lambda x: x['similarity'], reverse=True)

    for i, r in enumerate(results[:top_k], 1):
        print(f"\n[{i}] {r['name']}")
        print(f"    ID: {r['concept_id']} | 相似度: {r['similarity']:.4f}")
        print(f"    内容: {r['content']}")


def search_alias(query, cursor, model):
    print("\n" + "=" * 60)
    print(f"别名/实体搜索: {query}")
    print("=" * 60)

    query_lower = query.lower()
    cursor.execute("""
        SELECT a.alias, a.alias_type, a.concept_id, c.name, a.confidence, a.status
        FROM aliases a
        LEFT JOIN concepts c ON a.concept_id = c.concept_id
        WHERE LOWER(a.alias) LIKE ?
        ORDER BY a.confidence DESC
    """, (f'%{query_lower}%',))

    rows = cursor.fetchall()
    if not rows:
        print(f"  未找到包含 '{query}' 的别名/实体")
        return

    for row in rows:
        alias, alias_type, concept_id, concept_name, confidence, status = row
        concept_str = f"→ [{concept_id}] {concept_name}" if concept_id else "→ (无匹配)"
        print(f"  '{alias}' ({alias_type}) {concept_str} conf={confidence:.3f}")


def manual_assign(alias, concept_id, cursor):
    cursor.execute("SELECT concept_id, name FROM concepts WHERE concept_id = ?", (concept_id,))
    concept = cursor.fetchone()
    if not concept:
        print(f"❌ 概念 [{concept_id}] 不存在")
        return False

    cursor.execute("""
        UPDATE aliases SET concept_id = ?, status = 'llm_confirmed', llm_reason = '人工指定'
        WHERE alias = ?
    """, (concept_id, alias))
    
    if cursor.rowcount == 0:
        print(f"❌ 别名 '{alias}' 不存在")
        return False

    print(f"✓ 已将 '{alias}' 关联到 [{concept_id}] {concept[1]}")
    return True


def main():
    print("=" * 60)
    print("标准概念库查询")
    print("=" * 60)

    if not Path(DB_PATH).exists():
        print(f"❌ 数据库不存在: {DB_PATH}")
        print("   请先运行 build_concept_db.py 构建概念库")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    model = load_model()

    while True:
        print("\n" + "-" * 40)
        print("命令:")
        print("  1. 查看所有概念")
        print("  2. 查看所有别名/实体")
        print("  3. 查看待审核项")
        print("  4. 语义搜索概念")
        print("  5. 搜索别名/实体")
        print("  6. 人工指定概念")
        print("  0. 退出")
        print("-" * 40)

        cmd = input("\n请输入命令: ").strip()

        if cmd == '0':
            break
        elif cmd == '1':
            print_concepts(cursor)
        elif cmd == '2':
            print_aliases(cursor)
        elif cmd == '3':
            print_needs_review(cursor)
        elif cmd == '4':
            query = input("输入查询词: ").strip()
            if query:
                search_by_text(query, cursor, model)
        elif cmd == '5':
            query = input("输入搜索词: ").strip()
            if query:
                search_alias(query, cursor, model)
        elif cmd == '6':
            alias = input("别名/实体: ").strip()
            concept_id = input("目标概念ID (如 C001): ").strip()
            if alias and concept_id:
                if manual_assign(alias, concept_id, cursor):
                    conn.commit()
        else:
            print("无效命令")

    conn.close()


if __name__ == "__main__":
    main()
