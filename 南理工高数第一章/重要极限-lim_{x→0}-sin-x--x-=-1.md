---
title: 重要极限：lim_{x→0} sin x / x = 1
numeric_source: 1-6-1-7
aliases:
  - 正弦比极限
  - 第一个重要极限
tags:
  - 高等数学
  - 极限
  - 三角函数
  - 重要极限
source: 第一章/第六节/一、夹逼准则和重要极限 $\lim_{x\to 0}\frac{\sin x}{x} = 1$.md
position: 7
---

# 重要极限：$\lim_{x\to 0} \dfrac{\sin x}{x} = 1$

该极限是微积分中**最基础且最重要的极限之一**，刻画了小角下正弦函数与弧度量的线性近似关系：
$$
\sin x \sim x \quad (x \to 0).
$$

它不仅是推导 $\left(\sin x\right)' = \cos x$ 等三角函数导数的起点，更是求解各类“$\frac{0}{0}$”型未定式（如 $\tan x/x$、$(1-\cos x)/x^2$、$\sin kx / \sin mx$ 等）的核心工具。

此极限的严格成立依赖于[[夹逼准则(函数形式)]]{type=concept, label=函数夹逼准则, render=link, subject=高等数学, grade=大学, tags=极限|函数|核心定理}，其几何证明见[[例1.6.3：sin x / x 极限的几何证明]]{type=example, label=几何证明, render=link, tags=几何|单位圆|面积法}。

作为标准记号，该极限常被标注为：
$$
\lim_{x \to 0} \frac{\sin x}{x} = 1 \tag{1.6.1}
$$

掌握其意义、证明思路与变形应用，是理解初等函数局部行为与微分学逻辑链条的关键一环。

::: {.note}
该极限仅在**弧度制**下成立；若用角度制，结果为 $\pi/180$，故微积分中默认采用弧度。
:::