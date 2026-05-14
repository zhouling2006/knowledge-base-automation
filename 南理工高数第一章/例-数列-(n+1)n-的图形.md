---
title: 例：数列 (n+1)/n 的图形
numeric_source: 1-2-1-4
aliases: []
tags:
  - 高等数学
  - 数列
  - 示例
  - 图像
---

# 例：数列 (n+1)/n 的图形

考虑数列  
$$
\left\{\frac{n+1}{n}\right\} = 2,\; \frac{3}{2},\; \frac{4}{3},\; \frac{5}{4},\; \dots,\; \frac{n+1}{n},\; \dots
$$  
该数列具有以下性质：
- 严格单调递减（因 $\frac{n+2}{n+1} - \frac{n+1}{n} = -\frac{1}{n(n+1)} < 0$）；
- 所有项大于 $1$，且以 $1$ 为下界；
- 极限为 $1$，即 $\displaystyle \lim_{n \to \infty} \frac{n+1}{n} = \lim_{n \to \infty} \left(1 + \frac{1}{n}\right) = 1$；
- 其图像如图1.2.2所示，点列从右侧（大于1一侧）单调趋近于 $1$。

![图1.2.2：数列 {(n+1)/n} 的数轴表示](images/fe2789b8e10eb97b5689cf29c4c1911c123ebf3eaeb68ebc22e1072b26f4a36c.jpg)  
图1.2.2

::: {.example label="数列 {(n+1)/n}" type=example}
此例展示了**极限非零但可显式计算**的典型数列，是理解“极限作为趋势终点”而非“某项取值”的关键范例。
:::

知识链接：[[数列的极限]]{type=concept, label=极限概念, render=link, subject=高等数学, grade=大学, tags=数列|极限|基础}  
结构分析：[[数列的单调性]]{type=concept, label=单调递减验证, render=link, tags=数列|单调}  
对照案例：[[例：数列 1/2ⁿ 的图形]]{type=example, label=零极限对比, render=card, tags=数列|收敛|图像}