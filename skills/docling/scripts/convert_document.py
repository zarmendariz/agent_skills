#!/usr/bin/env python3
"""Convert documents to structured text using Docling.

Supports PDF, DOCX, PPTX, XLSX, HTML, Markdown, LaTeX, CSV, images, and more.
Outputs Markdown (default), JSON, HTML, plain text, or DocTags.

Usage:
    uv run --project .devtools python skills/docling/scripts/convert_document.py <source> [options]

Examples:
    # Convert PDF to markdown (stdout)
    python convert_document.py report.pdf

    # Convert to JSON and save to file
    python convert_document.py report.pdf -f json -o report.json

    # Chunk a large document for RAG
    python convert_document.py book.pdf --chunk --chunk-size 1024

    # Batch convert a directory
    python convert_document.py ./documents/ -o ./converted/

    # OCR a scanned document
    python convert_document.py scan.pdf --force-ocr
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        description="Convert documents to structured text using Docling.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "source",
        help="File path, directory, or URL to convert.",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["markdown", "json", "text", "html", "doctags"],
        default="markdown",
        help="Output format (default: markdown).",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file or directory path. Default: stdout for single files.",
    )
    parser.add_argument(
        "--chunk",
        action="store_true",
        help="Enable chunking for large documents.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=512,
        help="Max tokens per chunk (default: 512). Requires --chunk.",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=None,
        help="Maximum number of pages to process.",
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable OCR processing.",
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Replace existing text with OCR output.",
    )
    parser.add_argument(
        "--no-tables",
        action="store_true",
        help="Disable table structure recognition.",
    )
    parser.add_argument(
        "--table-mode",
        choices=["fast", "accurate"],
        default="accurate",
        help="Table extraction mode (default: accurate).",
    )
    parser.add_argument(
        "--image-mode",
        choices=["placeholder", "embedded", "referenced"],
        default="placeholder",
        help="Image export mode (default: placeholder).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="Per-document processing timeout in seconds.",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        default=4,
        help="Number of CPU threads (default: 4).",
    )
    return parser


def create_converter(args: argparse.Namespace) -> Any:
    """Create a DocumentConverter with the given options."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import (
        PdfPipelineOptions,
        TableFormerMode,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = not args.no_ocr
    pipeline_options.do_table_structure = not args.no_tables

    if args.force_ocr:
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options.force_full_page_ocr = True

    if args.table_mode == "fast":
        pipeline_options.table_structure_options.mode = TableFormerMode.FAST
    else:
        pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        }
    )
    return converter


def export_document(doc: Any, fmt: str, image_mode: str = "placeholder") -> str:
    """Export a DoclingDocument to the specified format."""
    from docling_core.types.doc.base import ImageRefMode

    mode_map = {
        "placeholder": ImageRefMode.PLACEHOLDER,
        "embedded": ImageRefMode.EMBEDDED,
        "referenced": ImageRefMode.REFERENCED,
    }
    img_mode = mode_map.get(image_mode, ImageRefMode.PLACEHOLDER)

    if fmt == "markdown":
        return doc.export_to_markdown(image_mode=img_mode)
    elif fmt == "html":
        return doc.export_to_html(image_mode=img_mode)
    elif fmt == "text":
        return doc.export_to_text()
    elif fmt == "json":
        return json.dumps(doc.export_to_dict(), indent=2, ensure_ascii=False)
    elif fmt == "doctags":
        return doc.export_to_doctags()
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def chunk_document(doc: Any, max_tokens: int = 512) -> list[dict[str, Any]]:
    """Chunk a document using HybridChunker."""
    from docling.chunking import HybridChunker

    chunker = HybridChunker(max_tokens=max_tokens)
    chunks = []
    for i, chunk in enumerate(chunker.chunk(doc)):
        page = None
        try:
            if (hasattr(chunk.meta, "doc_items")
                    and chunk.meta.doc_items
                    and hasattr(chunk.meta.doc_items[0], "prov")
                    and chunk.meta.doc_items[0].prov):
                page = chunk.meta.doc_items[0].prov[0].page_no
        except (IndexError, AttributeError):
            pass

        chunks.append({
            "index": i,
            "text": chunker.contextualize(chunk),
            "meta": {
                "headings": chunk.meta.headings if hasattr(chunk.meta, "headings") else [],
                "page": page,
            },
        })
    return chunks


def convert_single(args: argparse.Namespace) -> str | list[dict]:
    """Convert a single document source."""
    converter = create_converter(args)

    kwargs: dict[str, Any] = {}
    if args.pages is not None:
        kwargs["max_num_pages"] = args.pages

    result = converter.convert(args.source, **kwargs)
    doc = result.document

    if args.chunk:
        return chunk_document(doc, max_tokens=args.chunk_size)

    return export_document(doc, args.format, image_mode=args.image_mode)


def convert_directory(args: argparse.Namespace) -> dict[str, str]:
    """Convert all documents in a directory."""
    source_dir = Path(args.source)
    if not source_dir.is_dir():
        raise ValueError(f"Not a directory: {source_dir}")

    converter = create_converter(args)

    supported_extensions = {
        ".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm",
        ".md", ".csv", ".tex", ".png", ".jpg", ".jpeg",
        ".tiff", ".bmp", ".webp", ".adoc", ".txt",
    }

    results = {}
    for file_path in sorted(source_dir.rglob("*")):
        if file_path.suffix.lower() in supported_extensions:
            try:
                result = converter.convert(str(file_path))
                doc = result.document
                content = export_document(doc, args.format, image_mode=args.image_mode)
                results[str(file_path.relative_to(source_dir))] = content
            except Exception as e:
                results[str(file_path.relative_to(source_dir))] = f"ERROR: {e}"

    return results


def write_output(content: Any, output_path: str | None, fmt: str) -> None:
    """Write conversion output to file or stdout."""
    if isinstance(content, list):
        # Chunked output
        text = json.dumps(content, indent=2, ensure_ascii=False)
    elif isinstance(content, dict):
        # Batch output
        if output_path:
            out_dir = Path(output_path)
            out_dir.mkdir(parents=True, exist_ok=True)
            ext_map = {
                "markdown": ".md", "json": ".json", "text": ".txt",
                "html": ".html", "doctags": ".doctags",
            }
            ext = ext_map.get(fmt, ".md")
            for filename, file_content in content.items():
                out_file = out_dir / (Path(filename).stem + ext)
                out_file.parent.mkdir(parents=True, exist_ok=True)
                out_file.write_text(file_content, encoding="utf-8")
            print(f"Converted {len(content)} files to {out_dir}", file=sys.stderr)
            return
        text = json.dumps(content, indent=2, ensure_ascii=False)
    else:
        text = content

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(text, encoding="utf-8")
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        print(text)


def main() -> int:
    """Main entry point."""
    import os
    os.environ.setdefault("OMP_NUM_THREADS", "4")

    parser = build_parser()
    args = parser.parse_args()

    if args.num_threads:
        os.environ["OMP_NUM_THREADS"] = str(args.num_threads)

    try:
        source_path = Path(args.source)
        if source_path.is_dir():
            content = convert_directory(args)
        else:
            content = convert_single(args)

        write_output(content, args.output, args.format)
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
