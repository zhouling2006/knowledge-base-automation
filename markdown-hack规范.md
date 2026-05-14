# markdown-hack规范

## 1. 目标

本规范用于指导生成可扩展的 markdown 文档。

重点支持：

- 文档级 `doc-metadata`
- 多别名
- 多标签
- 页面引用与块引用
- 在引用中附加结构化信息，用于题目引用、知识点引用等场景

## 2. doc-metadata 规范

每个文档顶部应使用 frontmatter 表达 `doc-metadata`。

推荐格式：

```yaml
---
title: 极限的定义
numeric_source: 1-1-1-1
aliases:
  - 函数极限定义
  - 极限基础定义
tags:
  - 高等数学
  - 极限
  - 基础概念
---
```

### 2.1 字段定义

- `title`: 文档主标题，必须为单个字符串
- `numeric_source`: 文档编号，格式为 `章-节-小节-序号`（如 `1-1-1-3`），必须为单个字符串
- `aliases`: 文档别名列表，必须为字符串数组
- `tags`: 文档标签列表，必须为字符串数组

### 2.2 约定

- `title` 必填
- `aliases` 可选，未填写时可省略
- `tags` 可选，未填写时可省略
- `aliases` 与 `tags` 都应写为数组，即使只有一个值
- 标签建议使用短语，不建议写成长句

### 2.3 额外拓展（可选字段）

- `description`: 文档描述，必须为单个字符串
- `author`: 文档作者，必须为单个字符串
- `date`: 文档创建日期，必须为单个字符串
- `updated`: 文档更新日期，必须为单个字符串
- `source`: 文档来源，必须为单个字符串
- `version`: 文档版本，必须为单个字符串

若有其他需要的额外拓展字段，请单独写一份"文档拓展字段.md"文件。

## 3. 基础引用语法

兼容 logseq 风格：

- `[[页面名]]` 表示页面引用
- `((块ID))` 表示块引用（引用已定义的语义块）

示例：

```md
参考 [[极限的定义]]
证明过程见 ((block-limit-20260403-001))
```

### 3.1 语义块定义语法（Pandoc风格）

块定义使用 fenced div 风格：

```md
::: {#proof-limit-001 .proof label="定义推导" type=proof}
这里是一段完整推导，可包含多段文本、列表、公式。
:::
```

说明：

- `#proof-limit-001` 定义块 ID（供 `((proof-limit-001))` 引用）
- `.proof` 定义块 class（可多个）
- `label="定义推导"`、`type=proof` 是块元数据
- 语义块是“有边界的大块”，不是单行锚点

## 4. 引用扩展 hack

为了让引用携带附加信息，在基础引用外增加元信息尾部。

统一写法：

```md
[[引用目标]]{key=value, key=value}
((引用目标)){key=value, key=value}
```

说明：

- 前半部分仍然是标准引用主体
- 后半部分 `{...}` 为扩展信息区
- 扩展信息使用 `key=value` 形式
- 多个字段之间使用英文逗号分隔

## 5. 扩展字段约定

### 5.1 必填字段

- `type`: 引用类型

### 5.2 可选字段

- `label`: 展示名称
- `render`: 渲染方式，如 `link`、`card`
- `id`: 外部编号或题号
- `tags`: 引用级标签，多个值用 `|` 分隔
- `note`: 补充说明

### 5.3 保留扩展字段

- 允许增加未预定义字段
- 未识别字段应原样保留，供后续扩展

### 5.4 约定

- `render` 未填写时，默认按 `link` 处理

示例：

```md
[[极限的定义]]{type=concept, label=函数极限, render=link, tags=高数|极限}
((block-limit-20260403-001)){type=proof, render=card, note=极限定义证明}
```

## 6. 题目引用

当引用目标是题目时，`type` 应设为 `question`。

必填字段：

- `type=question`

可选字段：

- `id`: 题号
- `label`: 题目简称
- `render`: 渲染方式，如 `link`、`card`
- `source`: 来源
- `answer`: 答案或结论
- `tags`: 题目标签

示例：

```md
[[同济高数习题-极限-例1]]{type=question, id=例1, label=极限计算基础题, render=card, source=同济高数, answer=1, tags=高数|极限|计算题}
```

## 7. 知识点引用

当引用目标是知识点时，`type` 应设为 `concept`。

必填字段：

- `type=concept`

可选字段：

- `label`: 知识点简称
- `render`: 渲染方式，如 `link`、`card`
- `subject`: 学科
- `grade`: 学段或年级
- `tags`: 知识点标签

示例：

```md
[[极限的定义]]{type=concept, label=函数极限, render=link, subject=高等数学, grade=大学, tags=极限|核心概念}
```

## 8. 推荐解析原则

- 先扫描 `::: {#id ...}` 到 `:::` 的语义块定义，构建 block 索引
- 若只有 `[[...]]` 或 `((...))`，按普通引用处理
- 若引用后紧跟 `{...}`，则按增强引用处理
- `type` 用于区分语义类型
- `render` 未填写时，解析为 `link`
- 未识别字段可保留，供后续扩展
- `tags` 在引用扩展中使用 `|` 分隔多个值，避免与字段分隔逗号冲突

## 9. 图像资源规范

若文档有图像需求，图片文件应放在该 markdown 同级目录的 `assets` 子目录。

路径写法统一为相对路径：

```md
![说明文本](./images/xxx.png)
```

约定：

- 不使用绝对路径
- 不跨目录回溯（如 `../`）引用图片
- 文件名建议使用英文、小写、连字符或数字

示例：

```md
![线性代数封面](./images/image1.jpg)
```

## 10. 推荐示例

```md
---
title: 极限基础整理
numeric_source: 1-1-1-0
aliases:
  - 高数极限总结
tags:
  - 高等数学
  - 极限
---

本节先看知识点 [[极限的定义]]{type=concept, label=函数极限, render=link, subject=高等数学, grade=大学, tags=极限|核心概念}。

::: {#proof-limit-20260403-001 .proof label="极限定义证明过程" type=proof}
取任意 \(\varepsilon > 0\)，构造 \(\delta > 0\)，证明当 \(0<|x-x_0|<\delta\) 时有 \(|f(x)-L|<\varepsilon\)。
:::

对应例题见 [[同济高数习题-极限-例1]]{type=question, id=例1, label=极限计算基础题, render=card, source=同济高数, answer=1, tags=高数|极限|计算题}。

详细推导参考 ((block-limit-20260403-001)){type=proof, render=card, note=极限定义证明过程}。
```
