# 高等数学知识库

基于大模型的高等数学教材知识库构建工具集，支持章节结构解析、知识点切分、概念库构建和语义标注。

## 环境配置

### 1. 安装依赖

```bash
pip install openai numpy python-dotenv
```

### 2. 配置 API Key

创建 `.env` 文件（参考 `.env.example`）：

```bash
DASHSCOPE_API_KEY=你的阿里云DashScope密钥
```

### 阶段七：二次加工原文

```bash
# 基本用法（使用默认路径）
python reprocess_original.py

# 指定输入输出
python reprocess_original.py \
  --input-md "二、函数的概念.md" \
  --input-json "segments_output_pretty.json" \
  --output-dir "processed_output"

# 只生成提示词，不调用 API（调试用）
python reprocess_original.py --dry-run

# 调整批次大小（默认每批 6 个 segment）
python reprocess_original.py --batch-size 4
```

**功能说明**：通过 LLM（qwen-plus）将 `segments_output.json` 中的每个 segment 二次加工，输出符合 [markdown-hack 规范](https://github.com/zhouling2006/markdown-hack) 的独立 Markdown 文档。

**输出特性**：
- YAML frontmatter（`title`、`type`、`tags`、`aliases`、`related`、`section`）
- 引用语法 `[[页面名]]{key=value}`
- Pandoc 语义块 `:::{ .proof / .example / .note }:::`
- 图片资源统一放在 `./assets/`

**输入文件**：
| 文件 | 说明 |
|------|------|
| `二、函数的概念.md` | 原始教材 Markdown |
| `segments_output_pretty.json` | 结构化切分结果（由阶段三生成） |
| `samples/*.md` | 参考示例（few-shot prompt） |
| `markdown-hack规范.md` | 输出格式规范 |

**后续改进方向**：
1. 提示词中引入批次间 memory 上下文，使 LLM 能利用前面的处理结果
2. 解决分隔符 `---SPLIT---` 被省略的问题，增加 LLM 二次修正环节
3. 扩充训练集/示例文档，提升输出质量一致性
4. 将硬编码绝对路径改为配置化

---

## 项目结构

```
├── 目录.md                      # 教材原始目录
├── chapter_structure.json       # 章节结构（由 chapterspilt.py 生成）
├── chapters.db                  # 章节数据库
├── 高等数学（上）.md              # 原始教材全文
├── 全文_标准化.md                # 标准化后的教材
├── segments_output_pretty.json # 结构化切分结果
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
├── reprocess_original.py        # 二次加工原文（LLM 生成规范 Markdown）
├── samples/                     # 参考示例文档（few-shot）
├── processed_output/            # 二次加工输出目录
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
- 生成文本向量（使用 DashScope text-embedding-v2，1536维）

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
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API 密钥（通义千问） | 是 |


### 模型配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| LLM 模型 | `qwen-plus` | 用于知识点切分、实体对齐判断 |
| 向量模型 | `text-embedding-v2` | DashScope 中文文本向量化（1536维） |
| 向量阈值 | `0.65` | 别名对齐相似度阈值 |

## 依赖

- Python 3.8+
- `openai` - DashScope API 调用
- `numpy` - 向量计算
- `python-dotenv` - 环境变量管理

---

## 附录：多路召回对齐策略（待实现）

当前实体对齐仅使用向量相似度 + LLM 判断，未来可引入多路召回提升准确率。

### 改进思路

参考 RAG 多路召回架构，将单一向量匹配扩展为多维度加权融合：

```
综合得分 = 向量相似度 × (1 + TF-IDF关键词相关度)
```

**核心公式**：
- **向量相似度**：整体语义匹配（已有）
- **TF-IDF 关键词相关度**：文本中的关键词与概念的匹配程度

```
TF-IDF(关键词|文本) × TF-IDF(关键词|概念) = 关键词对文本和概念的联合相关度
```

**为什么有用**：
- 向量相似度一般，但关键词高度匹配 → 提升置信度
- 向量相似度很高，但关键词几乎不相关 → 降权/需要人工审核

### 方案设计

| 得分区间 | 动作 | LLM 调用 |
|----------|------|----------|
| **> 0.85** | 直接关联 | ❌ |
| **0.6~0.85** | Top-3 候选队列 | ⚠️ 可选 |
| **< 0.6** | LLM 仲裁 | ✅ |

### 实现方向

1. **TF-IDF 计算**：对文本段和概念库建立 TF-IDF 索引，计算关键词匹配度
2. **加权融合**：将向量相似度与 TF-IDF 相关度相乘，得到综合得分
3. **分层决策**：根据综合得分决定直接关联、候选队列或 LLM 仲裁

### 优势

- 减少 LLM API 调用次数（成本优化）
- 提高精确度（多维度信号交叉验证）
- 可解释性强（各维度得分透明可见）
- 灵活可调（权重可针对不同场景优化）
