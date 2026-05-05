---
title: 例1.1.13：直角坐标方程化为极坐标方程
aliases:
  - 圆的极坐标方程
  - x²+y²=a²的极坐标形式
tags:
  - 高等数学
  - 极坐标
  - 坐标变换
  - 曲线方程
---

# 例1.1.13：直角坐标方程化为极坐标方程

将直角坐标系下的圆方程  
$$
x^2 + y^2 = a^2 \quad (a > 0)
$$  
化为极坐标方程。

## 解法

利用极坐标与直角坐标的转换公式：  
$$
x = \rho \cos\varphi,\quad y = \rho \sin\varphi,
$$  
代入原方程得：  
$$
(\rho \cos\varphi)^2 + (\rho \sin\varphi)^2 = a^2,
$$  
即  
$$
\rho^2 (\cos^2\varphi + \sin^2\varphi) = a^2 \quad \Rightarrow \quad \rho^2 = a^2.
$$  
由于 $\rho \geq 0$（极径非负），故取正根：  
$$
\rho = a.
$$  

因此，该圆在极坐标系下的方程为：  
$$
\rho = a \quad (a > 0).
$$  

## 几何意义

此方程表示**以极点为圆心、半径为 $a$ 的圆**。极坐标形式 $\rho = a$ 简洁地刻画了“到定点（极点）距离恒为 $a$”这一几何本质，凸显了极坐标在描述中心对称曲线时的天然优势。

参考基础概念：[[极坐标系定义]]{type=concept, label=极坐标系, render=link, subject=高等数学, grade=大学, tags=坐标系|极坐标}  
坐标转换依据：[[极坐标与直角坐标转换公式]]{type=concept, label=坐标互化, render=link, tags=坐标变换|三角函数}

::: {#proof-polar-circle-001 .proof label="圆方程极坐标推导" type=proof}
由 $x = \rho \cos\varphi$, $y = \rho \sin\varphi$，代入 $x^2 + y^2 = a^2$ 得：
$$
\rho^2 \cos^2\varphi + \rho^2 \sin^2\varphi = \rho^2(\cos^2\varphi + \sin^2\varphi) = \rho^2 = a^2,
$$
因 $\rho \ge 0$，故 $\rho = a$。
:::

详细推导见 ((proof-polar-circle-001)){type=proof, label=圆方程极坐标推导, render=card, note=极坐标下圆的标准形式}