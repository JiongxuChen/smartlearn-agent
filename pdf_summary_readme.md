# PDF Summary Tool

A CLI tool that reads a PDF file and prints a structured summary via OpenRouter LLM.

---

一个 CLI 工具，读取 PDF 文件并通过 OpenRouter LLM 输出结构化摘要。

---

## Quick Start / 快速开始

```bash
# Install dependencies (rag_workshop conda env)
pip install pdfplumber openai python-dotenv

# Summarise entire PDF
python pdf_summary.py document.pdf

# Summarise specific pages
python pdf_summary.py document.pdf --pages 1-5

# Limit text sent to LLM
python pdf_summary.py document.pdf --max-chars 12000
```

## Requirements / 环境要求

- Python 3.10+
- conda env: `rag_workshop`
- `.env` file with `OPENROUTER_API_KEY=your-key`
- Packages: `pdfplumber`, `openai`, `python-dotenv`

## CLI Flags / 命令行参数

| Flag | Type | Default | Description |
|---|---|---|---|
| `pdf_path` | `str` (required) | — | Path to PDF file / PDF 文件路径 |
| `--pages START-END` | `str` | all pages | Page range to summarise, 1-indexed, inclusive. Rejects malformed ranges with a friendly message. / 要摘要的页码范围，1起始，闭区间。无效范围会给出友好提示。 |
| `--max-chars N` | `int` | 24000 | Max characters sent to LLM. Excess text is truncated with a warning. / 发送给 LLM 的最大字符数。超出部分截断并警告。 |

## Output / 输出

Three sections printed to stdout:
1. **Overview** — 2–4 sentence summary
2. **Key Points** — bullet list, each with `[Page X]` citation
3. **Limitations** — what the document does NOT cover

---

三个章节输出到 stdout：
1. **Overview** — 2–4 句概述
2. **Key Points** — 要点列表，每条附 `[Page X]` 引用
3. **Limitations** — 文档未涉及的内容或缺失部分

## Error Handling / 错误处理

| Scenario | Behaviour |
|---|---|
| Missing `.env` or API key | Friendly stderr message, exit 1 / 提示并退出 |
| File not found | Friendly stderr message + usage hint, exit 1 / 提示 + 用法说明 |
| Scanned PDF (no text) | Stderr explanation, no LLM call, exit 1 / 说明原因，不调用 LLM |
| `--pages 5-1` | `START (5) must be <= END (1).` |
| `--pages abc` | `Invalid page range 'abc'. Expected format: START-END` |
| `--pages 1-` | `Both START and END are required` |
| `--pages 0-5` | `Page numbers must be >= 1` |
| Text exceeds `--max-chars` | Truncated with stderr warning; LLM notes it in Limitations |
| LLM context-length error | Friendly message suggesting a smaller `--max-chars` |

## Architecture / 架构

```
pdf_summary.py
├── parse_page_range()     # validates --pages input
├── load_api_key()         # python-dotenv from .env
├── extract_text()         # pdfplumber, page-by-page with [Page N] markers
├── build_user_message()   # assembles the LLM prompt
├── call_openrouter()      # openai SDK → OpenRouter
└── main()                 # argparse → orchestrate → print
```

## File / 文件

- `pdf_summary.py` — the tool
- `.env` — `OPENROUTER_API_KEY=...` (never committed)
