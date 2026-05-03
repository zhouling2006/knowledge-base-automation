---
title: 分段函数
aliases:
  - 分段定义函数
  - piecewise function
tags:
  - 高等数学
  - 函数
  - 特殊函数
description: 定义、结构特征、常见实例及几何意义，强调“分域定义、统一规则”的思想。
author: 教材编写组
source: 《高等数学（上册）》第1章第3节注及例1.1.8–1.1.11
---
# 分段函数

## 定义

当函数在整个定义域上**无法用一个统一的解析式表示**时，可将定义域划分为若干个**互不相交的子集**，并在每个子集上分别指定一个解析式，由此定义的函数称为**分段函数**（piecewise-defined function）。

其一般形式为：
$$
f(x) =
\begin{cases}
f_1(x), & x \in I_1, \\
f_2(x), & x \in I_2, \\
\vdots \\
f_n(x), & x \in I_n,
\end{cases}
$$
其中 $I_1, I_2, \dots, I_n$ 是 $D_f$ 的一个划分（即 $I_i \cap I_j = \varnothing\ (i \ne j)$，且 $\bigcup_{i=1}^n I_i = D_f$）。

> ✅ 关键性质：对定义域中**每一个 $x$**，有且仅有一个解析式适用 → 仍为**单值函数**。

## 典型实例

| 名称         | 表达式                                                                 | 定义域             | 值域              | 图形特征         |
|--------------|------------------------------------------------------------------------|--------------------|-------------------|------------------|
| **三角波**   | $U(t) = \begin{cases} \frac{2E}{\tau}t, & 0 \le t < \frac{\tau}{2} \\ -\frac{2E}{\tau}(t-\tau), & \frac{\tau}{2} \le t \le \tau \end{cases}$ | $[0,\tau]$         | $[0,E]$           | 折线、周期性     |
| **绝对值函数** | $|x| = \begin{cases} x, & x \ge 0 \\ -x, & x < 0 \end{cases}$            | $(-\infty,+\infty)$ | $[0,+\infty)$     | V形、连续不可导  |
| **符号函数**   | $\operatorname{sgn}x = \begin{cases} 1, & x > 0 \\ 0, & x = 0 \\ -1, & x < 0 \end{cases}$ | $(-\infty,+\infty)$ | $\{-1,0,1\}$      | 阶梯、不连续     |
| **取整函数**   | $[x] = \max\{k \in \mathbb{Z} \mid k \le x\}$                           | $(-\infty,+\infty)$ | $\mathbb{Z}$      | 阶梯、右连续     |
| **狄利克雷函数** | $D(x) = \begin{cases} 1, & x \in \mathbb{Q} \\ 0, & x \notin \mathbb{Q} \end{cases}$ | $(-\infty,+\infty)$ | $\{0,1\}$         | 无图像（处处不连续） |

![图1.1.8：三角波](https://cdn-mineru.openxlab.org.cn/result/2026-04-03/ccf3acff-bbac-48d8-97dd-e31ada0e3759/b60be3cb93613cdb6d982cd7824bada7adccfc46f9ace1fad101f357a5f313da.jpg)  
图1.1.8：脉冲三角波（分段线性）

![图1.1.9：绝对值函数](https://cdn-mineru.openxlab.org.cn/result/2026-04-03/ccf3acff-bbac-48d8-97dd-e31ada0e3759/e6417afae7978ffdad8f8d0b18dfb7c94bce954be9a6819828b316dc7c4a5c6b.jpg)  
图1.1.9：$y = |x|$ 的V形图像

::: {#note-piecewise-domain-range .note label="定义域与值域的确定" type=concept}
- **定义域** = 所有子区间之并集；
- **值域** = 各段函数值域之并集；
- 分段点处的函数值必须明确指定（如 $\operatorname{sgn}0 = 0$），否则函数未完全定义。
:::

延伸学习：  
- [[例1.1.12：分段函数的平移变换]]{type=example, label=变量替换, render=card, id=例1.1.12, tags=函数|变换}  
- [[函数的图形定义]]{type=concept, label=图像特征, render=link, tags=函数|几何}  
- [[多值函数与单值分支]]{type=concept, label=对比概念, render=link, tags=函数|分类}