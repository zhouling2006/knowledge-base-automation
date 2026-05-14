---
title: 连续变量推广：$x \to \pm\infty$ 时极限仍为 $e$
numeric_source: 1-6-2-3
aliases:
  - 实变量推广形式
  - 双向无穷极限
tags:
  - 高等数学
  - 函数极限
  - 连续推广
  - 自然常数
source: 第一章/第六节/二、重要极限 \(\lim_{x\to \infty}\left(1 + \frac{1}{x}\right)^x = e\).md
position: 3
---

# 连续变量推广：$x \to \pm\infty$ 时极限仍为 $e$

在已知数列极限 $\lim_{n\to\infty}(1+1/n)^n = e$ 的基础上，将离散变量 $n$ 替换为**实变量 $x$**，考察函数  
$$
f(x) = \left(1 + \frac{1}{x}\right)^x,
$$  
其定义域为 $(-\infty, -1) \cup (1, +\infty)$。

关键结论：  
- 当 $x \to +\infty$ 时，$\lim_{x \to +\infty} f(x) = e$；  
- 当 $x \to -\infty$ 时，$\lim_{x \to -\infty} f(x) = e$；  
- 因此可统一记为：  
  $$
  \lim_{x \to \infty} \left(1 + \frac{1}{x}\right)^x = e,
  $$  
  其中 $x \to \infty$ 表示**广义无穷**（即不区分正负方向的无穷大），这是分析学中常见简写。

> 📌 **意义说明**：  
> 此推广表明：$e$ 不仅是数列的极限值，更是某类初等函数在无穷远处的**稳定渐近行为**，从而支撑起指数函数 $e^x$ 的微积分定义（如导数 $\frac{d}{dx}e^x = e^x$）。

关联知识：  
- [[重要极限 $\lim_{x\to \infty}\left(1 + \frac{1}{x}\right)^x = e$]]{type=concept, label=统一表述, render=link, tags=重要极限|e}  
- [[例1.6.8：证明 $\lim_{x\to +\infty}(1+1/x)^x = e$（夹逼法）]]{type=example, id=例1.6.8, label=正向证明, render=link, tags=极限|夹逼}  
- [[例1.6.8补证：$\lim_{x\to -\infty}(1+1/x)^x = e$]]{type=proof, label=负向证明, render=link, note=变量代换法, tags=极限|代换}

::: {.note}
该推广并非平凡：需独立验证负无穷情形（见例1.6.8后半部分），不能仅由正向极限推出。其成立依赖于函数在 $(-\infty,-1)$ 上的良好定义性与连续性。
:::