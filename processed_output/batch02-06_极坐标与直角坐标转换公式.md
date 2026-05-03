---
title: 极坐标与直角坐标转换公式
aliases:
  - 坐标变换公式
  - 极直互化公式
tags:
  - 高等数学
  - 解析几何
  - 坐标系
description: 给出两种坐标系间标准转换关系，强调三角函数本质与象限修正要点。
author: 教材编写组
source: 《高等数学（上册）》第1章第4节
---
# 极坐标与直角坐标转换公式

设极坐标系的**极点与直角坐标系原点重合**，**极轴与 $x$ 轴正半轴重合**。对平面内任意一点 $P$，其直角坐标为 $(x,y)$，极坐标为 $(\rho,\varphi)$，则二者满足如下关系：

## 1. 极坐标 → 直角坐标（正向变换）

$$
\begin{cases}
x = \rho \cos \varphi, \\
y = \rho \sin \varphi.
\end{cases}
\tag{1.1.1}
$$

该式直接由三角函数定义得出，几何意义清晰：$x,y$ 是极径 $\rho$ 在 $x,y$ 轴上的投影。

## 2. 直角坐标 → 极坐标（逆向变换）

由 (1.1.1) 平方相加得：
$$
\rho^2 = x^2 + y^2 \quad \Rightarrow \quad \rho = \sqrt{x^2 + y^2} \ge 0.
$$

由两式相除（当 $x \ne 0$）得：
$$
\tan \varphi = \frac{y}{x}.
$$

⚠️ **重要说明**：$\tan \varphi = y/x$ 仅能确定 $\varphi$ 的**参考角**，实际 $\varphi$ 必须根据点 $P(x,y)$ 所在**象限**修正：
- $x > 0, y \ge 0$ → $\varphi = \arctan(y/x) \in [0,\frac{\pi}{2}]$  
- $x < 0$ → $\varphi = \arctan(y/x) + \pi$  
- $x > 0, y < 0$ → $\varphi = \arctan(y/x) + 2\pi$（或取负角）  
- $x = 0, y > 0$ → $\varphi = \frac{\pi}{2}$；$x = 0, y < 0$ → $\varphi = \frac{3\pi}{2}$

![图1.1.13：极坐标与直角坐标关系](https://cdn-mineru.openxlab.org.cn/result/2026-04-03/ccf3acff-bbac-48d8-97dd-e31ada0e3759/3cb5a3483e2aa9aad83915fc7e7fce023e2cada66f5508ac5b2632e2669130d2.jpg)

图1.1.13：坐标系重合下的几何对应

::: {#proof-polar-cartesian .proof label="转换公式的推导" type=proof}
由图1.1.13，在直角三角形 $OP_xP$ 中（$P_x$ 为 $P$ 在 $x$ 轴投影），$\cos\varphi = x/\rho$, $\sin\varphi = y/\rho$，立即得正向公式。逆向由勾股定理与三角恒等式 $\tan\theta = \sin\theta/\cos\theta$ 导出。
:::

应用场景：  
- 将直角坐标方程（如圆、直线）转化为极坐标方程（如例1.1.13：$x^2+y^2=a^2 \to \rho=a$）  
- 绘制极坐标曲线（如心形线 $\rho = a(1-\cos\varphi)$）  
- 计算极坐标下的面积、弧长等积分  

关联内容：  
- [[极坐标系定义]]{type=concept, label=基础设定, render=link, tags=坐标系|基础}  
- [[心形线]]{type=concept, label=极坐标曲线实例, render=card, tags=曲线|应用}  
- [[函数的图形定义]]{type=concept, label=极坐标下图形, render=link, tags=函数|坐标系}
```