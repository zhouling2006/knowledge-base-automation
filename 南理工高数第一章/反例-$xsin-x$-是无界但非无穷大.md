---
title: 反例：$x\sin x$ 是无界但非无穷大
numeric_source: 1-4-2-8
aliases: []
tags:
  - 高等数学
  - 极限
  - 反例
  - 无界变量
  - 无穷大
source: 第一章/第四节/二、无穷大.md
position: 8
---

# 反例：$x\sin x$ 是无界但非无穷大

函数  
$$
f(x) = x \sin x
$$  
在 $x \to +\infty$ 过程中，是一个经典的**无界但非无穷大**的反例，有力佐证了“无界 ⇏ 无穷大”。

### 证明其无界性  
对任意 $M > 0$，取序列  
$$
x_n = 2n\pi + \frac{\pi}{2}, \quad n \in \mathbb{N},
$$  
则  
$$
\lim_{n \to \infty} x_n = +\infty,
$$  
且  
$$
|f(x_n)| = \left| \left(2n\pi + \frac{\pi}{2}\right) \cdot \sin\left(2n\pi + \frac{\pi}{2}\right) \right| = 2n\pi + \frac{\pi}{2} > M \quad (\text{当 } n \text{ 充分大时}).
$$  
故 $f(x)$ 在 $x \to +\infty$ 时**无界**。

### 证明其非无穷大  
取 $M = 1$。对任意 $X > 0$，总可取  
$$
x_n = n\pi, \quad n > X/\pi,
$$  
此时 $x_n > X$，但  
$$
|f(x_n)| = |n\pi \cdot \sin(n\pi)| = 0 < 1 = M.
$$  
因此，**不存在**满足无穷大定义所需的统一 $X$（或 $\delta$），故 $f(x)$ 在 $x \to +\infty$ 时**不是无穷大**。

该反例深刻揭示：无界性仅要求函数值能“冲破任意高度”，而无穷大还要求其**全程远离零点、不反复回落**。

核心结论引用：[[关于无穷大的三点注释]]{type=concept, label=第三点注释, render=link, tags=概念辨析|反例支撑}

关联知识点：[[无穷大的定义]]{type=concept, label=定义对照, render=card, tags=极限|严格性}

::: {.example label="无界但非无穷大反例" type=example}
此例常被用于高等数学课程中检验学生对“无穷大”本质的理解深度——是否停留在“很大”表象，还是把握住“一致发散”的量化内核。
:::