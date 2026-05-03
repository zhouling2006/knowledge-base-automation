```markdown
---
title: 函数的图形定义
aliases:
  - 函数图像
  - 函数曲线
tags:
  - 高等数学
  - 函数
  - 解析几何
description: 定义函数图形的集合论与几何本质，强调单值性在图像中的体现。
author: 教材编写组
source: 《高等数学（上册）》第1章第2节
---
# 函数的图形定义

设有函数 $y = f(x),\ x \in D$。在平面直角坐标系 $xOy$ 中，称所有满足  
$$
\{M(x, y) \mid y = f(x),\ x \in D\}
$$  
的点 $M(x, y)$ 构成的集合为函数 $y = f(x)$ 的**图形**。

该图形在几何上通常表现为一条或若干条曲线（包括直线），其核心性质由函数的**单值性**保证：  
> 任一平行于 $y$ 轴的直线（即形如 $x = x_0$ 的竖直线）与函数图形至多相交于一点。

这一性质是函数区别于一般二元关系（如圆方程 $x^2 + y^2 = R^2$）的关键几何判据。

![图1.1.6](https://cdn-mineru.openxlab.org.cn/result/2026-04-03/ccf3acff-bbac-48d8-97dd-e31ada0e3759/af05a55ae335dca7218b3621c474f94bce4a6522d38e591b66f2d8a7b7f4587c.jpg)

图1.1.6：函数图形示意图（单值性可视化）

::: {#note-graph-uniqueness .note label="单值性与垂直线检验" type=concept}
该几何特征常被称为**垂直线检验法（Vertical Line Test）**：若某平面图形被某条竖直线穿过两点及以上，则它**不能**表示一个（单值）函数。
:::

延伸阅读：  
- [[函数的定义]]{type=concept, label=函数本质, render=link, subject=高等数学, grade=大学, tags=函数|基础概念}  
- [[多值函数与单值分支]]{type=concept, label=多值情形, render=card, tags=函数|拓展}  
- [[分段函数]]{type=concept, label=分段图形, render=link, tags=函数|特殊类型}