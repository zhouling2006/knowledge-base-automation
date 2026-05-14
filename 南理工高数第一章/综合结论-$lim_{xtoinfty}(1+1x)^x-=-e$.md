---
title: 综合结论：$\lim_{x\to\infty}(1+1/x)^x = e$
numeric_source: 1-6-2-8
aliases:
  - 公式(1.6.3)
tags:
  - 高等数学
  - 极限
  - 重要极限
  - 公式编号
source: 第一章/第六节/二、重要极限 \(\lim_{x\to \infty}\left(1 + \frac{1}{x}\right)^x = e\).md
position: 8
---

# 综合结论：$\lim_{x\to\infty}(1+1/x)^x = e$

综合右极限与左极限两部分结果：

- $\displaystyle \lim_{x \to +\infty} \left(1 + \frac{1}{x}\right)^x = e$，
- $\displaystyle \lim_{x \to -\infty} \left(1 + \frac{1}{x}\right)^x = e$，

可得统一结论：

$$
\lim_{x \to \infty} \left(1 + \frac{1}{x}\right)^x = e. \tag{1.6.3}
$$

该公式被称作**第二个重要极限**（第一个为 $\lim_{x \to 0} \frac{\sin x}{x} = 1$），是自然指数函数 $e^x$ 与对数函数 $\ln x$ 微积分理论的基石之一。

进一步作变量替换 $x = \frac{1}{z}$（即 $z = \frac{1}{x}$），当 $x \to \infty$ 时 $z \to 0$，立即导出等价形式：

$$
\lim_{z \to 0} (1 + z)^{\frac{1}{z}} = e,
$$

或写作：

$$
\lim_{x \to 0} (1 + x)^{\frac{1}{x}} = e.
$$

该等价形式在处理 $1^\infty$ 型未定式时极为常用，是后续例1.6.9、例1.6.10等计算题的直接依据。

::: {.note}
该结论首次系统确立了连续变量下 $(1+1/x)^x$ 的极限行为，并与离散情形 [[离散情形回顾-数列极限-$lim_{ntoinfty}(1+1n)^n-=-e$.md]]{type=concept, label=数列极限 $e$, render=link, tags=极限|数列} 形成完美呼应，体现数学分析中“离散→连续”的自然延拓思想。
:::

延伸应用见：
- [[例1.6.9-求-$lim_{xto-infty}(1-13x)^x$.md]]{type=question, id=例1.6.9, label=形如 $(1+a/x)^x$ 的极限, render=card, source=同济高数, answer=e^{-1/3}, tags=高数|极限|计算题}
- [[例1.6.10-求-$lim_{xto-0}(1-x)^{2x}$.md]]{type=question, id=例1.6.10, label=形如 $(1+ax)^{b/x}$ 的极限, render=card, source=同济高数, answer=e^{-2}, tags=高数|极限|计算题}