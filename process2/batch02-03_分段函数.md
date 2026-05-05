---
title: 分段函数
aliases:
  - 分段定义函数
  - piecewise function
tags:
  - 高等数学
  - 函数
  - 特殊函数
description: 定义分段函数为在定义域不同子集上采用不同解析式描述的函数；涵盖绝对值、符号、取整、狄利克雷等经典范例。
---
# 分段函数

当函数在整个定义域上**无法用一个统一的解析式表示**时，可将其定义域划分为若干个互不相交的真子集，并在每个子集上分别给出对应的解析式。这类函数称为**分段函数（piecewise function）**。

形式上，若 $D = D_1 \cup D_2 \cup \cdots \cup D_n$，其中 $D_i \cap D_j = \varnothing\ (i \ne j)$，且对每个 $x \in D_i$，有 $f(x) = f_i(x)$，则：

$$
f(x) =
\begin{cases}
f_1(x), & x \in D_1, \\
f_2(x), & x \in D_2, \\
\vdots \\
f_n(x), & x \in D_n.
\end{cases}
$$

其**定义域**为各子集之并：$D_f = \bigcup_{i=1}^{n} D_i$；  
其**值域**为各段值域之并：$R_f = \bigcup_{i=1}^{n} R_{f_i}$。

::: {#example-piecewise-001 .example label="三角波函数" type=example}
脉冲发生器产生的三角波（见图1.1.8）：
$$
U(t) =
\begin{cases}
\frac{2E}{\tau} t, & 0 \leq t < \frac{\tau}{2}, \\
-\frac{2E}{\tau}(t - \tau), & \frac{\tau}{2} \leq t \leq \tau.
\end{cases}
$$
定义域：$[0,\tau]$；值域：$[0,E]$。
:::

经典分段函数示例：
- [[例1.1.8-绝对值函数]]{type=example, id=例1.1.8, label=|x|, render=link, tags=基础|分段}
- [[例1.1.9-符号函数]]{type=example, id=例1.1.9, label=sgn x, render=link, tags=离散|分段}
- [[例1.1.10-取整函数]]{type=example, id=例1.1.10, label=[x], render=link, tags=离散|分段}
- [[例1.1.11-狄利克雷函数]]{type=example, id=例1.1.11, label=D(x), render=card, tags=病态|分段}

> ⚠️ 注意：狄利克雷函数 $D(x)$ 在任意区间上都**不可画出图像**——因有理数与无理数在实数轴上稠密交错，导致其图像“处处跳跃、处处不连”。

![图1.1.8](https://cdn-mineru.openxlab.org.cn/result/2026-04-03/ccf3acff-bbac-48d8-97dd-e31ada0e3759/b60be3cb93613cdb6d982cd7824bada7adccfc46f9ace1fad101f357a5f313da.jpg)  
图1.1.8 —— 三角波函数图像（分段线性）

![图1.1.9](https://cdn-mineru.openxlab.org.cn/result/2026-04-03/ccf3acff-bbac-48d8-97dd-e31ada0e3759/e6417afae7978ffdad8f8d0b18dfb7c94bce954be9a6819828b316dc7c4a5c6b.jpg)  
图1.1.9 —— 绝对值函数图像（V形折线）