---
title: 函数的定义
aliases:
  - 映射
  - 单值映射
  - 实函数
tags:
  - 高等数学
  - 函数
  - 基础概念
description: 函数是定义在非空实数集上的单值映射，由定义域与对应法则唯一确定。
---

# 函数的定义

设非空数集 $D \subseteq \mathbf{R}$，则称映射 $f: D \to \mathbf{R}$ 为定义在 $D$ 上的**函数**，记作  
$$
y = f(x),\quad x \in D,
$$  
其中：

- $x$ 称为**自变量**，  
- $y$ 称为**因变量**，  
- $D$ 称为**定义域**，记作 $D_f = D$，  
- 当 $x$ 取定某值 $x_0 \in D$ 时，对应的唯一值 $y_0 = f(x_0)$ 称为函数在 $x_0$ 处的**函数值**，  
- 全体函数值构成的集合称为**值域**，记作  
  $$
  R_f = \{ y \mid y = f(x),\, x \in D \}.
  $$

函数中表示对应关系的记号 $f$ 可用其他字母替代，如 $\varphi, F, g$ 等；即 $y = \varphi(x),\, y = F(x),\, y = g(x)$ 等均表示函数。

> **关键性质**：在标准函数定义中，对每个 $x \in D$，其函数值 $y$ **必须唯一**。满足此条件者称为**单值函数**。若对应法则对某些 $x$ 给出多个 $y$，则称为**多值函数**——它不直接属于本课程默认讨论对象，但可通过分解为若干**单值分支**进行研究（参见 [[多值函数与单值分支]]{type=concept, label=多值函数分解, render=link, tags=函数|隐函数}）。

::: {#note-function-elements .note label="函数的两大要素" type=note}
函数由**定义域**与**对应法则**共同决定；值域是二者自然导出的结果。二者缺一不可，且共同构成函数相等性的判定依据（详见 [[函数的两大要素与相等性]]{type=concept, label=函数相等条件, render=link, tags=函数|逻辑基础}）。
:::

参考延伸：  
- [[多值函数与单值分支]]{type=concept, label=多值函数示例, render=card, subject=高等数学, grade=大学, tags=函数|隐函数}  
- [[函数的两大要素与相等性]]{type=concept, label=函数同一性判定, render=link, tags=函数|逻辑基础}  
- [[例1.1.5：求根式分式函数的定义域]]{type=question, id=例1.1.5, label=定义域计算题, render=card, source=教材例题, answer=(-∞,1] ∪ [2,3) ∪ (4,+∞), tags=函数|定义域|计算题}