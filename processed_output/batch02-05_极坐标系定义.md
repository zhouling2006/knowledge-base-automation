---
title: 极坐标系定义
aliases:
  - 极坐标
  - 极坐标表示
tags:
  - 高等数学
  - 解析几何
  - 坐标系
description: 构建极坐标系的公理化定义，阐明极点、极轴、极径、极角的几何含义与约定。
author: 教材编写组
source: 《高等数学（上册）》第1章第4节
---
# 极坐标系定义

## 基本构成

在平面内选定一个定点 $O$（称为**极点**），并从 $O$ 引出一条射线 $Ox$（称为**极轴**），则由此构成一个**极坐标系**。

对平面内任意一点 $P$（$P \ne O$），其位置由两个量唯一确定：
- **极径** $\rho = |OP| \ge 0$：点 $P$ 到极点 $O$ 的距离；
- **极角** $\varphi$：以极轴 $Ox$ 为始边、射线 $OP$ 为终边的**有向角**（通常取弧度制）。

有序实数对 $(\rho, \varphi)$ 称为点 $P$ 的**极坐标**，记作 $P(\rho, \varphi)$。

## 特殊约定与唯一性

| 情形 | 规定 | 说明 |
|------|------|------|
| **极点 $O$** | $\rho = 0$，$\varphi$ 可取任意实数 | 即 $(0,\varphi)$ 对所有 $\varphi$ 均表示同一点 $O$ |
| **非极点 $P$** | 通常限定 $\rho > 0$，且 $\varphi \in [0, 2\pi)$（或 $(-\pi, \pi]$） | 此时除极点外，**点与极坐标一一对应** |

> ⚠️ 注意：若不限定 $\rho \ge 0$ 或 $\varphi$ 范围，则同一 $P$ 可有无穷多种极坐标表示，例如 $P(2,\frac{\pi}{3}) = (2,\frac{7\pi}{3}) = (-2,\frac{4\pi}{3})$。

![图1.1.12：极坐标系示意图](https://cdn-mineru.openxlab.org.cn/result/2026-04-03/ccf3acff-bbac-48d8-97dd-e31ada0e3759/137e8c8eae22dbec7bfbbabac343d19cae78cb8d3ca978605e3b000b9274d0d7.jpg)

图1.1.12：极点 $O$、极轴 $Ox$、点 $P(\rho,\varphi)$ 的几何关系

::: {#note-polar-uniqueness .note label="极坐标的多值性与主值" type=concept}
极坐标本质上是**非单射映射**：$(\rho,\varphi) \mapsto P$。为便于计算与绘图，常取**主值分支**（principal value）：$\rho \ge 0$, $\varphi \in [0,2\pi)$。这与复数的极坐标表示完全一致。
:::

延伸知识：  
- [[极坐标与直角坐标转换公式]]{type=theorem, label=坐标互化, render=card, tags=坐标系|变换}  
- [[函数的图形定义]]{type=concept, label=极坐标下图形, render=link, tags=函数|坐标系}  
- [[心形线]]{type=concept, label=极坐标曲线范例, render=link, tags=曲线|极坐标}