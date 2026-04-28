#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量知识库构建脚本
- 读取 segments_output_pretty.json
- 使用 DashScope text-embedding-v2 生成中文嵌入向量
- 存入 SQLite 数据库
"""

import sys
import io
import json
import os
import sqlite3
import numpy as np
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

# ==================== 配置区 ====================
INPUT_JSON = "segments_output_pretty.json"
OUTPUT_DB = "knowledge_base.db"
EMBEDDING_MODEL = "text-embedding-v2"
# ==================== 配置区结束 ====================

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
    """批量编码文本（使用 DashScope text-embedding-v2）"""
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


def load_segments(json_path):
    """加载知识点段落"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"📖 加载 {len(data)} 条知识点")
    return data


def init_database(db_path):
    """初始化数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS knowledge_segments")
    cursor.execute("""
        CREATE TABLE knowledge_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            section TEXT,
            section_id TEXT,
            position INTEGER,
            title TEXT,
            content TEXT,
            raw_content TEXT,
            type TEXT,
            aliases TEXT,
            entities TEXT,
            refs TEXT,
            confidence REAL,
            needs_review INTEGER,
            summary TEXT,
            created_at TEXT,
            embedding BLOB
        )
    """)

    cursor.execute("DROP TABLE IF EXISTS metadata")
    cursor.execute("""
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    return conn


def build_knowledge_base():
    print("=" * 50)
    print("向量知识库构建")
    print("=" * 50)
    print(f"🤖 Embedding 模型: {EMBEDDING_MODEL}")

    # 加载数据
    segments = load_segments(INPUT_JSON)

    # 初始化数据库
    conn = init_database(OUTPUT_DB)
    cursor = conn.cursor()

    # 保存元数据
    cursor.execute("INSERT INTO metadata VALUES (?, ?)", ("embedding_model", EMBEDDING_MODEL))
    cursor.execute("INSERT INTO metadata VALUES (?, ?)", ("total_segments", str(len(segments))))
    cursor.execute("INSERT INTO metadata VALUES (?, ?)", ("created_at", ""))

    # 准备要嵌入的文本（用 content + title）
    texts_to_embed = []
    for seg in segments:
        text = f"{seg.get('title', '')}。{seg.get('content', '')}"
        texts_to_embed.append(text)

    # 生成向量
    print("\n🔢 生成向量嵌入...")
    embeddings = encode_texts(texts_to_embed)
    print(f"   向量维度: {embeddings.shape}")

    # 写入数据库
    print("\n💾 存入数据库...")
    for i, seg in enumerate(segments):
        embedding_blob = embeddings[i].astype(np.float32).tobytes()

        cursor.execute("""
            INSERT INTO knowledge_segments (
                source, section, section_id, position, title, content, raw_content,
                type, aliases, entities, refs, confidence, needs_review,
                summary, created_at, embedding
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            seg.get('source', ''),
            seg.get('section', ''),
            seg.get('section_id', ''),
            seg.get('position', 0),
            seg.get('title', ''),
            seg.get('content', ''),
            seg.get('raw_content', ''),
            seg.get('type', ''),
            json.dumps(seg.get('aliases', []), ensure_ascii=False),
            seg.get('entities', ''),
            json.dumps(seg.get('references', []), ensure_ascii=False),
            seg.get('confidence', 0),
            1 if seg.get('needs_review', False) else 0,
            seg.get('summary', ''),
            seg.get('created_at', ''),
            embedding_blob
        ))

    conn.commit()

    # 验证
    cursor.execute("SELECT COUNT(*) FROM knowledge_segments")
    count = cursor.fetchone()[0]
    print(f"\n✅ 完成！共存入 {count} 条知识")

    # 显示类型分布
    cursor.execute("SELECT type, COUNT(*) FROM knowledge_segments GROUP BY type")
    print("\n📊 类型分布:")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]}")

    # 显示样本
    print("\n📋 样本预览:")
    cursor.execute("SELECT id, type, title, LENGTH(embedding) FROM knowledge_segments LIMIT 3")
    for row in cursor.fetchall():
        print(f"   [{row[0]}] {row[1]} - {row[2]} (向量大小: {row[3]} bytes)")

    conn.close()
    print(f"\n📦 数据库: {OUTPUT_DB}")


if __name__ == "__main__":
    if not os.path.exists(INPUT_JSON):
        print(f"❌ 文件不存在: {INPUT_JSON}")
        exit(1)
    build_knowledge_base()
