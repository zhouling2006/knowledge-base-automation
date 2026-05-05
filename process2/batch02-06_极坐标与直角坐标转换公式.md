---
title: 极坐标与直角坐标转换公式
aliases:
  - 坐标变换公式
  - 极直互化公式
tags:
  - 高等数学
  - 坐标系
  - 三角函数
description: 给出极坐标 $(\rho,\varphi)$ 与直角坐标 $(x,y)$ 之间的标准互化公式，强调象限修正对 $\varphi$ 的必要性。
---
# 极坐标与直角坐标转换公式

设极点 $O$ 与直角坐标系原点重合，极轴 $Ox$ 与 $x$ 轴正半轴重合（见图1.1.13）。对平面上任意非极点 $P$，其直角坐标 $(x,y)$ 与极坐标 $(\rho,\varphi)$ 满足如下关系：

### ✅ 由极坐标 → 直角坐标（正向变换）
$$
\begin{cases}
x = \rho \cos \varphi, \\
y = \rho \sin \varphi.
\end{cases}
\tag{1.1.1}
$$

### ✅ 由直角坐标 → 极坐标（逆向变换）
$$
\begin{cases}
\rho = \sqrt{x^2 + y^2} \geq 0, \\
\tan \varphi = \dfrac{y}{x} \quad (\text{需据 }x,y\text{ 符号确定 }\varphi\text{ 所在象限}).
\end{cases}
$$

::: {#thm-polar-rect-001 .theorem label="坐标互化定理" type=theorem}
设 $P$ 为平面内一点，$(x,y)$ 为其直角坐标，$(\rho,\varphi)$ 为其极坐标（$\rho \geq 0$，$\varphi \in \mathbb{R}$），则恒有：
- $\rho^2 = x^2 + y^2$；
- 若 $\rho > 0$，则 $\cos \varphi = \dfrac{x}{\rho},\ \sin \varphi = \dfrac{y}{\rho}$，从而 $\varphi$ 唯一确定于 $[0,2\pi)$ 内；
- 若 $\rho = 0$（即 $P$ 为极点），则 $\varphi$ 可取任意值。
:::

⚠️ **重要提醒**：仅凭 $\tan \varphi = y/x$ 无法唯一确定 $\varphi$！必须结合 $x$ 与 $y$ 的正负号判断象限：
- $x>0,y>0$ → 第一象限（$\varphi \in (0,\pi/2)$）  
- $x<0,y>0$ → 第二象限（$\varphi \in (\pi/2,\pi)$）  
- $x<0,y<0$ → 第三象限（$\varphi \in (\pi,3\pi/2)$）  
- $x>0,y<0$ → 第四象限（$\varphi \in (3\pi/2,2\pi)$）

应用示例：  
- 圆方程转化 → [[例1.1.13]]{type=example, id=例1.1.13, label=直角→极坐标, render=link, tags=极坐标|代数}  
- 心形线绘图 → [[例1.1.14]]{type=example, id=例1.1.14, label=极坐标→直角, render=link, tags=极坐标|几何}  
- 曲线对称性分析 → [[极坐标系定义]]{type=concept, label=对称性优势, render=card, tags=极坐标|性质}

![图1.1.13](https://cdn-mineru.openxlab.org.cn/result/2026-04-03/ccf3acff-bbac-48d8-97dd-e31ada0e3759/3cb5a3483e2aa9aad83915fc7e7fce023e2cada66f5508ac5b2632e2669130d2.jpg)  
图1.1.13 —— 极坐标与直角坐标系的叠加示意图（互化几何基础）
```