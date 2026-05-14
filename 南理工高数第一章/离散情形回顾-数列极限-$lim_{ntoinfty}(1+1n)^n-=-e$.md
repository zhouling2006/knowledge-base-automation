---
title: 离散情形回顾：数列极限 $\lim_{n\to\infty}(1+1/n)^n = e$
numeric_source: 1-6-2-2
aliases:
  - 数列形式的重要极限
  - e的数列定义
tags:
  - 高等数学
  - 数列极限
  - 单调有界准则
  - 自然常数
source: 第一章/第六节/二、重要极限 \(\lim_{x\to \infty}\left(1 + \frac{1}{x}\right)^x = e\).md
position: 2
---

# 离散情形回顾：数列极限 $\lim_{n\to\infty}(1+1/n)^n = e$

本章第二节已严格证明如下**数列极限**：

$$
\lim_{n \to \infty} \left(1 + \frac{1}{n}\right)^n = e.
$$

该结论的证明依赖于**单调有界准则**：  
- 序列 $a_n = \left(1 + \frac{1}{n}\right)^n$ 单调递增；  
- 序列有上界（例如可证 $a_n < 3$）；  
- 故极限存在，记为 $e$，并赋予其自然对数的底数含义。

此数列极限是本节连续极限的**理论源头与逻辑前提**。它为将整数下标 $n$ 推广至实变量 $x$ 提供了坚实依据——没有该离散结果的成立，连续情形的极限就缺乏锚点。

> 🔗 **承上启下作用**：  
> - 是[[重要极限 $\lim_{x\to \infty}\left(1 + \frac{1}{x}\right)^x = e$]]{type=concept, label=核心极限, render=link, tags=重要极限|e} 的离散原型；  
> - 是[[例1.6.8：证明 $\lim_{x\to +\infty}(1+1/x)^x = e$（夹逼法）]]{type=example, id=例1.6.8, label=夹逼法基础, render=link, tags=证明|数列应用} 中构造不等式链的直接依据。

延伸阅读：  
- [[单调有界准则]]{type=concept, label=收敛判别法, render=link, subject=高等数学, tags=数列|极限|收敛性}  
- [[自然常数 $e$ 的多种定义方式]]{type=concept, label=e的定义谱系, render=card, tags=常数|定义|分析基础}