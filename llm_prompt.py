#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_prompt.py - LLM 调用核心模块

提供：
  - call_llm()           : 基础 LLM API 调用
  - format_candidates()  : 格式化候选列表
  - llm_pick()           : 单次 LLM 选择（从候选列表中选一个）
  - llm_verify()         : 二次校验 LLM 匹配结果
"""

import os
import re
import time
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# =============================================================================
# System Prompt（优化版）
# =============================================================================

LLM_SYSTEM_PICK = """\
你是数学知识点双链修复助手。给定一段双链引用文本和文档列表，
判断该引用最应该指向哪个文档（基于语义相近程度）。

核心规则：
1. 引用文本可能只是文档名的一部分（如"例1.1.13"对应"例1.1.13-直角坐标方程化为极坐标方程"）
2. 引用文本可能是概念的不同表述（如"夹逼准则"对应"例1.1.6.8-由夹逼准则得右极限"）
3. 不要选语义范围更宽泛的候选：若引用文本是"导数的几何意义"，不应选"导数的几何意义与物理意义"
4. 优先选范围完全一致或更具体的候选
5. 优先选来源层级更近的候选（同小节 > 同节 > 同章），列表已按优先级排序
6. 警惕字面相似但语义完全不同的候选（如"极限"与"极坐标"、"导数"与"倒数"）
7. 如没有任何合适的文档，返回 0

输出格式：只输出一个整数，代表选择的候选序号（从 1 开始），或 0 代表无合适候选。
不要输出任何其他内容。"""

LLM_SYSTEM_VERIFY = """\
你是数学知识点双链校验助手。LLM 已为双链引用 [[X]] 选出一个候选匹配 Y。
判断这个匹配是否可以接受。

## 核心原则
X 和 Y 只要**含义相近、属同一概念范畴**即可接受。
重心是排除两类问题：**完全无关**和**有明显不同**。

## 同节放宽规则
如果提示包含"引用来自同一节"，说明 X 和 Y 属于同一节。
该语境下作者可能省略了限定词（如在"数列极限"节写"极限的定义"实际就是指"数列极限的-ε-N-定义"）。
同节时只要概念上不矛盾就应接受，不要纠结限定词的省略。

## 应返回 YES（接受）：
- X 和 Y 指同一数学概念，表述不同可接受
  （如 X="函数的定义"→Y="映射的定义"，本质相通）
- X 是 Y 的一部分或 Y 涵盖了 X
  （如 X="导数的几何意义"→Y="导数的几何意义-切线斜率"）
- X 的知识点集成在 Y 中，不算过于宽泛
- 同节语境下，X 的描述在 Y 的范围内
  （如在"数列极限"小节中 X="极限的定义"→Y="数列极限的-ε-N-定义"应接受）

## 应返回 NO（拒绝）：
- X 和 Y **字面相似但含义完全无关**
  （如 X="极限"→Y="极坐标"，X="导数"→Y="倒数"）
- X 和 Y 核心概念匹配但**有明确的限定差异**，且非同节
  （如 X="数列极限的定义"→Y="函数极限的定义"，虽都讲极限但对象明确不同）
- X 和 Y 分属完全不同的知识点范畴

## 输出格式
第一行：YES 或 NO
第二行：一句话理由（中文，不超过30字）
不要输出其他内容。"""


# =============================================================================
# 基础 LLM 调用
# =============================================================================

def call_llm(user_prompt: str, max_tokens: int = 16, max_retries: int = 2) -> Optional[str]:
    """调用 DashScope qwen-plus API"""
    try:
        from openai import OpenAI
    except ImportError:
        print("    warning: openai not installed, skip LLM")
        return None

    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        print("    warning: DASHSCOPE_API_KEY not set, skip LLM")
        return None

    model = os.environ.get("LLM_MODEL", "qwen-plus")
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    for attempt in range(1, max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": LLM_SYSTEM_PICK},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            print(f"    warning: LLM failed({attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(2)
    return None


# =============================================================================
# 候选格式化
# =============================================================================

def format_candidates(link_text: str, candidates: list[str], idx,  # HierarchyIndex
                       context: str = "") -> str:
    """将候选列表格式化为 LLM prompt 的用户消息"""
    lines = [f"引用文本: 【{link_text}】"]
    if context:
        lines.append(f"上下文: ...{context}...")
    lines.append(f"候选文档列表（共{len(candidates)}个）：")
    for i, stem in enumerate(candidates, 1):
        entry = idx.entries.get(stem, {})
        title = entry.get('title', stem)
        summary = entry.get('summary', '')
        source_label = idx.source_label(entry)
        lines.append(f"  {i}. {stem}")
        if title != stem:
            lines.append(f"     标题: {title}")
        if source_label:
            lines.append(f"     来源: {source_label}")
        if summary:
            lines.append(f"     摘要: {summary[:120]}")
    return '\n'.join(lines)


# =============================================================================
# 全量列表批处理上限
# =============================================================================

MAX_FULL_LIST_BATCH = 80  # 单次 LLM 调用最多发送的候选数


# =============================================================================
# LLM 选择
# =============================================================================

def llm_pick(link_text: str, candidates: list[str], idx,  # HierarchyIndex
             context: str = "", full_list: bool = False) -> Optional[str]:
    """让 LLM 从候选列表中选一个匹配的文档"""
    if not candidates and not full_list:
        return None

    if full_list:
        source_order = {'subsection': 0, 'section': 1, 'chapter': 2}
        all_stems = sorted(
            idx.stems(),
            key=lambda s: source_order.get(idx.entries.get(s, {}).get('source', 'chapter'), 9),
        )
        # 如果候选过多，分批发送，优先匹配排在前面（subsection）的批次
        if len(all_stems) > MAX_FULL_LIST_BATCH:
            for batch_start in range(0, len(all_stems), MAX_FULL_LIST_BATCH):
                batch = all_stems[batch_start:batch_start + MAX_FULL_LIST_BATCH]
                result = _llm_pick_from_list(link_text, batch, idx, context)
                if result is not None:
                    return result
            return None
        else:
            return _llm_pick_from_list(link_text, all_stems, idx, context)
    else:
        return _llm_pick_from_list(link_text, candidates, idx, context)


def _llm_pick_from_list(link_text: str, target_list: list[str], idx,
                         context: str = "") -> Optional[str]:
    """单次 LLM 调用从 target_list 中选一个"""
    if not target_list:
        return None
    prompt = format_candidates(link_text, target_list, idx, context)
    result = call_llm(prompt)
    if not result:
        return None

    m = re.search(r'\d+', result)
    if m:
        n = int(m.group())
        if n == 0:
            return None
        if 1 <= n <= len(target_list):
            return target_list[n - 1]
    return None


# =============================================================================
# LLM 验证
# =============================================================================

def _extract_numbered_prefix(text: str) -> Optional[str]:
    """提取编号前缀如 例1.6.10、定理1.4.3、推论1.5.2、定义1.3.1、图1.6.1。

    返回编号前缀字符串，无编号则返回 None。"""
    m = re.match(r'(例|定理|推论|定义|图)\d[\d\.]*', text)
    return m.group(0) if m else None


def llm_verify(link_text: str, matched_stem: str, idx,  # HierarchyIndex
               context: str = "", source_stem: str = "") -> tuple[bool, str]:
    """
    二次校验 LLM 匹配结果。

    返回 (is_correct, reason)。
    - is_correct=True 表示验证通过
    - reason 是 LLM 给出的理由
    - source_stem: 源文件的 stem，用于判断是否同节（同节应放宽）
    """
    entry = idx.entries.get(matched_stem, {})
    title = entry.get('title', matched_stem)
    summary = entry.get('summary', '')
    source_label = idx.source_label(entry)

    # 判断源文件和候选是否同节（用于 verify 提示词）
    same_scope = ""
    if source_stem:
        src_entry = idx.entries.get(source_stem, {})
        src_section = src_entry.get('section', '')
        tgt_section = entry.get('section', '')
        if src_section and src_section == tgt_section:
            same_scope = "（注意：引用来自同一节，该语境下可能省略了限定词，应更倾向于接受）"

    lines = [
        f"引用文本: 【{link_text}】",
        f"匹配到的文档: 【{matched_stem}】",
    ]
    if same_scope:
        lines.append(same_scope)
    if title != matched_stem:
        lines.append(f"文档标题: {title}")
    if source_label:
        lines.append(f"文档来源: {source_label}")
    if summary:
        lines.append(f"文档摘要: {summary[:200]}")
    if context:
        lines.append(f"原文上下文: ...{context}...")

    lines.append("\n这个匹配是否正确？两个是否指同一个数学概念？")

    prompt = '\n'.join(lines)

    try:
        from openai import OpenAI
    except ImportError:
        return True, "(skip: openai not installed)"

    api_key = os.environ.get("DASHSCOPE_API_KEY", "")
    if not api_key:
        return True, "(skip: no API key)"

    model = os.environ.get("LLM_MODEL", "qwen-plus")
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    for attempt in range(1, 3):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": LLM_SYSTEM_VERIFY},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=64,
            )
            text = resp.choices[0].message.content.strip()
            lines = text.split('\n')
            verdict = lines[0].strip().upper()
            reason = lines[1].strip() if len(lines) > 1 else text
            return verdict.startswith('YES'), reason
        except Exception as e:
            print(f"    warning: verify LLM failed({attempt}/2): {e}")
            if attempt < 2:
                time.sleep(2)

    # 验证 API 失败时保守处理：保留匹配
    return True, "(verify API failed, keep match)"
