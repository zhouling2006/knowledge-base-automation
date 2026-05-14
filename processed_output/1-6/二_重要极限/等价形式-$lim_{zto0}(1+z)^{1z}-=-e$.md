---
title: 等价形式：$\lim_{z\to0}(1+z)^{1/z} = e$
numeric_source: 1-6-2-9
aliases:
  - 零点形式的重要极限
  - 倒代换形式
tags:
  - 高等数学
  - 极限
  - 重要极限
  - 变量代换
source: 第一章/第六节/二、重要极限 \(\lim_{x\to \infty}\left(1 + \frac{1}{x}\right)^x = e\).md
position: 9
---

# 等价形式：$\lim_{z\to0}(1+z)^{1/z} = e$

在公式 (1.6.3) —— 即 $\lim_{x\to\infty}\left(1 + \frac{1}{x}\right)^x = e$ —— 中，作变量代换 $x = \frac{1}{z}$，则当 $x \to \infty$ 时，必有 $z \to 0$（且 $z \neq 0$）。由此导出该重要极限的**零点等价形式**：

$$
\lim_{z \to 0} (1 + z)^{\frac{1}{z}} = e.
$$

该式亦可将哑变量统一记为 $x$，写作：

$$
\lim_{x \to 0} (1 + x)^{\frac{1}{x}} = e.
$$

此形式在处理含 $(1+\text{无穷小})^{\text{无穷大}}$ 型未定式时极为常用，是标准极限 $\lim_{n\to\infty}(1+1/n)^n = e$ 在连续变量下的自然延拓，也是后续推导复合指数极限（如 $\lim (1+u(x))^{v(x)}$）的核心桥梁。

相关基础支撑：  
- [[离散情形回顾-数列极限-$lim_{ntoinfty}(1+1n)^n-=-e$.md]]{type=concept, label=数列极限基础, render=link, subject=高等数学, grade=大学, tags=极限|数列|重要极限}  
- [[连续变量推广-$x-to-pminfty$-时极限仍为-$e$.md]]{type=concept, label=连续推广结论, render=link, subject=高等数学, grade=大学, tags=极限|函数极限|重要极限}  
- [[综合结论-$lim_{xtoinfty}(1+1x)^x-=-e$.md]]{type=concept, label=完整极限公式, render=card, subject=高等数学, grade=大学, tags=极限|重要极限|公式(1.6.3)}

::: {.note}
该等价形式揭示了自然常数 $e$ 的本质定义之一：它是函数 $(1+z)^{1/z}$ 在 $z=0$ 处的**去心极限值**，体现了“单位增长速率”在瞬时尺度下的累积效应。
:::