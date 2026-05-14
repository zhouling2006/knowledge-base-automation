---
title: 微元法推导y型面积公式
numeric_source: 6-2-1-5
aliases:
  - y型面积微元推导
  - 微元法推导极坐标外的y型面积
tags:
  - 高等数学
  - 定积分
  - 微元法
  - 平面图形面积
source: 第六章/第二节/一、平面图形的面积.md
position: 5
---

# 微元法推导y型面积公式

为严格建立直角坐标系下以 $y$ 为积分变量的两曲线间面积公式（即公式 (6.2.2)），我们采用**微元法三步法**进行推导：

**第一步：确定积分变量与区间**  
选取 $y$ 作为积分变量，由题设知平面图形位于直线 $y = c$ 与 $y = d$ 之间（$c < d$），故 $y \in [c, d]$。

**第二步：构造面积微元 $\mathrm{d}S$**  
在区间 $[c, d]$ 上任取一小区间 $[y, y + \mathrm{d}y]$。相应于该小区间的平面图形可近似看作一个**小矩形**（参见图6.2.2中阴影部分）：  
- 底边长度为 $\mathrm{d}y$，  
- 高度为两曲线横坐标之差 $\psi(y) - \varphi(y)$（因 $\varphi(y) \leqslant \psi(y)$）。  
因此，面积微元为：
$$
\mathrm{d}S = \left[ \psi(y) - \varphi(y) \right] \mathrm{d}y.
$$

**第三步：积分得总面积**  
将面积微元在 $[c, d]$ 上积分，即得所求平面图形的面积：
$$
S = \int_{c}^{d} \left[ \psi(y) - \varphi(y) \right] \mathrm{d}y.
$$

该推导完整体现了微元法“以直代曲、以匀代不匀”的思想，同时凸显了**积分变量选择的灵活性**——当图形在 $y$ 方向更易描述时，$y$ 型积分具有天然优势。

参考对比：[[微元法推导x型面积公式]]{type=concept, label=x型微元推导, render=link, tags=微元法|定积分|面积}  
延伸应用：[[直角坐标系下两曲线间图形面积公式(y型)]]{type=concept, label=y型面积公式, render=card, subject=高等数学, grade=大学, tags=面积|公式|直角坐标系}

::: {#proof-micro-y-001 .proof label="y型面积微元推导" type=proof}
在 $[c, d]$ 上任取小区间 $[y, y + \mathrm{d}y]$，对应图形近似为高 $\psi(y)-\varphi(y)$、底 $\mathrm{d}y$ 的矩形，得微元 $\mathrm{d}S = [\psi(y)-\varphi(y)]\mathrm{d}y$；积分即得 $S = \int_c^d [\psi(y)-\varphi(y)]\,\mathrm{d}y$。
:::

关键步骤见 ((proof-micro-y-001)){type=proof, label=y型微元推导, render=card, note=微元法三步实现}