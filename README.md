# 高等数学知识库

基于大模型的高等数学教材知识库构建工具集，支持章节结构解析、知识点切分、概念库构建和语义标注。

## 环境配置

### 1. 安装依赖

```bash
pip install zhipuai sentence-transformers python-dotenv
```

### 2. 配置 API Key

创建 `.env` 文件（参考 `.env.example`）：

```bash
ZHIPU_API_KEY=你的智谱AI密钥
```

## 项目结构

```
├── 目录.md                      # 教材原始目录
├── chapter_structure.json       # 章节结构（由 chapterspilt.py 生成）
├── chapters.db                  # 章节数据库
├── 高等数学（上）.md              # 原始教材全文
├── 全文_标准化.md                # 标准化后的教材
│
├── chapterspilt.py              # 目录解析：提取章节结构
├── build_chapter_db.py          # 构建章节数据库
│
├── split_segment.py             # 知识点切分（单文件）
├── prograhspilt.py              # 知识点切分（单文件，支持查找section_id）
│
├── build_concept_db.py          # 构建概念库数据库
├── query_concepts.py           # 概念库查询
├── align_aliases.py             # 别名对齐（向量 + LLM）
│
├── annotate_md.py               # 概念标注（在 Markdown 中标注概念）
│
├── normalize_titles.py          # 标题标准化工具
└── split_all.py                 # 批量切分脚本
```

## 工作流程

### 阶段一：章节结构解析

```bash
# 1. 解析目录，生成章节结构 JSON
python chapterspilt.py

# 2. 构建章节数据库
python build_chapter_db.py
```

**chapterspilt.py** - 分析目录结构规律，自动识别层级关系，输出结构化 JSON：
- `structure_summary`: 层级数量、编号格式
- `chapters`: 每个条目的编号、标题、父级关系

**build_chapter_db.py** - 将 JSON 转换为 SQLite 数据库：
- 支持无限层级嵌套
- 自动建立父子关系

### 阶段二：教材标准化

```bash
# 标准化教材标题格式
python normalize_titles.py
```

将教材标题统一为"第X节 / X、"格式，调整章节层次，便于后续处理。

### 阶段三：知识点切分

```bash
# 单文件切分
python split_segment.py -i "二、函数的概念.md" -s "二、函数的概念.md" --section "函数的概念"

# 支持自动查找 section_id
python prograhspilt.py -i "二、函数的概念.md" -s "二、函数的概念.md" --section "函数的概念"
```

**输出字段说明**：

| 字段 | 说明 |
|------|------|
| `source` | 来源文件路径 |
| `section` | 所属小节名 |
| `section_id` | 章节数据库中的小节 ID |
| `position` | 在当前章节内的顺序号 |
| `title` | 本块标题 |
| `content` | 语义压缩后的核心内容 |
| `raw_content` | 原文内容 |
| `type` | 类型：concept(概念)/theorem(定理)/proof(证明)/example(例题)/note(说明) |
| `aliases` | 本块中概念的别名/同义词 |
| `entities` | 涉及的关键实体名词 |
| `references` | 含关系连接词的原文语句 |
| `confidence` | 置信度 (0-1) |
| `needs_review` | 是否需要人工审核 |
| `summary` | 一句话摘要 |

### 阶段四：构建概念库

```bash
# 构建概念库（增量模式）
python build_concept_db.py

# 强制重建
python build_concept_db.py --rebuild
```

**build_concept_db.py** 从切分结果中：
- 提取 `type` 为 concept/definition/theorem 的条目作为标准概念
- 提取所有别名和实体名词
- 生成文本向量（使用 shibing624/text2vec-base-chinese）

**数据库结构**：

| 表名 | 说明 |
|------|------|
| `concepts` | 标准概念库 |
| `aliases` | 别名/实体表（含状态：pending/auto_mapped/llm_confirmed/needs_review） |
| `metadata` | 元数据 |

### 阶段五：别名对齐

```bash
# 自动对齐别名到概念
python align_aliases.py
```

**对齐策略**：
- **别名 (alias)**：直接向量相似度匹配
- **实体 (entity)**：向量相似度 + LLM 二次判断
- 低于阈值或 LLM 判断不匹配的条目标记为 `needs_review`，待人工审核

### 阶段六：概念标注

```bash
# 基础用法（文末添加注释表）
python annotate_md.py 二、函数的概念.md

# 指定输出文件
python annotate_md.py 二、函数的概念.md --output 标注版.md

# 内联标注（直接替换原文）
python annotate_md.py 二、函数的概念.md --inline
```

使用 AC 自动机快速匹配已对齐的别名，在 Markdown 文件中标注文中出现的概念。

## 数据库

### chapters.db - 章节数据库

```sql
CREATE TABLE chapters (
    id        INTEGER PRIMARY KEY,
    level     INTEGER,      -- 层级（0=根节点，1=章，2=节，3=小节）
    number    TEXT,         -- 编号
    title     TEXT,         -- 标题
    parent_id INTEGER       -- 父节点 ID
);
```

### concept_base.db - 概念库

```sql
-- 标准概念表
CREATE TABLE concepts (
    concept_id TEXT PRIMARY KEY,
    name       TEXT,
    file_path  TEXT,
    title      TEXT,
    content    TEXT,
    concept_type TEXT,     -- concept/definition/theorem
    created_at TEXT,
    embedding  BLOB
);

-- 别名/实体表
CREATE TABLE aliases (
    alias       TEXT PRIMARY KEY,
    block_id    INTEGER,
    concept_id  TEXT,
    alias_type  TEXT,       -- alias/entity/concept
    source_doc  TEXT,
    confidence  REAL,
    status      TEXT,      -- pending/auto_mapped/llm_confirmed/needs_review
    llm_reason  TEXT,
    created_at  TEXT,
    embedding   BLOB,
    FOREIGN KEY (concept_id) REFERENCES concepts(concept_id)
);
```

## 概念库查询

```bash
python query_concepts.py
```

交互式查询：
- 查看所有概念
- 查看所有别名/实体
- 查看待审核项
- 语义搜索概念
- 搜索别名/实体
- 人工指定概念关联

## 配置说明

### 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `ZHIPU_API_KEY` | 智谱 AI API 密钥 | 是 |


### 模型配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| LLM 模型 | `glm-4-plus` | 用于知识点切分 |
| LLM 辅助模型 | `glm-4-flash` | 用于别名对齐判断 |
| 向量模型 | `shibing624/text2vec-base-chinese` | 中文文本向量化 |
| 向量阈值 | `0.75` | 别名对齐相似度阈值 |

## 依赖

- Python 3.8+
- `zhipuai` - 智谱 AI SDK
- `sentence-transformers` - 文本向量化
- `python-dotenv` - 环境变量管理
