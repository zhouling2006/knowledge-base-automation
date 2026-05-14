---
title: k阶无穷小示例
numeric_source: 1-4-2-6
aliases: []
tags:
  - 高等数学
  - 无穷小
  - 示例
source: 第一章/第四节 无穷小与无穷大.md
position: 6
---

# k阶无穷小示例

以下实例验证定义1.7.2的实际应用：

- 当 $x \to 0$ 时，$1 - \cos x$ 是关于 $x$ 的**二阶无穷小**。  
  因为  
  $$
  \lim_{x \to 0} \frac{1 - \cos x}{x^2} = \frac{1}{2} \neq 0,
  $$  
  故满足 $k = 2$，$c = \frac{1}{2}$。

- 当 $x \to x_0$ 时，函数 $5(x - x_0) + 3(x - x_0)^3$ 是关于 $(x - x_0)$ 的**一阶无穷小**。  
  因为  
  $$
  \lim_{x \to x_0} \frac{5(x - x_0) + 3(x - x_0)^3}{(x - x_0)^1} = \lim_{x \to x_0} \left[5 + 3(x - x_0)^2\right] = 5 \neq 0,
  $$  
  故 $k = 1$，$c = 5$。

> ✅ **关键观察**：主导项决定阶数——高次项在极限下可忽略，主部（lowest-order nonzero term）决定阶。

延伸思考：若考虑 $f(x) = (x - x_0)^2 \ln|x - x_0|$（$x \to x_0$），它是否属于某整数阶无穷小？[[无穷小比较的动机与直观背景.md]]{type=concept, label=快慢差异本质, render=link, tags=无穷小|动机}