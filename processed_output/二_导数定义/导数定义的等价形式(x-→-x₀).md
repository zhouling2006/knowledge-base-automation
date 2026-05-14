---
title: 导数定义的等价形式（x → x₀）
numeric_source: 2-1-2-4
aliases:
  - 差商极限（两点式）
tags:
  - 高等数学
  - 导数
  - 定义等价性
source: 第二章/第一节/二、导数定义.md
position: 4
---

# 导数定义的等价形式（x → x₀）

在导数定义中，令 $x = x_0 + \Delta x$，则 $\Delta x \to 0$ 等价于 $x \to x_0$，且  
$$
\frac{f(x_0 + \Delta x) - f(x_0)}{\Delta x} = \frac{f(x) - f(x_0)}{x - x_0}.
$$  
因此，导数可等价地定义为：  
$$
f'(x_0) = \lim_{x \to x_0} \frac{f(x) - f(x_0)}{x - x_0}. \tag{2.1.2}
$$  

该形式强调**两点间差商在自变量趋近时的极限**，更突出“局部变化率”的直观含义，也便于后续推导（如洛必达法则、中值定理）。

对比标准定义：[[导数的定义]]{type=concept, label=增量式定义, render=link, tags=导数|基础概念}  
补充形式（步长 $h$）：[[导数定义的等价形式（h → 0）]]{type=concept, label=步长形式, render=link, tags=导数|等价定义}

::: {.note}
> **教学提示**：两种形式本质一致，但适用场景略有不同——$\Delta x$ 形式便于物理建模（强调“变化量”），$x \to x_0$ 形式便于分析函数性态（强调“趋近过程”）。熟练切换有助于深化理解。
:::