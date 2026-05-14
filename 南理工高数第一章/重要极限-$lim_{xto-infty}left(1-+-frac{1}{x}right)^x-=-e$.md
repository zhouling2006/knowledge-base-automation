---
title: 重要极限 $\lim_{x\to \infty}\left(1 + \frac{1}{x}\right)^x = e$
numeric_source: 1-6-2-1
aliases:
  - 第二个重要极限
  - 自然指数极限
  - e的定义极限
tags:
  - 高等数学
  - 极限
  - 重要极限
  - 自然常数
source: 第一章/第六节/二、重要极限 \(\lim_{x\to \infty}\left(1 + \frac{1}{x}\right)^x = e\).md
position: 1
---

# 重要极限 $\lim_{x\to \infty}\left(1 + \frac{1}{x}\right)^x = e$

该极限是微积分中**第二个重要极限**，其核心意义在于：  
当自变量 $x$ 趋向无穷（不区分正负）时，函数  
$$
\left(1 + \frac{1}{x}\right)^x
$$  
的极限存在，且精确等于自然常数 $e \approx 2.71828\ldots$。

这一极限不仅是 $e$ 的分析定义之一，更是后续导数、指数函数与对数函数理论的基石。它将离散的数列极限自然延拓至连续函数，体现了极限理论中“离散→连续”的典型统一思想。

> ✅ **关键特征**：  
> - 定义域为 $|x| > 1$（避免分母为零及底数非正）；  
> - 极限值与路径无关：$x \to +\infty$ 与 $x \to -\infty$ 均收敛于同一值 $e$；  
> - 可等价变形为 $\lim_{x \to 0}(1+x)^{1/x} = e$，构成 $e$ 的两种标准解析定义。

相关知识点：  
- [[离散情形回顾：数列极限 $\lim_{n\to\infty}(1+1/n)^n = e$]]{type=concept, label=数列基础, render=link, subject=高等数学, grade=大学, tags=重要极限|数列|e}  
- [[连续变量推广：$x \to \pm\infty$ 时极限仍为 $e$]]{type=concept, label=双向推广, render=link, tags=极限|连续|e}  
- [[例1.6.8：证明 $\lim_{x\to +\infty}(1+1/x)^x = e$（夹逼法）]]{type=example, id=例1.6.8, label=右极限证明, render=card, source=教材, tags=重要极限|夹逼准则|证明}

::: {.note}
该极限常被记作式 (1.6.3)，是本节核心结论，后续所有变形题（如例1.6.9、例1.6.10）均以此为基础。
:::