import uuid
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from app.ingest.parser import ParsedDocument


@dataclass
class ChunkData:
    id: str
    document_id: str
    document_name: str
    document_title: str
    page_number: int
    section: Optional[str]
    text: str
    chunk_index: int
    metadata: Dict[str, Any]


def chunk_document(doc: ParsedDocument, max_chunk_words: int = 220, overlap_words: int = 40) -> List[ChunkData]:
    """Chunks a parsed document preserving page-level and section provenance."""
    chunks: List[ChunkData] = []
    global_chunk_idx = 0

    for page in doc.pages:
        raw_text = page.raw_text

        # Detect section headings within page (e.g. ### 7.2 General Attendance...)
        subsections = re.split(r'\n(?=###?\s+)', raw_text)

        for subsec in subsections:
            subsec_clean = subsec.strip()
            if not subsec_clean:
                continue

            # Extract section name if present
            current_section = page.section_name
            lines = subsec_clean.split("\n", 1)
            first_line = lines[0].strip()
            if first_line.startswith("#"):
                current_section = first_line.lstrip("#").strip()

            words = subsec_clean.split()
            if len(words) <= max_chunk_words:
                chunks.append(
                    ChunkData(
                        id=f"chk-{uuid.uuid4().hex[:12]}",
                        document_id=doc.id,
                        document_name=doc.name,
                        document_title=doc.title,
                        page_number=page.page_number,
                        section=current_section,
                        text=subsec_clean,
                        chunk_index=global_chunk_idx,
                        metadata={
                            "word_count": len(words),
                            "file_type": doc.file_type,
                        },
                    )
                )
                global_chunk_idx += 1
            else:
                # Sliding window chunking with overlap
                start = 0
                while start < len(words):
                    end = min(start + max_chunk_words, len(words))
                    chunk_words = words[start:end]
                    chunk_text = " ".join(chunk_words)

                    chunks.append(
                        ChunkData(
                            id=f"chk-{uuid.uuid4().hex[:12]}",
                            document_id=doc.id,
                            document_name=doc.name,
                            document_title=doc.title,
                            page_number=page.page_number,
                            section=current_section,
                            text=chunk_text,
                            chunk_index=global_chunk_idx,
                            metadata={
                                "word_count": len(chunk_words),
                                "file_type": doc.file_type,
                                "window": [start, end],
                            },
                        )
                    )
                    global_chunk_idx += 1

                    if end == len(words):
                        break
                    start += (max_chunk_words - overlap_words)

    return chunks
