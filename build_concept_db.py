#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标准概念库构建脚本
- 从 segments_output_pretty.json 提取概念
- 构建 concepts 表（标准概念 + 向量）
- 构建 aliases 表（别名 + 实体名词 + 向量）
"""

import sys
import io
import json
import os
import sqlite3
import numpy as np
from pathlib import Path
import ssl
import warnings
warnings.filterwarnings('ignore')

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

INPUT_JSON = "segments_output_pretty.json"
OUTPUT_DB = "concept_base.db"
EMBEDDING_MODEL = "text-embedding-v2"
VECTOR_DIM = 1536  # text-embedding-v2 固定维度

# DashScope API Key
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not DASHSCOPE_API_KEY:
    raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

try:
    from openai import OpenAI
except ImportError:
    print("❌ 请先安装: pip install openai")
    exit(1)

_embedding_client = None

def get_embedding_client():
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    return _embedding_client

def encode_texts(texts):
    """使用 DashScope text-embedding-v2 生成向量"""
    if not texts:
        return np.array([])

    client = get_embedding_client()

    # 分批处理（每批最多25条）
    all_embeddings = []
    batch_size = 25

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch
        )
        for item in response.data:
            all_embeddings.append(np.array(item.embedding, dtype=np.float32))
        print(f"  已处理 {min(i+batch_size, len(texts))}/{len(texts)} 条")

    return np.array(all_embeddings)


def init_database(db_path, force_rebuild=False):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if force_rebuild:
        cursor.execute("DROP TABLE IF EXISTS aliases")
        cursor.execute("DROP TABLE IF EXISTS concepts")
        cursor.execute("DROP TABLE IF EXISTS metadata")
        print("🗑️  已删除旧数据库")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS concepts (
            concept_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            file_path TEXT,
            title TEXT,
            content TEXT,
            concept_type TEXT,
            created_at TEXT,
            embedding BLOB
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aliases (
            alias TEXT PRIMARY KEY,
            block_id INTEGER,
            concept_id TEXT,
            alias_type TEXT CHECK(alias_type IN ('alias', 'entity', 'concept')),
            source_doc TEXT,
            confidence REAL DEFAULT 0.0,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'auto_mapped', 'llm_confirmed', 'needs_review', 'unmapped')),
            llm_reason TEXT,
            created_at TEXT,
            embedding BLOB,
            FOREIGN KEY (concept_id) REFERENCES concepts(concept_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_aliases_concept ON aliases(concept_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_aliases_status ON aliases(status)")

    return conn


def load_segments(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"📖 加载 {len(data)} 条知识点")
    return data


CONCEPT_TYPES = {'concept', 'definition', 'theorem'}


def extract_concepts(segments):
    concepts = []
    seen_names = set()

    for seg in segments:
        seg_type = seg.get('type', '')
        if seg_type not in CONCEPT_TYPES:
            continue

        title = seg.get('title', '').strip()
        if not title or title in seen_names:
            continue

        concepts.append({
            'concept_id': f"C{len(concepts) + 1:03d}",
            'name': title,
            'file_path': seg.get('source', ''),
            'title': title,
            'content': seg.get('content', ''),
            'concept_type': seg_type,
            'created_at': seg.get('created_at', '')
        })
        seen_names.add(title)

    return concepts


def extract_aliases(segments):
    aliases = []
    seen = set()

    concept_source_set = set()
    for seg in segments:
        seg_type = seg.get('type', '')
        if seg_type in CONCEPT_TYPES:
            concept_source_set.add(seg.get('source', ''))

    for idx, seg in enumerate(segments):
        source = seg.get('source', '')
        created_at = seg.get('created_at', '')
        seg_type = seg.get('type', '')
        block_id = idx + 1

        if seg_type in CONCEPT_TYPES:
            for alias in seg.get('aliases', []):
                if alias and alias not in seen:
                    aliases.append({
                        'alias': alias,
                        'block_id': block_id,
                        'alias_type': 'alias',
                        'source_doc': source,
                        'created_at': created_at
                    })
                    seen.add(alias)

        entities_str = seg.get('entities', '')
        if entities_str:
            for entity in entities_str.split(','):
                entity = entity.strip()
                if entity and entity not in seen:
                    aliases.append({
                        'alias': entity,
                        'block_id': block_id,
                        'alias_type': 'entity',
                        'source_doc': source,
                        'created_at': created_at
                    })
                    seen.add(entity)

    return aliases


def build_concept_base(force_rebuild=False):
    print("=" * 60)
    print("标准概念库构建")
    print("=" * 60)

    segments = load_segments(INPUT_JSON)

    conn = init_database(OUTPUT_DB, force_rebuild)
    cursor = conn.cursor()

    if force_rebuild:
        cursor.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)", ("embedding_model", EMBEDDING_MODEL))
        cursor.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)", ("created_at", ""))
    else:
        cursor.execute("SELECT value FROM metadata WHERE key = 'embedding_model'")
        row = cursor.fetchone()
        if row:
            print(f"\n📦 数据库已存在，增量更新模式")
        else:
            cursor.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)", ("embedding_model", EMBEDDING_MODEL))
            cursor.execute("INSERT OR REPLACE INTO metadata VALUES (?, ?)", ("created_at", ""))

    concepts = extract_concepts(segments)
    aliases = extract_aliases(segments)

    print(f"\n📚 提取 {len(concepts)} 个标准概念")
    print(f"📝 提取 {len(aliases)} 个别名/实体名词")

    if not force_rebuild:
        cursor.execute("SELECT name FROM concepts")
        existing_concepts = set(row[0] for row in cursor.fetchall())
        cursor.execute("SELECT alias FROM aliases")
        existing_aliases = set(row[0] for row in cursor.fetchall())
        concepts = [c for c in concepts if c['name'] not in existing_concepts]
        aliases = [a for a in aliases if a['alias'] not in existing_aliases]
        print(f"\n➕ 新增概念: {len(concepts)}")
        print(f"➕ 新增别名/实体: {len(aliases)}")

        if not concepts and not aliases:
            print("✅ 没有新增内容，无需更新")
            conn.close()
            return

    print(f"🤖 Embedding 模型: {EMBEDDING_MODEL}")

    new_concepts_added = 0
    new_aliases_added = 0

    if concepts:
        print("\n🔢 生成概念向量...")
        concept_texts = [c['name'] for c in concepts]
        concept_embeddings = encode_texts(concept_texts)

        print("\n💾 存入概念...")
        for i, concept in enumerate(concepts):
            embedding_blob = concept_embeddings[i].astype(np.float32).tobytes()
            cursor.execute("""
                INSERT OR REPLACE INTO concepts (concept_id, name, file_path, title, content, concept_type, created_at, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                concept['concept_id'],
                concept['name'],
                concept['file_path'],
                concept['title'],
                concept['content'],
                concept['concept_type'],
                concept['created_at'],
                embedding_blob
            ))
            new_concepts_added += 1

        # 概念名本身也加入 aliases 表（alias_type='concept'，直接映射到自身）
        print("💾 同步概念名到别名表...")
        cursor.execute("SELECT alias FROM aliases")
        existing_aliases = set(row[0] for row in cursor.fetchall())
        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        for i, concept in enumerate(concepts):
            cname = concept['name']
            if cname and cname not in existing_aliases:
                embedding_blob = concept_embeddings[i].astype(np.float32).tobytes()
                cursor.execute("""
                    INSERT OR REPLACE INTO aliases
                        (alias, block_id, concept_id, alias_type, source_doc, confidence, status, llm_reason, created_at, embedding)
                    VALUES (?, ?, ?, 'concept', ?, 1.0, 'auto_mapped', '概念名本身', ?, ?)
                """, (
                    cname,
                    None,
                    concept['concept_id'],
                    concept['file_path'],
                    now_str,
                    embedding_blob
                ))
                existing_aliases.add(cname)

    if aliases:
        print("🔢 生成别名/实体向量...")
        alias_texts = [a['alias'] for a in aliases]
        alias_embeddings = encode_texts(alias_texts)

        print("\n💾 存入别名/实体...")
        for i, alias in enumerate(aliases):
            embedding_blob = alias_embeddings[i].astype(np.float32).tobytes()
            cursor.execute("""
                INSERT OR REPLACE INTO aliases (alias, block_id, alias_type, source_doc, created_at, embedding, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (
                alias['alias'],
                alias['block_id'],
                alias['alias_type'],
                alias['source_doc'],
                alias['created_at'],
                embedding_blob
            ))
            new_aliases_added += 1

    conn.commit()

    print(f"\n✅ 完成！")
    print(f"   新增概念: {new_concepts_added}")
    print(f"   新增别名/实体: {new_aliases_added}")

    cursor.execute("SELECT COUNT(*) FROM concepts")
    total_concepts = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM aliases")
    total_aliases = cursor.fetchone()[0]
    print(f"\n📊 数据库总计:")
    print(f"   概念总数: {total_concepts}")
    print(f"   别名/实体总数: {total_aliases}")

    print("\n📊 别名类型分布:")
    cursor.execute("SELECT alias_type, COUNT(*) FROM aliases GROUP BY alias_type")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]}")

    print("\n📋 概念样本:")
    cursor.execute("SELECT concept_id, name, concept_type FROM concepts LIMIT 5")
    for row in cursor.fetchall():
        print(f"   [{row[0]}] {row[1]} ({row[2]})")

    print("\n📋 别名样本:")
    cursor.execute("SELECT alias, alias_type FROM aliases LIMIT 5")
    for row in cursor.fetchall():
        print(f"   '{row[0]}' ({row[1]})")

    conn.close()
    print(f"\n📦 数据库: {OUTPUT_DB}")


if __name__ == "__main__":
    if not os.path.exists(INPUT_JSON):
        print(f"❌ 文件不存在: {INPUT_JSON}")
        exit(1)

    import argparse
    parser = argparse.ArgumentParser(description='构建标准概念库')
    parser.add_argument('--rebuild', action='store_true', help='强制重建数据库（删除旧数据）')
    args = parser.parse_args()

    build_concept_base(force_rebuild=args.rebuild)
