```markdown
---
title: 例1.1.13：直角坐标方程化为极坐标方程
aliases:
  - 圆的极坐标表示
  - x²+y²=a² 的极坐标转换
tags:
  - 高等数学
  - 解析几何
  - 极坐标系
  - 坐标变换
---

# 例1.1.13：直角坐标方程化为极坐标方程

将直角坐标方程  
$$
x^{2} + y^{2} = a^{2} \quad (a > 0)
$$  
化为极坐标方程。

## 解法

利用极坐标与直角坐标的转换关系：  
$$
x = \rho \cos \varphi,\quad y = \rho \sin \varphi,
$$  
代入原方程得：  
$$
(\rho \cos \varphi)^2 + (\rho \sin \varphi)^2 = a^2,
$$  
即  
$$
\rho^2 (\cos^2 \varphi + \sin^2 \varphi) = a^2 \quad \Rightarrow \quad \rho^2 = a^2.
$$  

由于 $\rho \geq 0$（极径非负），故取正根：  
$$
\rho = a.
$$  

因此，该曲线在极坐标系下的方程为：  
$$
\rho = a \quad (a > 0).
$$

## 几何意义

方程 $\rho = a$ 表示**以极点为圆心、半径为 $a$ 的圆**。这清晰体现了极坐标对具有中心对称性的曲线（如圆、螺旋线、心形线等）的简洁表达优势。

相关知识点：[[极坐标与直角坐标的关系]]{type=concept, label=坐标转换公式, render=link, subject=高等数学, grade=大学, tags=解析几何|坐标系}

延伸思考：[[例1.1.14：心形线 ρ=a(1−cosφ) 的作图分析]]{type=example, id=例1.1.14, label=心形线绘图, render=card, source=教材例题, tags=极坐标图形|参数作图}

::: {#proof-eg1113-001 .proof label="代入推导" type=proof}
$$
\begin{aligned}
x^2 + y^2 &= (\rho \cos \varphi)^2 + (\rho \sin \varphi)^2 \\
&= \rho^2 (\cos^2 \varphi + \sin^2 \varphi) \\
&= \rho^2 \\
&= a^2 \quad \Rightarrow \quad \rho = a \quad (\rho \geq 0)
\end{aligned}
$$
:::

关键步骤见 ((proof-eg1113-001)){type=proof, label=代入推导, render=card, note=极坐标代换恒等变形}