# Docling Format Reference

## Table of Contents

1. [Supported Input Formats](#supported-input-formats)
2. [Supported Output Formats](#supported-output-formats)
3. [Pipeline Options](#pipeline-options)
4. [OCR Engines](#ocr-engines)
5. [VLM Models](#vlm-models)
6. [Chunking Options](#chunking-options)

## Supported Input Formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| PDF | .pdf | Full layout analysis, OCR, tables, formulas |
| DOCX | .docx | Office Open XML word processing |
| PPTX | .pptx | Office Open XML presentations |
| XLSX | .xlsx | Office Open XML spreadsheets |
| HTML/XHTML | .html, .xhtml, .htm | Web pages |
| Markdown | .md, .qmd, .Rmd | Including Quarto and R Markdown |
| AsciiDoc | .adoc, .asciidoc | Technical documentation format |
| LaTeX | .tex, .latex | Scientific document format |
| CSV | .csv | Comma-separated values |
| Images | .png, .jpeg, .jpg, .tiff, .bmp, .webp | OCR-based extraction |
| Audio | .wav, .mp3, .m4a, .aac, .ogg, .flac | Requires `asr` extra |
| Video | .mp4, .avi, .mov | Audio track extraction + ASR |
| WebVTT | .vtt | Timed text tracks |
| USPTO XML | .xml | US Patent and Trademark Office |
| JATS XML | .xml | Journal Article Tag Suite |
| XBRL XML | .xml | Financial reporting |
| Docling JSON | .json | Re-import previously exported documents |
| Plain Text | .txt, .text | Simple text files |

## Supported Output Formats

| Format | CLI Flag | Python Method | Notes |
|--------|----------|---------------|-------|
| Markdown | `--to md` | `export_to_markdown()` | Default output format |
| HTML | `--to html` | `export_to_html()` | Supports image embedding |
| JSON | `--to json` | `export_to_dict()` | Lossless DoclingDocument |
| YAML | `--to yaml` | N/A | CLI only |
| Plain Text | `--to text` | `export_to_text()` | No formatting markers |
| DocTags | `--to doctags` | `export_to_doctags()` | Layout-preserving markup |
| WebVTT | `--to vtt` | N/A | Timed text output |

## Pipeline Options

### Standard Pipeline (default)
- Layout analysis model detects page structure
- Table structure recognition with TableFormer
- OCR for scanned content
- Code and formula detection
- Image classification

### VLM Pipeline
- Uses Visual Language Models for document understanding
- Available models: granite_docling, smoldocling, deepseek_ocr, phi4, qwen
- Better for complex or unusual layouts
- Requires model download on first use

### ASR Pipeline
- Automatic Speech Recognition for audio/video
- Uses Whisper models (tiny through large)
- Supports MLX acceleration on Apple Silicon

## OCR Engines

| Engine | Platform | Notes |
|--------|----------|-------|
| easyocr | All | Default, supports many languages |
| tesseract | All | Requires system install |
| rapidocr | All | Fast alternative |
| ocrmac | macOS | Uses Apple's Vision framework |

## VLM Models

| Model ID | Description |
|----------|-------------|
| granite_docling | IBM Granite document model (default) |
| smoldocling | Lightweight document model |
| deepseek_ocr | DeepSeek OCR model |
| phi4 | Microsoft Phi-4 |
| qwen | Qwen vision model |
| pixtral | Mistral Pixtral |
| got_ocr | GOT-OCR model |

## Chunking Options

### HybridChunker
- Token-aware splitting respecting document structure
- Configurable max chunk size
- Merges undersized adjacent chunks with same context
- Repeats table headers across chunks

### HierarchicalChunker
- One chunk per document element
- Preserves complete hierarchy metadata
- Merges list items by default

### LineBasedTokenChunker
- Preserves line boundaries
- Good for tables, code, logs
- Supports prefix repetition for context

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DOCLING_ARTIFACTS_PATH` | Local model cache directory |
| `OMP_NUM_THREADS` | Limit CPU thread usage |

## Python API Quick Reference

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import PdfFormatOption

# Basic conversion
converter = DocumentConverter()
result = converter.convert("file.pdf")
doc = result.document

# Export methods
doc.export_to_markdown()
doc.export_to_html()
doc.export_to_text()
doc.export_to_dict()  # JSON-serializable dict
doc.export_to_doctags()

# Custom pipeline
pipeline_options = PdfPipelineOptions(
    do_table_structure=True,
    do_ocr=True,
)
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# Chunking
from docling.chunking import HybridChunker
chunker = HybridChunker(tokenizer="BAAI/bge-small-en-v1.5", max_tokens=512)
chunks = list(chunker.chunk(doc))
```
