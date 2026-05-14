---
title: 旋转体体积公式（绕x轴）
numeric_source: 6-2-2-4
aliases:
  - 圆盘法
  - x轴旋转公式
tags:
  - 高等数学
  - 定积分应用
  - 旋转体
source: 第六章/第二节/二、立体的体积.md
position: 4
---

# 旋转体体积公式（绕x轴）

设连续曲线 $y = f(x) \geq 0$、直线 $x = a$、$x = b$（$a < b$）及 $x$ 轴所围成的平面图形，绕 $x$ 轴旋转一周，所得旋转体的体积为：

$$
V = \pi \int_{a}^{b} \big[f(x)\big]^2 \,\mathrm{d}x. \tag{6.2.7}
$$

![](images/43fa353d322c46fa49216ee56d62f75bdc0691ae7b46c0de443b162bd15b2001.jpg)  
图6.2.14

### 推导（截面法特例）

- 选 $x$ 为积分变量，$x \in [a,b]$；  
- 过点 $x$ 作垂直于 $x$ 轴的平面，截旋转体得一**圆形截面**（图6.2.14阴影部分）；  
- 该圆半径恰为函数值 $f(x)$，故面积为  
  $$
  S(x) = \pi \big[f(x)\big]^2;
  $$  
- 代入一般截面公式 $V = \int_a^b S(x)\,\mathrm{d}x$，即得上式。

此法称为**圆盘法（Disk Method）**，适用于旋转轴与积分变量轴重合、且截面为实心圆的情形。

📌 **使用前提**：  
- $f(x) \geq 0$（确保无符号歧义）；  
- 曲线与 $x$ 轴围成封闭区域；  
- 旋转轴为 $x$ 轴（或平行于 $x$ 轴的直线，需平移调整）。

关联知识：  
- [[平行截面面积已知的立体体积公式]]{type=theorem, label=一般形式, render=link, tags=基础公式}  
- [[旋转体体积公式（绕y轴）]]{type=theorem, label=y轴公式, render=link, tags=旋转体|坐标变换}  
- [[例6.2.12：正弦曲线旋转体]]{type=example, id=例6.2.12, label=正弦旋转, render=card, source=教材第六章, answer=V_x=\frac{\pi^2}{2},\,V_y=2\pi^2, tags=典型例题}