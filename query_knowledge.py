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

# 使用国内镜像
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_DISABLE_SSL_VERIFICATION'] = '1'

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

# ==================== 配置区 ====================
DB_PATH = "knowledge_base.db"
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"
TOP_K = 5
# ==================== 配置区结束 ====================

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    print("❌ 请先安装: pip install sentence-transformers")
    exit(1)


def load_model():
    """加载 embedding 模型"""
    print(f"🤖 加载模型: {EMBEDDING_MODEL}")
    return SentenceTransformer(EMBEDDING_MODEL)


def search(query, model, top_k=TOP_K):
    """语义搜索"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 生成查询向量
    query_embedding = model.encode(query)

    # 获取所有向量
    cursor.execute("SELECT id, title, content, type, embedding FROM knowledge_segments")
    rows = cursor.fetchall()

    results = []
    for row in rows:
        seg_id, title, content, seg_type, embedding_blob = row
        embedding = np.frombuffer(embedding_blob, dtype=np.float32)

        # 计算余弦相似度
        similarity = util.cos_sim(query_embedding, embedding).item()

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

    if not Path(DB_PATH).exists():
        print(f"❌ 数据库不存在: {DB_PATH}")
        print("   请先运行 build_vector_db.py 构建知识库")
        return

    model = load_model()

    while True:
        query = input("\n🔍 输入查询（回车退出）: ").strip()
        if not query:
            break

        results = search(query, model)
        print_results(results)


if __name__ == "__main__":
    main()
