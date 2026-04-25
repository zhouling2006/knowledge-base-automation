# 高等数学知识库项目使用指南

## 项目概述

将《高等数学（上）》教材进行结构化处理，建立可查询的知识库系统。

---

## 处理流程

```
原始教材.md
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 第一步：chapterspilt.py                                      │
│ 分析目录结构，提取层级规则和章节信息                            │
│ 输出：chapter_structure.json（章节结构）                        │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 第二步：normalize_titles.py                                  │
│ 根据规则标准化全文标题层级                                     │
│ 输出：全文_标准化.md                                          │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 第三步：split_all.py                                         │
│ 多级拆分文档（一级章 → 二级节 → 三级小节）                     │
│ 输出：高等数学（上）/（完整目录结构）                           │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 第四步：prograhspilt.py                                      │
│ 将单章内容切分为细粒度知识点段落                               │
│ 输出：segments_output.json（知识点 JSON）                     │
└─────────────────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────┐
│ 第五步：build_chapter_db.py                                  │
│ 构建章节层级关系数据库                                         │
│ 输出：chapters.db（SQLite 数据库）                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 脚本说明

### 1. chapterspilt.py - 目录结构分析

| 项目 | 说明 |
|------|------|
| **功能** | 用大模型（GLM-4-Plus）分析目录，学习结构规律 |
| **输入** | `目录.md` |
| **输出** | `chapter_structure.json`（包含 `structure_summary` 和 `chapters`） |
| **规则字段** | `structure_summary.层级定义` 中每条记录含 `level`、`编号格式`（正则）、`层级名称` |

**配置文件（顶部）**：
```python
API_KEY = "04dd47f822084d5e8e8c738e60519efe.JDPMEUfQmWUqbpkk"
MODEL = "glm-4-plus"
```

---

### 2. normalize_titles.py - 标题标准化

| 项目 | 说明 |
|------|------|
| **功能** | 根据 JSON 规则标准化 Markdown 标题层级 |
| **输入** | 原始 Markdown + 规则 JSON |
| **输出** | 标准化后的 Markdown |
| **规则** | `编号格式` 正则匹配 → 指定层级（`#` 数量） |
| **不匹配** | 去除 `#` 格式保留纯文本 |

**配置文件（顶部）**：
```python
INPUT_PATH = "高等数学（上）.md"
OUTPUT_PATH = "全文_标准化.md"
RULES_JSON = "chapter_structure.json"
```

---

### 3. split_all.py - 多级拆分

| 项目 | 说明 |
|------|------|
| **功能** | 按一/二/三级标题拆分 Markdown 文件 |
| **一级** | 按 `#` 拆分章，提取目录（第二次 `# 第一章` 之前） |
| **二级** | 按 `##` 拆分节，每个节生成独立文件夹 |
| **三级** | 按 `###` 拆分小节文件 |

**配置文件（顶部）**：
```python
INPUT_PATH = "全文_标准化.md"
OUTPUT_DIR = "高等数学（上）"
```

**输出结构**：
```
高等数学（上）/
├── 第一章 函数、极限、连续/
│   ├── 第一章_源文件.md
│   ├── 第一节 映射与函数/
│   │   └── 第一节 映射与函数.md
│   ├── 第二节 数列极限/
│   │   └── 第二节 数列极限.md
│   └── ...
├── 第二章 导数与微分/
│   └── ...
└── 目录.md
```

---

### 4. prograhspilt.py - 知识点切分

| 项目 | 说明 |
|------|------|
| **功能** | 将单章内容切分为细粒度语义段落 |
| **输入** | 单个章节 Markdown |
| **输出** | JSON 数组，每条含 `textbook_id`、`chapter_id`、`segment_type`、`title`、`content`、`tags` |
| **类型** | definition（定义）、theorem（定理）、proof（证明）、example（例题）、note（说明） |

**配置文件（顶部）**：
```python
API_KEY = "04dd47f822084d5e8e8c738e60519efe.JDPMEUfQmWUqbpkk"
MODEL = "glm-4-plus"
input_path = "二、函数的概念.md"
output_path = "segments_output.json"
```

**输出 JSON 结构**：
```json
[
  {
    "textbook_id": 1,
    "chapter_id": "第一章_第一节",
    "segment_type": "definition",
    "title": "集合",
    "content": "具有某种特定性质的对象的全体称为集合...",
    "tags": "集合,定义,数学基础"
  }
]
```

---

### 5. build_chapter_db.py - 章节数据库

| 项目 | 说明 |
|------|------|
| **功能** | 将 `chapter_structure.json` 的章节信息导入 SQLite 数据库 |
| **输入** | `chapter_structure.json` |
| **输出** | `chapters.db` |

**数据库结构**：
```sql
CREATE TABLE chapters (
    id        INTEGER PRIMARY KEY,
    level     INTEGER,      -- 层级（0=书名, 1=章, 2=节, 3=小节）
    number    TEXT,         -- 编号（"第一章"、"第一节"、"一、"）
    title     TEXT,        -- 标题
    parent_id INTEGER       -- 父级 ID
);
```

---

## 数据文件说明

| 文件 | 说明 |
|------|------|
| `chapter_structure.json` | 章节结构分析结果（层级规则 + 章节列表） |
| `chapter_structure.json` | 章节结构分析结果（层级规则 + 章节列表） |
| `chapters.db` | 章节层级关系数据库（SQLite） |
| `segments_output.json` | 原始知识点切分结果 |
| `segments_output_pretty.json` | 格式化知识点切分结果 |
| `segments_output_pretty_cleaned.json` | 清理后的知识点（去换行） |

---

## 文档说明

| 文件 | 说明 |
|------|------|
| `高等数学（上）.md` | 原始教材全文 |
| `全文_标准化.md` | 标题标准化后的完整教材 |
| `目录.md` | 提取的教材目录 |
| `二、函数的概念.md` | 手动拆分出的单个章节 |
| `高等数学（上）/` | 多级拆分后的完整目录（176个文件） |

---

## 快速开始

### 完整流程（从原始教材开始）

```bash
# 1. 确保有目录.md和教材全文

# 2. 分析目录结构
python chapterspilt.py

# 3. 标准化标题
python normalize_titles.py

# 4. 多级拆分
python split_all.py

# 5. 对单个章节切分知识点（示例）
# 编辑 prograhspilt.py 的 input_path
python prograhspilt.py

# 6. 构建章节数据库
python build_chapter_db.py
```

### 单独使用某个脚本

每个脚本顶部都有配置区，直接修改对应变量：

```python
# normalize_titles.py
INPUT_PATH = "你的教材.md"
OUTPUT_PATH = "标准化后.md"
RULES_JSON = "chapter_structure.json"
```

---

## 注意事项

1. **API Key**：涉及大模型的脚本需要有效的智谱 AI API Key
2. **章节匹配规则**：`chapter_structure.json` 中的 `编号格式` 是正则表达式，可手动调整
3. **拆分容错**：一级拆分找不到目录时，会直接处理整个文件
4. **编码**：所有脚本已处理 Windows UTF-8 输出

---

## 层级匹配规则

当前项目的正则规则（来自 `chapter_structure.json`）：

| 层级 | 编号格式 | 层级名称 |
|------|----------|----------|
| 1 | `第[一二三四五六]章` | 章 |
| 2 | `第[一二三四五六七八九十]节` | 节 |
| 3 | `[一二三四五六七八九十]+、` | 小节 |
| 3 | `习题[0-9]+\.[0-9]+` | 习题 |
| 3 | `实验.*` | 实验 |
| 3 | `附录[0-9]+` | 附录 |
| 3 | `参考答案` | 参考答案 |
| 3 | `参考文献` | 参考文献 |
