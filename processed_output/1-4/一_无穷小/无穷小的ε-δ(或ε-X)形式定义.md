---
title: 无穷小的ε-δ（或ε-X）形式定义
numeric_source: 1-4-1-4
aliases:
  - ε-δ定义
  - ε-X定义
tags:
  - 高等数学
  - 极限
  - 无穷小
  - 严格定义
source: 第一章/第四节 无穷小与无穷大.md
position: 4
---

# 无穷小的ε-δ（或ε-X）形式定义

无穷小的严格定义源于极限的 $\varepsilon$-$\delta$（或 $\varepsilon$-$X$）语言，是对“极限为 0”的精确刻画：

> 若对任意给定的正数 $\varepsilon > 0$，  
> - 存在正数 $\delta > 0$，使得当 $0 < |x - x_0| < \delta$ 时，恒有 $|f(x)| < \varepsilon$，  
>   则称 $f(x)$ 是当 $x \to x_0$ 时的无穷小；  
> - 或存在正数 $X > 0$，使得当 $|x| > X$ 时，恒有 $|f(x)| < \varepsilon$，  
>   则称 $f(x)$ 是当 $x \to \infty$ 时的无穷小。

该定义强调：**函数值的绝对值可被任意预先指定的正数 $\varepsilon$ 所控制**，只要自变量足够接近 $x_0$（或足够远离原点）。

🔍 对比理解：  
- 此即 $\lim\limits_{x \to x_0} f(x) = 0$ 的 $\varepsilon$-$\delta$ 表述；  
- 与一般极限定义相比，此处极限值 $L = 0$，故不等式简化为 $|f(x)| < \varepsilon$（无需减去 $L$）。

延伸阅读：  
- [[极限的ε-δ定义]]{type=concept, label=一般极限, render=link, subject=高等数学, grade=大学, tags=极限|严格化}  
- [[无穷小的性质]]{type=concept, label=运算封闭性, render=link, tags=高数|极限}  
- [[函数极限与无穷小的关系]]{type=concept, label=充要条件, render=link, tags=高数|极限|结构定理}