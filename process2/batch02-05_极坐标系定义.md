---
title: 极坐标系定义
aliases:
  - 极坐标
  - 极坐标表示
tags:
  - 高等数学
  - 坐标系
  - 几何基础
description: 形式化定义极坐标系的构成要素（极点、极轴、极径、极角），阐明其与直角坐标系的本质差异及一一对应条件。
---
# 极坐标系定义

在平面内取一定点 $O$（称为**极点**），由 $O$ 引一条射线 $Ox$（称为**极轴**），则平面上任意一点 $P$ 的位置可由两个量唯一确定：

- **极径** $\rho = |OP| \geq 0$：点 $P$ 到极点 $O$ 的距离；  
- **极角** $\varphi$：从极轴 $Ox$ 到射线 $OP$ 的有向角（通常取逆时针方向为正）。

有序数对 $(\rho, \varphi)$ 称为点 $P$ 的**极坐标**，记作 $P(\rho, \varphi)$（见图1.1.12）。

::: {#def-polar-001 .definition label="极坐标系公理化定义" type=definition}
- 极点 $O$ 对应所有 $(0, \varphi)$，其中 $\varphi$ 可取任意实数（约定：$(0,\varphi)$ 均表示同一点 $O$）；  
- 若限定 $\rho > 0$ 且 $\varphi \in [0, 2\pi)$（或 $(-\pi, \pi]$），则除极点外，平面上每一点与唯一一组极坐标 $(\rho,\varphi)$ 构成**一一对应**。
:::

💡 **对比直角坐标系**：  
- 直角坐标系用**位移分量** $(x,y)$ 描述位置（加法结构）；  
- 极坐标系用**距离与方向** $(\rho,\varphi)$ 描述位置（乘法/旋转结构），天然适配圆对称问题（如圆、螺线、心形线）。

延伸学习：  
- 坐标互化 → [[极坐标与直角坐标转换公式]]{type=theorem, label=互化公式, render=link, tags=坐标变换}  
- 应用实例 → [[例1.1.13-圆的极坐标方程]]{type=example, id=例1.1.13, label=ρ=a, render=card, source=教材, tags=极坐标|圆}  
- 图形绘制 → [[例1.1.14-心形线]]{type=example, id=例1.1.14, label=ρ=a(1−cosφ), render=card, source=教材, tags=极坐标|曲线}

![图1.1.12](https://cdn-mineru.openxlab.org.cn/result/2026-04-03/ccf3acff-bbac-48d8-97dd-e31ada0e3759/137e8c8eae22dbec7bfbbabac343d19cae78cb8d3ca978605e3b000b9274d0d7.jpg)  
图1.1.12 —— 极坐标系基本结构（极点 O、极轴 Ox、点 P(ρ,φ)）