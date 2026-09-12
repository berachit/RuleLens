from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
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


def parse_pdf(pdf_path: Path, doc_id: str, title: str, description: str) -> ParsedDocument:
    """Parses a paginated PDF document, preserving page-level provenance."""
    reader = PdfReader(str(pdf_path))
    pages: List[ParsedPage] = []

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        text = page.extract_text() or ""
        pages.append(ParsedPage(page_number=page_num, raw_text=text.strip()))

    return ParsedDocument(
        id=doc_id,
        name=pdf_path.name,
        file_type="pdf",
        title=title,
        description=description,
        pages=pages,
    )


def parse_markdown(md_path: Path, doc_id: str, title: str, description: str) -> ParsedDocument:
    """Parses a markdown document into logical chapters/pages."""
    content = md_path.read_text(encoding="utf-8")
    # Break into logical chapters by '## Chapter' or '## '
    chapters = content.split("## ")
    pages: List[ParsedPage] = []

    # First section before first ## (Title/Preamble)
    if chapters and chapters[0].strip():
        pages.append(ParsedPage(page_number=1, raw_text=chapters[0].strip(), section_name="Preamble"))

    for idx, chap in enumerate(chapters[1:], start=2):
        lines = chap.strip().split("\n", 1)
        section_title = lines[0].strip() if lines else f"Section {idx}"
        pages.append(ParsedPage(page_number=idx, raw_text="## " + chap.strip(), section_name=section_title))

    return ParsedDocument(
        id=doc_id,
        name=md_path.name,
        file_type="markdown",
        title=title,
        description=description,
        pages=pages,
    )
