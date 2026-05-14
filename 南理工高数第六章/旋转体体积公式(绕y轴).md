---
title: 旋转体体积公式（绕y轴）
numeric_source: 6-2-2-5
aliases:
  - y轴圆盘法
tags:
  - 高等数学
  - 积分应用
  - 旋转体
  - 体积计算
source: 第六章/第二节/二、立体的体积.md
position: 5
---

# 旋转体体积公式（绕y轴）

由连续曲线 $x = \varphi(y)$（其中 $\varphi(y) \geqslant 0$）、直线 $y = c$、$y = d$（$c < d$）及 $y$ 轴所围成的平面图形，绕 $y$ 轴旋转一周所得旋转体，其垂直于 $y$ 轴的截面为圆形，半径为 $\varphi(y)$，面积为  
$$
S(y) = \pi\, \varphi^2(y).
$$  
因此，该旋转体的体积为：

$$
V = \pi \int_{c}^{d} \varphi^2(y)\, \mathrm{d}y. \tag{6.2.8}
$$

此公式称为 **y方向圆盘法**（或“垂直于y轴的圆盘法”），适用于以 $y$ 为自变量、边界函数显式表示为 $x = \varphi(y)$ 的情形。

> ✅ 对比参考：  
> - [[旋转体体积公式(绕x轴)]]{type=concept, label=绕x轴圆盘法, render=link, tags=高数|积分应用|旋转体}  
> - [[平行截面面积已知的立体体积公式]]{type=concept, label=一般截面法, render=link, subject=高等数学, grade=大学, tags=体积|积分}

![](images/b2e88c4c852c134901c81c8b3d284dce66b265d42ae6a790bc642e7ea870699d.jpg)  
图6.2.15

::: {.note}
该公式是[[平行截面面积已知的立体体积公式]]{type=concept, label=截面法通式, render=link}在旋转对称情形下的特例：当截面恒为圆且半径由 $\varphi(y)$ 给出时，$S(y) = \pi \varphi^2(y)$，代入即得。
:::