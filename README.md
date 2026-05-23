# 高等数学知识库自动化

将高等数学教材自动处理成结构化知识文档，面向大一新生群体。

## 工作流程

```
教材 Markdown
    │
    ▼
┌─────────────────────┐
│   prograhspilt.py   │  细粒度切分 → 结构化 JSON
└─────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  reprocess_original.py  │  LLM 二次加工 → 独立 Markdown
└─────────────────────────┘
    │
    ▼
知识文档（frontmatter + 引用语法）
```

## 快速开始

### 1. 安装依赖

```bash
pip install openai python-dotenv
```

### 2. 配置 API Key

在项目根目录创建 `.env`：

```env
DASHSCOPE_API_KEY=你的阿里云 DashScope API Key
```

### 3. 一键运行

```bash
# 处理单个文件
python run_all.py -i "高等数学改/第一章/二、函数的概念.md"

# 批量处理整章(谨慎使用)
python run_all.py -i "高等数学改/第一章 函数、极限、连续"

# 只生成提示词（不调用 API，干跑调试）
python run_all.py --dry-run

# 调整批处理大小
python run_all.py -i "高等数学改/第一章/" --batch-size 3
```

## 核心脚本

### run_all.py — 自动化流水线（推荐）

串联 `prograhspilt.py` 和 `reprocess_original.py`，自动处理输入文件。

**参数：**

| 参数 | 说明 |
|------|------|
| `-i, --input` | 输入 `.md` 文件或目录（必填） |
| `-o, --output-root` | 最终输出根目录（默认：`processed_output/`） |
| `-s, --segments-dir` | 中间 JSON 目录（默认：`segments_output/`） |
| `-b, --batch-size` | 每批处理的 segment 数量（默认：4） |
| `--dry-run` | 只生成提示词，不调用 API |

**特性：**
- 自动跳过习题/练习/作业类文件
- 中间 JSON 统一归档到 `segments_output/`
- 最终文档按源文件分目录：`processed_output/{源文件名}/`
- 步骤2失败不中断，JSON 已保存可单独重跑

### prograhspilt.py — 细粒度切分

将 Markdown 教材按语义完整性原则切分为知识点段落，输出 JSON 数组。

**输出格式：** `{block_id, type, title, content, prerequisites}`

**JSON 示例：**

```json
{
  "block_id": "concept_060001_1746781234567",
  "type": "definition",
  "title": "函数的定义",
  "content": "设 D 是实数集...",
  "prerequisites": []
}
```

### reprocess_original.py — LLM 二次加工

将原始教材片段 + 结构化 JSON 转换为独立 Markdown 知识文档。

**参数：**

| 参数 | 说明 |
|------|------|
| `--input-md` | 原始 Markdown 文件 |
| `--input-json` | 结构化 JSON 文件 |
| `--output-dir` | 输出目录 |
| `--batch-size` | 每批处理数量（默认：4） |
| `--spec-file` | markdown-hack 规范文件（可选） |
| `--dry-run` | 只生成提示词 |

**输出：** 符合 markdown-hack 规范的独立 Markdown，含 YAML frontmatter 和 `[[...]]` 引用语法。

## 目录结构

```
F:/xschem/
├── .env                          # API Key 配置
├── run_all.py                    # 自动化流水线（入口脚本）
├── prograhspilt.py               # 细粒度切分
├── reprocess_original.py         # LLM 二次加工
├── split_all.py                  # 多级拆分（历史脚本）
├── normalize_titles.py           # 标题标准化
├── web_tool.py                   # FastAPI 网页工具
├── markdown-hack规范.md           # 文档格式规范
├── segments_output/              # 中间 JSON 归档
│   └── *.json
├── processed_output/             # 最终文档输出
│   └── {源文件名}/
│       ├── *.md
│       ├── _{源文件名}_memory.json
│       └── _{源文件名}_report.md
├── samples/                      # 参考示例文档
│   ├── 01-极限定义.md
│   └── 02-极限运算法则.md
└── 高等数学改/                    # 拆分后的教材
    ├── 第一章 函数、极限、连续/
    │   ├── 第一章 函数、极限、连续_源文件.md
    │   └── 第一节 映射与函数/
    │       ├── 一、集合和映射.md
    │       ├── 二、函数的概念.md
    │       └── ...
    └── 第二章 导数与微分/
```

## 费用估算

以一本非习题小节约 93 节、总 segment 数约 1000~1400 条估算：

| 步骤 | 费用 |
|------|------|
| prograhspilt.py 切分 | ~¥0.4 |
| reprocess_original.py 加工 | ~¥2.8 |
| rewrite 额外 | ~¥0.6 |
| **合计** | **约 ¥4~6** |

## 技术栈

- **LLM**: DashScope API（`qwen-plus` 文本改写，`text-embedding-v2` 向量嵌入）
- **接口**: OpenAI SDK 兼容
- **配置**: `.env` 文件存储 API Key

## 配置变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DASHSCOPE_API_KEY` | DashScope API Key | 必填 |
| `LLM_MODEL` | 模型名称 | `qwen-plus` |
| `BATCH_SIZE` | 批处理大小 | 4 |

## Block ID 命名规范

格式：`{type}_{6位来源编号}_{微秒时间戳}`

示例：`concept_060001_1746781234567`

类型前缀：`concept`、`theorem`、`proof`、`example`、`note`

## 数据库

知识块可存入 SQLite 数据库（`idtry.db`），主块与附属块通过 `prerequisites` 字段关联。

## 常见问题

**Q: API Key 如何获取？**
访问阿里云 DashScope 控制台（https://dashscope.console.aliyun.com/）创建 API Key。

**Q: 批量处理中断了怎么办？**
中间 JSON 已保存在 `segments_output/`，可直接重跑 `reprocess_original.py`：
```bash
python reprocess_original.py --input-json segments_output/xxx.json --input-md xxx.md
```

**Q: 如何调整输出格式？**
修改 `markdown-hack规范.md` 或在 `reprocess_original.py` 中自定义 prompt 模板。
