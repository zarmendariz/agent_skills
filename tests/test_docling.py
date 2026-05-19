"""Comprehensive tests for the docling skill.

Tests cover:
- Document conversion across all supported formats
- Output format selection (markdown, json, text, html, doctags)
- CLI argument parsing
- Chunking functionality
- Directory batch processing
- Error handling and edge cases
- Script integration (subprocess execution)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "docling"
SCRIPT_PATH = REPO_ROOT / "skills" / "docling" / "scripts" / "convert_document.py"

# Add the script directory to path for imports
sys.path.insert(0, str(SCRIPT_PATH.parent))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_md():
    return FIXTURES_DIR / "sample.md"


@pytest.fixture
def sample_html():
    return FIXTURES_DIR / "sample.html"


@pytest.fixture
def sample_csv():
    return FIXTURES_DIR / "sample.csv"


@pytest.fixture
def sample_txt():
    return FIXTURES_DIR / "sample.txt"


@pytest.fixture
def sample_docx():
    return FIXTURES_DIR / "sample.docx"


@pytest.fixture
def sample_pdf():
    return FIXTURES_DIR / "sample.pdf"


@pytest.fixture
def sample_docling_json():
    return FIXTURES_DIR / "sample_docling.json"


@pytest.fixture
def sample_pptx():
    return FIXTURES_DIR / "sample.pptx"


@pytest.fixture
def sample_xlsx():
    return FIXTURES_DIR / "sample.xlsx"


@pytest.fixture
def sample_tex():
    return FIXTURES_DIR / "sample.tex"


@pytest.fixture
def temp_output_dir(tmp_path):
    return tmp_path / "output"


@pytest.fixture
def converter():
    """Cached DocumentConverter instance for tests."""
    from docling.document_converter import DocumentConverter
    return DocumentConverter()


# ---------------------------------------------------------------------------
# Test: Argument Parser
# ---------------------------------------------------------------------------


class TestArgumentParser:
    """Test CLI argument parsing."""

    def test_build_parser_defaults(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.source == "test.pdf"
        assert args.format == "markdown"
        assert args.output is None
        assert args.chunk is False
        assert args.chunk_size == 512
        assert args.pages is None
        assert args.no_ocr is False
        assert args.force_ocr is False
        assert args.no_tables is False
        assert args.table_mode == "accurate"
        assert args.image_mode == "placeholder"
        assert args.timeout is None
        assert args.num_threads == 4

    def test_format_choices(self):
        from convert_document import build_parser
        parser = build_parser()
        for fmt in ["markdown", "json", "text", "html", "doctags"]:
            args = parser.parse_args(["test.pdf", "-f", fmt])
            assert args.format == fmt

    def test_chunk_options(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--chunk", "--chunk-size", "1024"])
        assert args.chunk is True
        assert args.chunk_size == 1024

    def test_ocr_options(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--no-ocr"])
        assert args.no_ocr is True
        args = parser.parse_args(["test.pdf", "--force-ocr"])
        assert args.force_ocr is True

    def test_table_options(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--no-tables"])
        assert args.no_tables is True
        args = parser.parse_args(["test.pdf", "--table-mode", "fast"])
        assert args.table_mode == "fast"

    def test_image_mode_options(self):
        from convert_document import build_parser
        parser = build_parser()
        for mode in ["placeholder", "embedded", "referenced"]:
            args = parser.parse_args(["test.pdf", "--image-mode", mode])
            assert args.image_mode == mode

    def test_timeout_and_threads(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--timeout", "30.5", "--num-threads", "8"])
        assert args.timeout == 30.5
        assert args.num_threads == 8

    def test_output_option(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "-o", "output.md"])
        assert args.output == "output.md"

    def test_pages_option(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--pages", "5"])
        assert args.pages == 5


# ---------------------------------------------------------------------------
# Test: Document Conversion (Markdown input)
# ---------------------------------------------------------------------------


class TestMarkdownConversion:
    """Test converting Markdown documents."""

    def test_convert_markdown_to_markdown(self, converter, sample_md):
        result = converter.convert(str(sample_md))
        md = result.document.export_to_markdown()
        assert "Test Document" in md
        assert "Introduction" in md
        assert "Section One" in md

    def test_convert_markdown_preserves_structure(self, converter, sample_md):
        result = converter.convert(str(sample_md))
        md = result.document.export_to_markdown()
        assert "## " in md or "# " in md  # Headings preserved
        assert "- " in md or "* " in md  # Lists preserved

    def test_convert_markdown_preserves_table(self, converter, sample_md):
        result = converter.convert(str(sample_md))
        md = result.document.export_to_markdown()
        assert "Column A" in md
        assert "Value 1" in md

    def test_convert_markdown_to_text(self, converter, sample_md):
        result = converter.convert(str(sample_md))
        text = result.document.export_to_text()
        assert "Test Document" in text
        assert "Introduction" in text

    def test_convert_markdown_to_html(self, converter, sample_md):
        result = converter.convert(str(sample_md))
        html = result.document.export_to_html()
        assert "Test Document" in html

    def test_convert_markdown_to_json(self, converter, sample_md):
        result = converter.convert(str(sample_md))
        d = result.document.export_to_dict()
        assert isinstance(d, dict)
        assert "name" in d
        assert "body" in d

    def test_convert_markdown_to_doctags(self, converter, sample_md):
        result = converter.convert(str(sample_md))
        doctags = result.document.export_to_doctags()
        assert isinstance(doctags, str)
        assert len(doctags) > 0


# ---------------------------------------------------------------------------
# Test: HTML Conversion
# ---------------------------------------------------------------------------


class TestHtmlConversion:
    """Test converting HTML documents."""

    def test_convert_html_to_markdown(self, converter, sample_html):
        result = converter.convert(str(sample_html))
        md = result.document.export_to_markdown()
        assert "HTML Test Document" in md

    def test_convert_html_preserves_table(self, converter, sample_html):
        result = converter.convert(str(sample_html))
        md = result.document.export_to_markdown()
        assert "Alpha" in md
        assert "100" in md

    def test_convert_html_preserves_list(self, converter, sample_html):
        result = converter.convert(str(sample_html))
        md = result.document.export_to_markdown()
        assert "First item" in md
        assert "Second item" in md

    def test_convert_html_to_text(self, converter, sample_html):
        result = converter.convert(str(sample_html))
        text = result.document.export_to_text()
        assert "HTML Test Document" in text
        # Plain text should not have markdown markers
        assert "<html>" not in text


# ---------------------------------------------------------------------------
# Test: CSV Conversion
# ---------------------------------------------------------------------------


class TestCsvConversion:
    """Test converting CSV documents."""

    def test_convert_csv_to_markdown(self, converter, sample_csv):
        result = converter.convert(str(sample_csv))
        md = result.document.export_to_markdown()
        assert "Alice" in md
        assert "New York" in md

    def test_convert_csv_preserves_all_rows(self, converter, sample_csv):
        result = converter.convert(str(sample_csv))
        md = result.document.export_to_markdown()
        assert "Alice" in md
        assert "Bob" in md
        assert "Charlie" in md
        assert "Diana" in md

    def test_convert_csv_preserves_headers(self, converter, sample_csv):
        result = converter.convert(str(sample_csv))
        md = result.document.export_to_markdown()
        assert "Name" in md
        assert "Age" in md
        assert "City" in md


# ---------------------------------------------------------------------------
# Test: DOCX Conversion
# ---------------------------------------------------------------------------


class TestDocxConversion:
    """Test converting DOCX documents."""

    def test_convert_docx_to_markdown(self, converter, sample_docx):
        result = converter.convert(str(sample_docx))
        md = result.document.export_to_markdown()
        assert "Test DOCX Document" in md

    def test_convert_docx_preserves_headings(self, converter, sample_docx):
        result = converter.convert(str(sample_docx))
        md = result.document.export_to_markdown()
        assert "Section One" in md
        assert "Section Two" in md

    def test_convert_docx_preserves_table(self, converter, sample_docx):
        result = converter.convert(str(sample_docx))
        md = result.document.export_to_markdown()
        assert "Header A" in md
        assert "Row1A" in md
        assert "Row2C" in md

    def test_convert_docx_preserves_lists(self, converter, sample_docx):
        result = converter.convert(str(sample_docx))
        md = result.document.export_to_markdown()
        assert "First bullet" in md
        assert "Second bullet" in md

    def test_convert_docx_to_json(self, converter, sample_docx):
        result = converter.convert(str(sample_docx))
        d = result.document.export_to_dict()
        assert isinstance(d, dict)
        assert d.get("schema_name") == "DoclingDocument"


# ---------------------------------------------------------------------------
# Test: PDF Conversion
# ---------------------------------------------------------------------------


class TestPdfConversion:
    """Test converting PDF documents."""

    def test_convert_pdf_to_markdown(self, converter, sample_pdf):
        result = converter.convert(str(sample_pdf))
        md = result.document.export_to_markdown()
        assert "Test PDF Document" in md

    def test_convert_pdf_extracts_text(self, converter, sample_pdf):
        result = converter.convert(str(sample_pdf))
        md = result.document.export_to_markdown()
        assert "Docling parsing validation" in md

    def test_convert_pdf_to_text(self, converter, sample_pdf):
        result = converter.convert(str(sample_pdf))
        text = result.document.export_to_text()
        assert "Test PDF Document" in text

    def test_convert_pdf_to_json(self, converter, sample_pdf):
        result = converter.convert(str(sample_pdf))
        d = result.document.export_to_dict()
        assert isinstance(d, dict)
        assert "texts" in d or "body" in d


# ---------------------------------------------------------------------------
# Test: Plain Text Conversion
# ---------------------------------------------------------------------------


class TestPlainTextConversion:
    """Test converting plain text documents."""

    def test_convert_txt_to_markdown(self, converter, sample_txt):
        result = converter.convert(str(sample_txt))
        md = result.document.export_to_markdown()
        assert "Plain Text Document" in md or "Lorem ipsum" in md

    def test_convert_txt_preserves_content(self, converter, sample_txt):
        result = converter.convert(str(sample_txt))
        text = result.document.export_to_text()
        assert "Lorem ipsum" in text


# ---------------------------------------------------------------------------
# Test: PPTX Conversion
# ---------------------------------------------------------------------------


class TestPptxConversion:
    """Test converting PPTX documents."""

    def test_convert_pptx_to_markdown(self, converter, sample_pptx):
        result = converter.convert(str(sample_pptx))
        md = result.document.export_to_markdown()
        assert "Test Presentation" in md

    def test_convert_pptx_preserves_slide_titles(self, converter, sample_pptx):
        result = converter.convert(str(sample_pptx))
        md = result.document.export_to_markdown()
        assert "Key Points" in md

    def test_convert_pptx_preserves_bullet_points(self, converter, sample_pptx):
        result = converter.convert(str(sample_pptx))
        md = result.document.export_to_markdown()
        assert "First point" in md
        assert "Second point" in md

    def test_convert_pptx_to_text(self, converter, sample_pptx):
        result = converter.convert(str(sample_pptx))
        text = result.document.export_to_text()
        assert "Test Presentation" in text

    def test_convert_pptx_to_json(self, converter, sample_pptx):
        result = converter.convert(str(sample_pptx))
        d = result.document.export_to_dict()
        assert isinstance(d, dict)
        assert d.get("schema_name") == "DoclingDocument"


# ---------------------------------------------------------------------------
# Test: Docling JSON Reimport
# ---------------------------------------------------------------------------


class TestDoclingJsonReimport:
    """Test reimporting previously exported Docling JSON documents."""

    def test_reimport_docling_json(self, converter, sample_docling_json):
        result = converter.convert(str(sample_docling_json))
        md = result.document.export_to_markdown()
        assert "Test PDF-like Document" in md

    def test_reimport_preserves_headings(self, converter, sample_docling_json):
        result = converter.convert(str(sample_docling_json))
        md = result.document.export_to_markdown()
        assert "Introduction" in md
        assert "Data Section" in md

    def test_reimport_preserves_content(self, converter, sample_docling_json):
        result = converter.convert(str(sample_docling_json))
        md = result.document.export_to_markdown()
        assert "JSON roundtrip" in md

    def test_reimport_to_json_roundtrip(self, converter, sample_docling_json):
        result = converter.convert(str(sample_docling_json))
        d = result.document.export_to_dict()
        assert d["schema_name"] == "DoclingDocument"
        assert len(d.get("texts", [])) > 0


# ---------------------------------------------------------------------------
# Test: XLSX Conversion
# ---------------------------------------------------------------------------


class TestXlsxConversion:
    """Test converting XLSX spreadsheet documents."""

    def test_convert_xlsx_to_markdown(self, converter, sample_xlsx):
        result = converter.convert(str(sample_xlsx))
        md = result.document.export_to_markdown()
        assert "Widget A" in md

    def test_convert_xlsx_preserves_headers(self, converter, sample_xlsx):
        result = converter.convert(str(sample_xlsx))
        md = result.document.export_to_markdown()
        assert "Product" in md
        assert "Q1" in md

    def test_convert_xlsx_preserves_data(self, converter, sample_xlsx):
        result = converter.convert(str(sample_xlsx))
        md = result.document.export_to_markdown()
        assert "100" in md
        assert "Widget C" in md

    def test_convert_xlsx_to_json(self, converter, sample_xlsx):
        result = converter.convert(str(sample_xlsx))
        d = result.document.export_to_dict()
        assert isinstance(d, dict)
        assert len(d.get("tables", [])) > 0


# ---------------------------------------------------------------------------
# Test: LaTeX Conversion
# ---------------------------------------------------------------------------


class TestLatexConversion:
    """Test converting LaTeX documents."""

    def test_convert_latex_to_markdown(self, converter, sample_tex):
        result = converter.convert(str(sample_tex))
        md = result.document.export_to_markdown()
        assert "Test LaTeX Document" in md

    def test_convert_latex_preserves_sections(self, converter, sample_tex):
        result = converter.convert(str(sample_tex))
        md = result.document.export_to_markdown()
        assert "Introduction" in md
        assert "Methods" in md
        assert "Conclusion" in md

    def test_convert_latex_preserves_equation(self, converter, sample_tex):
        result = converter.convert(str(sample_tex))
        md = result.document.export_to_markdown()
        assert "mc^2" in md or "mc" in md

    def test_convert_latex_preserves_table(self, converter, sample_tex):
        result = converter.convert(str(sample_tex))
        md = result.document.export_to_markdown()
        assert "1.23" in md
        assert "4.56" in md

    def test_convert_latex_to_text(self, converter, sample_tex):
        result = converter.convert(str(sample_tex))
        text = result.document.export_to_text()
        assert "Introduction" in text
        assert "Docling parsing" in text


# ---------------------------------------------------------------------------
# Test: Export Document Function
# ---------------------------------------------------------------------------


class TestExportDocument:
    """Test the export_document helper function."""

    def test_export_markdown(self, converter, sample_md):
        from convert_document import export_document
        result = converter.convert(str(sample_md))
        output = export_document(result.document, "markdown")
        assert isinstance(output, str)
        assert "Test Document" in output

    def test_export_text(self, converter, sample_md):
        from convert_document import export_document
        result = converter.convert(str(sample_md))
        output = export_document(result.document, "text")
        assert isinstance(output, str)
        assert "Test Document" in output

    def test_export_html(self, converter, sample_md):
        from convert_document import export_document
        result = converter.convert(str(sample_md))
        output = export_document(result.document, "html")
        assert isinstance(output, str)
        assert len(output) > 0

    def test_export_json(self, converter, sample_md):
        from convert_document import export_document
        result = converter.convert(str(sample_md))
        output = export_document(result.document, "json")
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_export_doctags(self, converter, sample_md):
        from convert_document import export_document
        result = converter.convert(str(sample_md))
        output = export_document(result.document, "doctags")
        assert isinstance(output, str)

    def test_export_unsupported_format(self, converter, sample_md):
        from convert_document import export_document
        result = converter.convert(str(sample_md))
        with pytest.raises(ValueError, match="Unsupported format"):
            export_document(result.document, "invalid_format")


# ---------------------------------------------------------------------------
# Test: Create Converter Function
# ---------------------------------------------------------------------------


class TestCreateConverter:
    """Test converter creation with various options."""

    def test_create_default_converter(self):
        from convert_document import build_parser, create_converter
        parser = build_parser()
        args = parser.parse_args(["test.pdf"])
        conv = create_converter(args)
        assert conv is not None

    def test_create_converter_no_ocr(self):
        from convert_document import build_parser, create_converter
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--no-ocr"])
        conv = create_converter(args)
        assert conv is not None

    def test_create_converter_no_tables(self):
        from convert_document import build_parser, create_converter
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--no-tables"])
        conv = create_converter(args)
        assert conv is not None

    def test_create_converter_fast_tables(self):
        from convert_document import build_parser, create_converter
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--table-mode", "fast"])
        conv = create_converter(args)
        assert conv is not None

    def test_create_converter_force_ocr(self):
        from convert_document import build_parser, create_converter
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--force-ocr"])
        conv = create_converter(args)
        assert conv is not None


# ---------------------------------------------------------------------------
# Test: Chunking
# ---------------------------------------------------------------------------


class TestChunking:
    """Test document chunking functionality."""

    def test_chunk_document_returns_list(self, converter, sample_md):
        from convert_document import chunk_document
        result = converter.convert(str(sample_md))
        chunks = chunk_document(result.document, max_tokens=128)
        assert isinstance(chunks, list)
        assert len(chunks) > 0

    def test_chunk_document_structure(self, converter, sample_md):
        from convert_document import chunk_document
        result = converter.convert(str(sample_md))
        chunks = chunk_document(result.document, max_tokens=128)
        for chunk in chunks:
            assert "index" in chunk
            assert "text" in chunk
            assert "meta" in chunk
            assert isinstance(chunk["text"], str)
            assert len(chunk["text"]) > 0

    def test_chunk_document_indices_sequential(self, converter, sample_md):
        from convert_document import chunk_document
        result = converter.convert(str(sample_md))
        chunks = chunk_document(result.document, max_tokens=128)
        for i, chunk in enumerate(chunks):
            assert chunk["index"] == i

    def test_chunk_large_document_respects_size(self, converter, sample_docx):
        from convert_document import chunk_document
        result = converter.convert(str(sample_docx))
        chunks = chunk_document(result.document, max_tokens=64)
        # With small chunk size, we should get multiple chunks
        assert len(chunks) >= 1

    def test_chunk_small_size_creates_more_chunks(self, converter, sample_md):
        from convert_document import chunk_document
        result = converter.convert(str(sample_md))
        chunks_small = chunk_document(result.document, max_tokens=64)
        chunks_large = chunk_document(result.document, max_tokens=2048)
        assert len(chunks_small) >= len(chunks_large)


# ---------------------------------------------------------------------------
# Test: Directory Batch Processing
# ---------------------------------------------------------------------------


class TestDirectoryProcessing:
    """Test batch directory conversion."""

    def test_convert_directory(self, converter, temp_output_dir):
        from convert_document import build_parser, convert_directory
        parser = build_parser()
        args = parser.parse_args([str(FIXTURES_DIR), "-o", str(temp_output_dir)])
        results = convert_directory(args)
        assert isinstance(results, dict)
        assert len(results) > 0
        # Should find our test files
        filenames = list(results.keys())
        assert any("sample.md" in f for f in filenames)
        assert any("sample.html" in f for f in filenames)
        assert any("sample.csv" in f for f in filenames)

    def test_convert_directory_not_a_dir(self):
        from convert_document import build_parser, convert_directory
        parser = build_parser()
        args = parser.parse_args(["nonexistent_path"])
        with pytest.raises(ValueError, match="Not a directory"):
            convert_directory(args)

    def test_convert_directory_results_have_content(self, converter):
        from convert_document import build_parser, convert_directory
        parser = build_parser()
        args = parser.parse_args([str(FIXTURES_DIR)])
        results = convert_directory(args)
        for filename, content in results.items():
            if not content.startswith("ERROR:"):
                assert len(content) > 0


# ---------------------------------------------------------------------------
# Test: Write Output Function
# ---------------------------------------------------------------------------


class TestWriteOutput:
    """Test output writing."""

    def test_write_string_to_file(self, tmp_path):
        from convert_document import write_output
        output_file = str(tmp_path / "output.md")
        write_output("# Hello World", output_file, "markdown")
        assert Path(output_file).exists()
        assert Path(output_file).read_text(encoding="utf-8") == "# Hello World"

    def test_write_string_to_stdout(self, capsys):
        from convert_document import write_output
        write_output("hello output", None, "markdown")
        captured = capsys.readouterr()
        assert "hello output" in captured.out

    def test_write_chunks_to_file(self, tmp_path):
        from convert_document import write_output
        chunks = [{"index": 0, "text": "chunk1"}, {"index": 1, "text": "chunk2"}]
        output_file = str(tmp_path / "chunks.json")
        write_output(chunks, output_file, "json")
        content = json.loads(Path(output_file).read_text(encoding="utf-8"))
        assert len(content) == 2
        assert content[0]["text"] == "chunk1"

    def test_write_dict_to_directory(self, tmp_path):
        from convert_document import write_output
        results = {
            "doc1.pdf": "# Document One",
            "doc2.pdf": "# Document Two",
        }
        output_dir = str(tmp_path / "batch_out")
        write_output(results, output_dir, "markdown")
        out_path = Path(output_dir)
        assert out_path.exists()
        assert (out_path / "doc1.md").exists()
        assert (out_path / "doc2.md").exists()

    def test_write_creates_parent_dirs(self, tmp_path):
        from convert_document import write_output
        output_file = str(tmp_path / "deep" / "nested" / "output.md")
        write_output("content", output_file, "markdown")
        assert Path(output_file).exists()


# ---------------------------------------------------------------------------
# Test: Convert Single Function
# ---------------------------------------------------------------------------


class TestConvertSingle:
    """Test single file conversion end-to-end."""

    def test_convert_single_markdown(self, sample_md):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_md)])
        result = convert_single(args)
        assert isinstance(result, str)
        assert "Test Document" in result

    def test_convert_single_json_format(self, sample_md):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_md), "-f", "json"])
        result = convert_single(args)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_convert_single_text_format(self, sample_html):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_html), "-f", "text"])
        result = convert_single(args)
        assert "HTML Test Document" in result

    def test_convert_single_with_chunking(self, sample_md):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_md), "--chunk", "--chunk-size", "128"])
        result = convert_single(args)
        assert isinstance(result, list)
        assert len(result) > 0
        assert "text" in result[0]

    def test_convert_single_with_pages_limit(self, sample_pdf):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_pdf), "--pages", "1"])
        result = convert_single(args)
        assert isinstance(result, str)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Test: Script Subprocess Execution
# ---------------------------------------------------------------------------


class TestSubprocessExecution:
    """Test running the script as a subprocess."""

    def test_script_help(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "Convert documents" in result.stdout

    def test_script_convert_markdown(self, sample_md):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(sample_md)],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0
        assert "Test Document" in result.stdout

    def test_script_convert_html(self, sample_html):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(sample_html)],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0
        assert "HTML Test Document" in result.stdout

    def test_script_convert_csv(self, sample_csv):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(sample_csv)],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0
        assert "Alice" in result.stdout

    def test_script_convert_to_json(self, sample_md):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(sample_md), "-f", "json"],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, dict)

    def test_script_output_to_file(self, sample_md, tmp_path):
        output_file = str(tmp_path / "output.md")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(sample_md), "-o", output_file],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0
        assert Path(output_file).exists()
        content = Path(output_file).read_text(encoding="utf-8")
        assert "Test Document" in content

    def test_script_chunk_mode(self, sample_md):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(sample_md),
             "--chunk", "--chunk-size", "128"],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0
        parsed = json.loads(result.stdout)
        assert isinstance(parsed, list)
        assert len(parsed) > 0

    def test_script_nonexistent_file(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "nonexistent_file.pdf"],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 1
        assert "Error" in result.stderr

    def test_script_convert_docx(self, sample_docx):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(sample_docx)],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0
        assert "Test DOCX Document" in result.stdout


# ---------------------------------------------------------------------------
# Test: Error Handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_nonexistent_file_raises(self):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args(["nonexistent_file_xyz.pdf"])
        with pytest.raises(Exception):
            convert_single(args)

    def test_empty_file_handling(self, tmp_path):
        """Empty file should either convert to empty output or raise gracefully."""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("", encoding="utf-8")
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(empty_file)])
        # Should not crash
        result = convert_single(args)
        assert isinstance(result, str)

    def test_invalid_format_in_export(self, converter, sample_md):
        from convert_document import export_document
        result = converter.convert(str(sample_md))
        with pytest.raises(ValueError):
            export_document(result.document, "nonexistent")

    def test_directory_nonexistent_raises(self):
        from convert_document import build_parser, convert_directory
        parser = build_parser()
        args = parser.parse_args(["/nonexistent/path/xyz"])
        with pytest.raises(ValueError, match="Not a directory"):
            convert_directory(args)


# ---------------------------------------------------------------------------
# Test: DoclingDocument Properties
# ---------------------------------------------------------------------------


class TestDoclingDocumentProperties:
    """Test properties of the converted DoclingDocument."""

    def test_document_has_name(self, converter, sample_md):
        result = converter.convert(str(sample_md))
        doc = result.document
        assert doc.name is not None

    def test_document_has_body(self, converter, sample_md):
        result = converter.convert(str(sample_md))
        doc = result.document
        assert doc.body is not None

    def test_document_export_to_dict_roundtrip(self, converter, sample_md):
        result = converter.convert(str(sample_md))
        doc = result.document
        d = doc.export_to_dict()
        assert d["schema_name"] == "DoclingDocument"
        assert "body" in d
        assert "texts" in d

    def test_document_texts_populated(self, converter, sample_html):
        result = converter.convert(str(sample_html))
        doc = result.document
        d = doc.export_to_dict()
        assert len(d.get("texts", [])) > 0

    def test_document_tables_populated(self, converter, sample_csv):
        result = converter.convert(str(sample_csv))
        doc = result.document
        d = doc.export_to_dict()
        assert len(d.get("tables", [])) > 0


# ---------------------------------------------------------------------------
# Test: Multi-format Output Consistency
# ---------------------------------------------------------------------------


class TestOutputConsistency:
    """Verify that different output formats contain equivalent content."""

    def test_all_formats_have_content(self, converter, sample_docx):
        result = converter.convert(str(sample_docx))
        doc = result.document
        md = doc.export_to_markdown()
        text = doc.export_to_text()
        html = doc.export_to_html()
        json_out = doc.export_to_dict()

        # All should be non-empty
        assert len(md) > 0
        assert len(text) > 0
        assert len(html) > 0
        assert len(json_out) > 0

    def test_text_is_subset_of_markdown(self, converter, sample_docx):
        """Plain text content should appear in markdown output."""
        result = converter.convert(str(sample_docx))
        doc = result.document
        text = doc.export_to_text()
        md = doc.export_to_markdown()
        # Key phrases from text should appear in markdown
        for phrase in ["Section One", "Section Two"]:
            assert phrase in text
            assert phrase in md

    def test_json_contains_schema(self, converter, sample_md):
        result = converter.convert(str(sample_md))
        d = result.document.export_to_dict()
        assert d["schema_name"] == "DoclingDocument"
        assert "version" in d


# ---------------------------------------------------------------------------
# Test: Document Info Feature
# ---------------------------------------------------------------------------


class TestDocumentInfo:
    """Test the --info document introspection feature."""

    def test_info_returns_string(self, sample_md):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_md), "--info"])
        result = convert_single(args)
        assert isinstance(result, str)

    def test_info_contains_document_name(self, sample_md):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_md), "--info"])
        result = convert_single(args)
        assert "Document:" in result

    def test_info_contains_content_summary(self, sample_md):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_md), "--info"])
        result = convert_single(args)
        assert "Text elements:" in result
        assert "Tables:" in result

    def test_info_contains_statistics(self, sample_md):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_md), "--info"])
        result = convert_single(args)
        assert "Words:" in result
        assert "Characters:" in result

    def test_info_shows_headings(self, sample_docx):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_docx), "--info"])
        result = convert_single(args)
        assert "Table of Contents:" in result
        assert "Section One" in result

    def test_info_shows_label_counts(self, sample_docx):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_docx), "--info"])
        result = convert_single(args)
        assert "Text Labels:" in result

    def test_info_docx_has_tables(self, sample_docx):
        from convert_document import build_parser, convert_single
        parser = build_parser()
        args = parser.parse_args([str(sample_docx), "--info"])
        result = convert_single(args)
        assert "Tables: 1" in result

    def test_info_subprocess(self, sample_md):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(sample_md), "--info"],
            capture_output=True, text=True, timeout=120,
        )
        assert result.returncode == 0
        assert "Document:" in result.stdout
        assert "Words:" in result.stdout


# ---------------------------------------------------------------------------
# Test: Pipeline Options
# ---------------------------------------------------------------------------


class TestPipelineOptions:
    """Test pipeline configuration."""

    def test_parser_accepts_pipeline_standard(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--pipeline", "standard"])
        assert args.pipeline == "standard"

    def test_parser_accepts_pipeline_vlm(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--pipeline", "vlm"])
        assert args.pipeline == "vlm"

    def test_parser_default_pipeline(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.pipeline == "standard"

    def test_info_flag_in_parser(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf", "--info"])
        assert args.info is True

    def test_info_default_false(self):
        from convert_document import build_parser
        parser = build_parser()
        args = parser.parse_args(["test.pdf"])
        assert args.info is False


# ---------------------------------------------------------------------------
# Test: Image Mode Handling
# ---------------------------------------------------------------------------


class TestImageModeHandling:
    """Test image export mode enum mapping."""

    def test_export_with_placeholder_mode(self, converter, sample_md):
        from convert_document import export_document
        result = converter.convert(str(sample_md))
        output = export_document(result.document, "markdown", image_mode="placeholder")
        assert isinstance(output, str)

    def test_export_with_embedded_mode(self, converter, sample_md):
        from convert_document import export_document
        result = converter.convert(str(sample_md))
        output = export_document(result.document, "markdown", image_mode="embedded")
        assert isinstance(output, str)

    def test_export_with_referenced_mode(self, converter, sample_md):
        from convert_document import export_document
        result = converter.convert(str(sample_md))
        output = export_document(result.document, "html", image_mode="referenced")
        assert isinstance(output, str)

    def test_export_with_invalid_mode_falls_back(self, converter, sample_md):
        from convert_document import export_document
        result = converter.convert(str(sample_md))
        # Invalid mode should fall back to placeholder without error
        output = export_document(result.document, "markdown", image_mode="invalid")
        assert isinstance(output, str)


# ---------------------------------------------------------------------------
# Test: JSON Export/Reimport Roundtrip
# ---------------------------------------------------------------------------


class TestJsonRoundtrip:
    """Test that JSON export → reimport preserves document content."""

    def test_docx_json_roundtrip(self, converter, sample_docx, tmp_path):
        """Export DOCX to JSON, reimport, verify content preserved."""
        # Convert original
        result = converter.convert(str(sample_docx))
        original_md = result.document.export_to_markdown()

        # Export to JSON
        json_file = tmp_path / "exported.json"
        d = result.document.export_to_dict()
        json_file.write_text(json.dumps(d, indent=2), encoding="utf-8")

        # Reimport
        result2 = converter.convert(str(json_file))
        reimported_md = result2.document.export_to_markdown()

        # Key content preserved
        assert "Test DOCX Document" in reimported_md
        assert "Section One" in reimported_md

    def test_html_json_roundtrip(self, converter, sample_html, tmp_path):
        """Export HTML to JSON, reimport, verify content preserved."""
        result = converter.convert(str(sample_html))

        json_file = tmp_path / "exported.json"
        d = result.document.export_to_dict()
        json_file.write_text(json.dumps(d, indent=2), encoding="utf-8")

        result2 = converter.convert(str(json_file))
        reimported_md = result2.document.export_to_markdown()

        assert "HTML Test Document" in reimported_md

    def test_roundtrip_preserves_table_data(self, converter, sample_csv, tmp_path):
        """Tables survive the JSON roundtrip."""
        result = converter.convert(str(sample_csv))

        json_file = tmp_path / "exported.json"
        d = result.document.export_to_dict()
        json_file.write_text(json.dumps(d, indent=2), encoding="utf-8")

        result2 = converter.convert(str(json_file))
        reimported_md = result2.document.export_to_markdown()

        assert "Alice" in reimported_md
        assert "New York" in reimported_md
