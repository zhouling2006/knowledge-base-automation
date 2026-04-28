#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
别名对齐脚本
- 别名：直接向量映射
- 实体名词：向量相似度 + LLM 双重判断
- 允许 concept_id 为 null（人工审核）
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

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_DISABLE_SSL_VERIFICATION'] = '1'
ssl._create_default_https_context = ssl._create_unverified_context

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

DB_PATH = "concept_base.db"
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"

VECTOR_THRESHOLD = 0.75

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

LLM_API_KEY = os.environ.get("ZHIPU_API_KEY", "")
LLM_MODEL = "glm-4-flash"

if not LLM_API_KEY:
    raise ValueError("请设置环境变量 ZHIPU_API_KEY")

try:
    from sentence_transformers import SentenceTransformer, util
    from zhipuai import ZhipuAI
except ImportError:
    print("❌ 请先安装: pip install sentence-transformers zhipuai")
    exit(1)


def load_model():
    print(f"🤖 加载模型: {EMBEDDING_MODEL}")
    return SentenceTransformer(EMBEDDING_MODEL)


def llm_judge(alias, concept_name, concept_content):
    prompt = f"""你是数学概念知识对齐专家。请判断术语与概念的关系类型。

术语: {alias}
目标概念: {concept_name}
概念内容摘要: {concept_content[:300]}

判断标准：
- 高关联：术语是概念的同义词/别名（注意：必须是等价关系，不允许反向包含）
- 中关联：术语是概念的组成部分，或者概念是术语的上位概念
- 无关联：术语与概念无关

重要：
1. "函数的表示法"是"函数"的一部分，"函数的表示法" ≠ "函数"，不能算高关联
2. 只能术语 = 概念 或 术语 ≈ 概念 时才算高关联
3. 如果概念是术语的上位概念，或者术语是概念的组成部分，都只能算中关联

请只回答以下格式（不要有其他内容）：
{{"decision": "高关联|中关联|无关联", "reason": "简短原因"}}
"""
    
    try:
        client = ZhipuAI(api_key=LLM_API_KEY)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        return json.loads(content.strip())
    except Exception as e:
        return {"decision": "无关联", "reason": f"LLM调用失败: {str(e)}"}


def align_aliases(model, rerun_all=False):
    print("=" * 60)
    print("别名对齐")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT concept_id, name, content, embedding FROM concepts")
    concepts = cursor.fetchall()

    concept_data = []
    for row in concepts:
        concept_id, name, content, embedding_blob = row
        embedding = np.frombuffer(embedding_blob, dtype=np.float32) if embedding_blob else None
        concept_data.append({
            'concept_id': concept_id,
            'name': name,
            'content': content,
            'embedding': embedding
        })

    print(f"📚 加载 {len(concept_data)} 个概念")

    if rerun_all:
        cursor.execute("UPDATE aliases SET status = 'pending', concept_id = NULL, confidence = 0, llm_reason = NULL WHERE alias_type = 'entity'")
        print("🔄 重新对齐所有实体")
        cursor.execute("SELECT alias, alias_type, embedding FROM aliases WHERE alias_type = 'entity'")
    else:
        cursor.execute("SELECT alias, alias_type, embedding FROM aliases WHERE status = 'pending'")

    pending_aliases = cursor.fetchall()
    print(f"📝 待处理 {len(pending_aliases)} 个别名/实体")

    if not pending_aliases:
        print("✅ 没有待处理的别名")
        conn.close()
        return

    auto_mapped = 0
    llm_confirmed = 0
    llm_rejected = 0
    needs_review = 0
    unmapped = 0

    for alias, alias_type, embedding_blob in pending_aliases:
        alias_embedding = np.frombuffer(embedding_blob, dtype=np.float32) if embedding_blob else None

        if alias_embedding is None:
            cursor.execute("UPDATE aliases SET status = 'unmapped' WHERE alias = ?", (alias,))
            unmapped += 1
            continue

        best_match = None
        best_similarity = 0

        for concept in concept_data:
            if concept['embedding'] is None:
                continue
            sim = util.cos_sim(alias_embedding, concept['embedding']).item()
            if sim > best_similarity:
                best_similarity = sim
                best_match = concept

        if best_match and best_similarity >= VECTOR_THRESHOLD:
            if alias_type == 'alias':
                cursor.execute("""
                    UPDATE aliases SET concept_id = ?, confidence = ?, status = 'auto_mapped', llm_reason = ?
                    WHERE alias = ?
                """, (best_match['concept_id'], best_similarity, f'向量匹配(阈值{VECTOR_THRESHOLD})', alias))
                auto_mapped += 1
                print(f"  ✓ 别名 '{alias}' → [{best_match['concept_id']}] {best_match['name']} (sim={best_similarity:.3f})")

            else:
                llm_result = llm_judge(alias, best_match['name'], best_match['content'])
                decision = llm_result.get('decision', '无关联')
                reason = llm_result.get('reason', '')

                if decision == '高关联':
                    cursor.execute("""
                        UPDATE aliases SET concept_id = ?, confidence = ?, status = 'llm_confirmed', llm_reason = ?
                        WHERE alias = ?
                    """, (best_match['concept_id'], best_similarity, f'LLM:{decision}|{reason}', alias))
                    llm_confirmed += 1
                    print(f"  ✓ 实体 '{alias}' → [{best_match['concept_id']}] {best_match['name']} (sim={best_similarity:.3f}, LLM:高关联)")

                elif decision == '中关联':
                    cursor.execute("""
                        UPDATE aliases SET concept_id = NULL, confidence = ?, status = 'needs_review', llm_reason = ?
                        WHERE alias = ?
                    """, (best_similarity, f'LLM:{decision}|{reason}', alias))
                    needs_review += 1
                    print(f"  ? 实体 '{alias}' → 待审核 (sim={best_similarity:.3f}, LLM:中关联-无映射)")

                else:
                    cursor.execute("""
                        UPDATE aliases SET concept_id = NULL, confidence = ?, status = 'needs_review', llm_reason = ?
                        WHERE alias = ?
                    """, (best_similarity, f'LLM:{decision}|{reason}', alias))
                    llm_rejected += 1
                    print(f"  ✗ 实体 '{alias}' → 无匹配 (sim={best_similarity:.3f}, LLM:无关联)")

        elif alias_type == 'alias':
            cursor.execute("""
                UPDATE aliases SET concept_id = ?, confidence = ?, status = 'needs_review', llm_reason = ?
                WHERE alias = ?
            """, (best_match['concept_id'] if best_match else None, best_similarity, f'向量相似度不足({best_similarity:.3f}<{VECTOR_THRESHOLD})', alias))
            needs_review += 1
            print(f"  ? 别名 '{alias}' → 相似度不足 (sim={best_similarity:.3f})")

        else:
            cursor.execute("""
                UPDATE aliases SET concept_id = NULL, confidence = ?, status = 'needs_review', llm_reason = ?
                WHERE alias = ?
            """, (best_similarity if best_match else 0, f'向量相似度不足({best_similarity:.3f}<{VECTOR_THRESHOLD})' if best_match else '无匹配概念', alias))
            needs_review += 1
            print(f"  ? 实体 '{alias}' → 无匹配 (sim={best_similarity:.3f})")

        conn.commit()

    print(f"\n📊 对齐结果:")
    print(f"   别名自动映射: {auto_mapped}")
    print(f"   实体LLM确认: {llm_confirmed}")
    print(f"   实体LLM拒绝: {llm_rejected}")
    print(f"   待人工审核: {needs_review}")
    print(f"   无法映射: {unmapped}")

    print(f"\n📊 当前数据库状态:")
    cursor.execute("SELECT status, COUNT(*) FROM aliases GROUP BY status")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]}")

    conn.close()


if __name__ == "__main__":
    if not Path(DB_PATH).exists():
        print(f"❌ 数据库不存在: {DB_PATH}")
        print("   请先运行 build_concept_db.py 构建概念库")
        exit(1)

    import argparse
    parser = argparse.ArgumentParser(description='别名对齐')
    parser.add_argument('--rerun', action='store_true', help='重新对齐所有实体（忽略已有结果）')
    args = parser.parse_args()

    model = load_model()
    align_aliases(model, rerun_all=args.rerun)