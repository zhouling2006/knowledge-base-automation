#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量知识库查询脚本
- 根据语义相似度搜索知识点
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
DB_PATH = "knowledge_base.db"
EMBEDDING_MODEL = "text-embedding-v2"
TOP_K = 5
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

def encode_text(text):
    """使用 DashScope text-embedding-v2 生成向量"""
    client = get_embedding_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)


def search(query, top_k=TOP_K):
    """语义搜索"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 生成查询向量
    query_embedding = encode_text(query)

    # 获取所有向量
    cursor.execute("SELECT id, title, content, type, embedding FROM knowledge_segments")
    rows = cursor.fetchall()

    results = []
    for row in rows:
        seg_id, title, content, seg_type, embedding_blob = row
        embedding = np.frombuffer(embedding_blob, dtype=np.float32)

        # 阿里 embedding 已归一化，直接用点积计算余弦相似度
        similarity = np.dot(query_embedding, embedding).item()

        results.append({
            'id': seg_id,
            'title': title,
            'content': content[:200] + '...' if len(content) > 200 else content,
            'type': seg_type,
            'similarity': similarity
        })

    conn.close()

    # 按相似度排序
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]


def print_results(results):
    """打印结果"""
    for i, r in enumerate(results, 1):
        print(f"\n{'='*60}")
        print(f"[{i}] {r['title']}")
        print(f"    类型: {r['type']} | 相似度: {r['similarity']:.4f}")
        print(f"    内容: {r['content']}")


def main():
    print("=" * 60)
    print("向量知识库语义搜索")
    print("=" * 60)
    print(f"🤖 Embedding 模型: {EMBEDDING_MODEL}")

    if not Path(DB_PATH).exists():
        print(f"❌ 数据库不存在: {DB_PATH}")
        print("   请先运行 build_vector_db.py 构建知识库")
        return

    while True:
        query = input("\n🔍 输入查询（回车退出）: ").strip()
        if not query:
            break

        results = search(query)
        print_results(results)


if __name__ == "__main__":
    main()
