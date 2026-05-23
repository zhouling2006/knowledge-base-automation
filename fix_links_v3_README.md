# fix_links_v3 使用说明

## 环境配置

```bash
# 设置 DashScope API Key（必需，否则 LLM 不可用）
export DASHSCOPE_API_KEY=你的key
# Windows PowerShell
$env:DASHSCOPE_API_KEY="你的key"
```

依赖：Python 3.10+

## 基本用法

```bash
# 1. 先干跑，看结果不写文件
python fix_links_v3.py --input processed_output_t --dry-run

# 2. 确认无误后正式运行
python fix_links_v3.py --input processed_output_t --output processed_output_t_v3
```

## 重要参数

| 参数 | 说明 |
|---|---|
| `--input` / `-i` | 输入目录（默认 `./processed_output_t`） |
| `--output` / `-o` | 输出目录（默认 `./processed_output_t_v3`） |
| `--dry-run` | 干跑，只评估不写文件 |
| `--no-llm` | 禁用 LLM，仅用字符串匹配 |
| `--no-verify` | 禁用 LLM 结果二次校验 |
| `--in-place` | 直接覆盖原文件（慎用） |

## 匹配流程

工具按以下顺序逐一尝试，命中即停止。靠前的步骤是确定性的，不走 LLM：

| 步骤 | 方法 | 确定性 | 说明 |
|---|---|---|---|
| 1 | exact string | ✅ | 链接文本与文档名完全一致 |
| 2 | depunct unique | ✅ | 去标点后唯一命中 |
| 3 | numbered_prefix | ✅ | 例1.6.10、定理1.4.3 等编号在全章范围唯一命中。多命中时自动过滤辅助文档（"的证明"、"的推论"等） |
| 4 | LLM 小节级全量 | ❌ | 当前小节内让 LLM 从全部文档中挑选 |
| 5 | LLM 节级全量 | ❌ | 小节未命中则扩大到当前节 |
| 6 | LLM 章级候选 | ❌ | 最后兜底，从 LCS Top-20 候选中精选 |

LLM 步骤（4-6）的结果会经二次校验（verify），排除完全无关或概念偏差的匹配。

## 注意事项

### API 消耗

- 前 3 步（exact/depunct/numbered_prefix）**不消耗 API**，尽可能靠它们命中
- LLM 调用范围从小节 → 节 → 章逐步放大，控制成本
- 每批最多 80 条文档送入 LLM，超出自动分批

### 自引用

工具会自动排除源文件本身，不会让 `[[函数极限的定义]]` 匹配回自己所在的文件。

### 同节引用

来自同一节的引用，verify 会更倾向于接受——因为同节语境下省略限定词（如"的运算法则"省略了"函数极限"）是正常的。

### 辅助文档

编号前缀匹配（步骤 3）会自动排除含以下关键词的辅助文档：

- `的证明`、`的推论`、`的推广`、`的说明`、`的补充说明`
- `的例题`、`的例题解答`

例如 `[[定理1.4.3]]` 在全章匹配到 `定理1.4.3-xxx` 和 `定理1.4.3的证明` 两个文档，工具会过滤掉证明文档，直接命中主文档。

### 干跑不写文件

`--dry-run` 模式下只打印结果，不修改任何文件。正式运行前务必先干跑检查。

### unresolved 日志

正式运行后会在输出目录生成两个文件：

- `fix_links_v3_unresolved.log` — 未解决链接汇总
- `fix_links_v3_report.json` — 完整匹配报告

---

## 输出解读

### 处理中输出

```
> [第一章\1-4\一_无穷小]  (index: 18 files)
   fixed: 5 | exact: 12 | unresolved: 1 | verified_ok: 2 | verified_reject: 0
```

逐行含义：

- `> [路径]` — 当前处理的小节
- `(index: N files)` — 该小节的文档数量
- `fixed` — 工具修改了多少条链接（`[[旧]]` → `[[新|旧]]`）
- `exact` — 精确自匹配数（链接文本 = 文件名，无需修改，不打印）
- `unresolved` — 所有方法均未命中，保留原文
- `verified_ok` — LLM 结果通过 verify 校验
- `verified_reject` — LLM 结果被 verify 拒绝

### 匹配行详解

```
+ [极限的定义] -> [数列极限的ε-N-定义] ([subsec]full_llm+verified, src:subsection)
```

- `+` — 命中了，会写入链接
- `[] -> []` — 链接文本 → 匹配到的文档名
- `[subsec]full_llm+verified` — 匹配方法（见下表）
- `src:subsection` — 文档所在作用域

| 方法标记 | 含义 |
|---|---|
| `exact` | 精确字符串匹配（不打印，链接无变化） |
| `depunct` | 去标点后唯一命中 |
| `numbered_prefix` | 编号前缀确定性命中 |
| `[subsec]full_llm+verified` | 小节级 LLM 全量匹配 + verify 通过 |
| `[sec]full_llm+verified` | 节级 LLM 全量匹配 + verify 通过 |
| `xxx+llm_cand+verified` | 章级 LLM 候选匹配 + verify 通过 |

**注意**：exact 自匹配（picked == link_text）默认不打印，减少噪音。

### 匹配失败行

```
! verify REJECT: [定理1.4.3] -> [定理1.4.3-无穷小...] (原因说明)
```

- `! verify REJECT` — LLM 选出了结果，但 verify 认为不对，放弃了

```
- [定理X.Y.Z]  (unresolved)
```

- `-` — 所有方法均未命中，保留原文不动

### 汇总

```
============================================================
summary
============================================================
  files:            375
  fixed:            576
  unresolved:       37
  verified_ok:      210
  verified_reject:  20
```

| 字段 | 含义 |
|---|---|
| files | 处理的文档总数 |
| fixed | 成功修复的链接数 |
| unresolved | 未解决的链接数 |
| verified_ok | 通过 verify 的 LLM 匹配数 |
| verified_reject | 被 verify 拒绝的 LLM 匹配数 |

**注意**：`fixed` 仅统计 LLM 路径的修复（含 numbered_prefix），`exact` 和 `depunct` 不计入 `fixed`——它们本来就匹配成功了。
