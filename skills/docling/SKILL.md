---
name: docling
description: >
  Document parsing and conversion skill using Docling. Invoke when the user needs to
  extract text, tables, or structured content from PDF, DOCX, PPTX, XLSX, HTML, images,
  LaTeX, AsciiDoc, CSV, or audio/video files. Triggers on: "parse document", "convert PDF",
  "extract text from", "read this file", "import document", "docling", "OCR", or any
  request to load non-code file content into context.
---

# Docling Document Parser

Parse and convert documents into structured text for model context using Docling.

## Prerequisites

Docling must be installed as a system-level uv tool:

```bash
uv tool install docling-slim
```

This provides the `docling` CLI command system-wide. Do NOT add docling as a project
dependency — always invoke the installed tool directly.

## Capabilities

- **Multi-format parsing**: PDF, DOCX, PPTX, XLSX, HTML, Markdown, AsciiDoc, LaTeX, CSV,
  images (PNG/JPEG/TIFF/BMP/WEBP), audio (WAV/MP3/M4A), video (MP4/AVI/MOV), WebVTT
- **Output formats**: Markdown (default), HTML, JSON, plain text, DocTags
- **Advanced PDF features**: Layout analysis, table extraction, OCR, formula recognition,
  code detection, image classification, chart data extraction
- **Chunking**: Split large documents into token-aware chunks for RAG workflows
- **Batch processing**: Convert entire directories of documents
- **URL support**: Fetch and convert documents directly from URLs

## Quick Reference

### CLI Usage

Convert a single file to Markdown:
```bash
docling path/to/document.pdf
```

Convert with specific output format:
```bash
docling --to json path/to/document.pdf
docling --to html path/to/document.pdf
docling --to text path/to/document.pdf
```

Convert from URL:
```bash
docling https://example.com/paper.pdf
```

Specify input format explicitly:
```bash
docling --from docx path/to/file.docx
```

Output to specific directory:
```bash
docling --output ./converted/ path/to/document.pdf
```

### Python API Usage

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("path/to/document.pdf")
markdown = result.document.export_to_markdown()
```

### Key CLI Options

| Option | Description |
|--------|-------------|
| `--from` | Input format (pdf, docx, pptx, html, image, md, csv, xlsx, latex, etc.) |
| `--to` | Output format (md, json, yaml, html, text, doctags, vtt) |
| `--output` | Output directory (default: current directory) |
| `--pipeline` | Processing pipeline: standard, vlm, asr |
| `--ocr / --no-ocr` | Enable/disable OCR (default: enabled) |
| `--force-ocr` | Replace existing text with OCR output |
| `--tables / --no-tables` | Enable/disable table extraction (default: enabled) |
| `--table-mode` | Table extraction quality: fast or accurate |
| `--image-export-mode` | Image handling: placeholder, embedded, referenced |
| `--vlm-model` | VLM model for advanced parsing (granite_docling, etc.) |
| `--ocr-engine` | OCR backend: easyocr, tesseract, rapidocr, etc. |
| `--num-threads` | CPU threads (default: 4) |
| `--document-timeout` | Per-document timeout in seconds |

## Script: convert_document.py

Use `skills/docling/scripts/convert_document.py` for programmatic document conversion
with additional features beyond the CLI. This script uses PEP 723 inline metadata and
runs standalone via `uv run` (no project context needed):

```bash
uv run skills/docling/scripts/convert_document.py <source> [options]
```

Options:
- `--format` / `-f`: Output format (markdown, json, text, html, doctags). Default: markdown
- `--output` / `-o`: Output file path (default: stdout)
- `--chunk`: Enable chunking for large documents
- `--chunk-size`: Max tokens per chunk (default: 512)
- `--pages`: Max pages to process
- `--no-ocr`: Disable OCR
- `--no-tables`: Disable table extraction
- `--table-mode`: Table mode (fast/accurate)
- `--image-mode`: Image export (placeholder/embedded/referenced)
- `--timeout`: Document processing timeout in seconds
- `--force-ocr`: Replace text with OCR output
- `--info`: Print document structure summary (element counts, headings, word count)
- `--pipeline`: Processing pipeline (standard/vlm)
- `--tables-only`: Extract only table content from the document

## Workflow Patterns

### 1. Parse a document into context
```bash
uv run skills/docling/scripts/convert_document.py paper.pdf
```

### 2. Extract tables from a PDF
```bash
uv run skills/docling/scripts/convert_document.py report.pdf -f markdown
```

### 3. Chunk a large document for RAG
```bash
uv run skills/docling/scripts/convert_document.py book.pdf --chunk --chunk-size 1024
```

### 4. Convert a slide deck
```bash
docling presentation.pptx
```

### 5. Batch convert a directory
```bash
uv run skills/docling/scripts/convert_document.py ./documents/ -o ./converted/
```

### 6. OCR a scanned image
```bash
docling --force-ocr scan.png
```

### 7. Export as structured JSON
```bash
docling --to json path/to/report.pdf --output ./
```

### 8. Inspect document structure
```bash
uv run skills/docling/scripts/convert_document.py report.pdf --info
```

### 9. Extract only tables from a document
```bash
uv run skills/docling/scripts/convert_document.py spreadsheet.xlsx --tables-only
```

## Advanced Features

### Chunking for RAG
The script supports HybridChunker for intelligent document splitting that respects
document structure (headings, paragraphs, tables) while staying within token limits.

### Pipeline Selection
- **standard**: Default pipeline with layout analysis + OCR + table extraction
- **vlm**: Visual Language Model pipeline for complex layouts (requires VLM model)
- **asr**: Audio Speech Recognition pipeline for audio/video files

### Table Extraction
Use `--tables-only` to extract just tabular data from documents. Useful for
spreadsheets, reports with embedded tables, or any document where you need
structured data without surrounding prose.

### Error Handling
- Graceful degradation: if OCR fails, falls back to text extraction
- Timeout support: prevents hanging on corrupted files
- Page limits: process only first N pages for quick previews

## MCP Server Integration

Docling provides an MCP server for agentic AI applications. Add to your MCP config:

```json
{
  "mcpServers": {
    "docling": {
      "command": "uvx",
      "args": ["--from=docling-mcp", "docling-mcp-server"]
    }
  }
}
```

This enables document processing capabilities directly through the Model Context Protocol.

## Format Reference

See `skills/docling/references/format_reference.md` for complete format support matrix
including per-format configuration options and known limitations.
