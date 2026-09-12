from typing import List, Dict, Any


def validate_citations(
    candidate_chunks: List[Dict[str, Any]],
    max_citations: int = 4,
) -> List[Dict[str, Any]]:
    """Strictly validates and formats citations from retrieved evidence metadata.

    Enforces the Provenance Invariant:
    Every emitted citation must trace directly to a real, retrieved chunk
    with valid document name, page number, chunk ID, and source text snippet.
    """
    valid_citations = []
    seen_chunks = set()

    for chunk in candidate_chunks:
        chunk_id = chunk.get("chunk_id")
        doc_name = chunk.get("document_name")
        page_num = chunk.get("page_number")

        # Provenance Invariant: must possess chunk_id, document, and page
        if not chunk_id or not doc_name or page_num is None:
            continue

        if chunk_id in seen_chunks:
            continue

        seen_chunks.add(chunk_id)

        # Build clean citation object
        text_snippet = chunk.get("text", "")
        # Shorten snippet if too long
        snippet = text_snippet[:350] + ("..." if len(text_snippet) > 350 else "")

        valid_citations.append({
            "document": doc_name,
            "page": int(page_num),
            "section": chunk.get("section") or "General Section",
            "chunk_id": chunk_id,
            "text_snippet": snippet,
        })

        if len(valid_citations) >= max_citations:
            break

    return valid_citations
