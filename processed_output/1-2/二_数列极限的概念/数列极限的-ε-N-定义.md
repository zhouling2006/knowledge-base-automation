---
title: 数列极限的 ε-N 定义
numeric_source: 1-2-2-3
aliases:
  - ε-N 定义
  - 柯西极限定义
tags:
  - 高等数学
  - 数列极限
  - 严格定义
source: 第一章/第二节/二、数列极限的概念.md
position: 3
---

# 数列极限的 ε-N 定义

> **定义（数列极限的 $\varepsilon$-$N$ 定义）**  
> 设有数列 $\{u_n\}$。若存在常数 $a$，使得对**任意给定的正数 $\varepsilon > 0$**，总存在**正整数 $N$**，使得当 $n > N$ 时，恒有  
> $$
|u_n - a| < \varepsilon,
$$  
> 则称常数 $a$ 为数列 $\{u_n\}$ 当 $n \to \infty$ 时的**极限**，也称 $\{u_n\}$ **收敛于 $a$**。  
> 记作  
> $$
\lim_{n \to \infty} u_n = a \quad \text{或} \quad u_n \to a \; (n \to \infty).
$$  
> 否则，称 $\{u_n\}$ **发散**（即极限不存在）。

该定义亦称为**$\varepsilon$-$N$ 语言**，是分析学中极限概念的**严格逻辑基石**。

::: {.note}
- $\varepsilon$ 的**任意性**：体现“无限接近”的彻底性——精度可任取，无下界；
- $N$ 的**存在性与依赖性**：对每个 $\varepsilon$，只需存在某个 $N$（不必最小），且 $N$ 通常随 $\varepsilon$ 减小而增大；
- 定义**不提供求法**，仅提供**验证标准**；后续将学习极限运算法则与技巧。
:::

几何解释见：[[数列极限的几何意义]]{type=concept, label=几何图示, render=link, tags=数列极限|几何视角}  
应用范例：[[例1.2.1：(-1)ⁿ⁻¹/n 的极限]]{type=question, id=例1.2.1, label=(-1)ⁿ⁻¹/n → 0, render=card, source=教材例题, answer=0, tags=数列极限|验证题}

::: {#def-seq-limit-epsN .definition label="ε-N 定义（标准表述）" type=definition}
设 $\{u_n\}$ 是一个数列。若 $\forall \varepsilon > 0,\; \exists N \in \mathbb{N}^+$，使得 $\forall n > N$，有 $|u_n - a| < \varepsilon$，则称 $a$ 为 $\{u_n\}$ 的极限。
:::