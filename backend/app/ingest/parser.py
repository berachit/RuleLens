import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union
from pypdf import PdfReader


@dataclass
class ParsedPage:
    page_number: int
    raw_text: str
    section_name: Optional[str] = None


@dataclass
class ParsedDocument:
    id: str
    name: str
    file_type: str
    title: str
    description: str
    pages: List[ParsedPage] = field(default_factory=list)


def parse_pdf_bytes(file_bytes: bytes, filename: str, doc_id: str, title: str, description: str) -> ParsedDocument:
    """Parses a paginated PDF document directly from memory bytes."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages: List[ParsedPage] = []

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        text = page.extract_text() or ""
        pages.append(ParsedPage(page_number=page_num, raw_text=text.strip()))

    return ParsedDocument(
        id=doc_id,
        name=filename,
        file_type="pdf",
        title=title,
        description=description,
        pages=pages,
    )


def parse_markdown_text(content: str, filename: str, doc_id: str, title: str, description: str) -> ParsedDocument:
    """Parses a markdown document directly from text into logical sections/pages."""
    chapters = content.split("## ")
    pages: List[ParsedPage] = []

    if chapters and chapters[0].strip():
        pages.append(ParsedPage(page_number=1, raw_text=chapters[0].strip(), section_name="Preamble"))

    for idx, chap in enumerate(chapters[1:], start=2):
        lines = chap.strip().split("\n", 1)
        section_title = lines[0].strip() if lines else f"Section {idx}"
        pages.append(ParsedPage(page_number=idx, raw_text="## " + chap.strip(), section_name=section_title))

    return ParsedDocument(
        id=doc_id,
        name=filename,
        file_type="markdown",
        title=title,
        description=description,
        pages=pages,
    )


def parse_pdf(pdf_path: Union[Path, str], doc_id: str, title: str, description: str) -> ParsedDocument:
    """Parses a PDF from file path."""
    path = Path(pdf_path)
    return parse_pdf_bytes(path.read_bytes(), path.name, doc_id, title, description)


def parse_markdown(md_path: Union[Path, str], doc_id: str, title: str, description: str) -> ParsedDocument:
    """Parses a Markdown file from file path."""
    path = Path(md_path)
    return parse_markdown_text(path.read_text(encoding="utf-8"), path.name, doc_id, title, description)
