import re
from typing import Optional
from app.schemas.chat import CitationItem
from app.services.vector_store import ScoredChunk

class CitationValidationResult:
    def __init__(
        self,
        cleaned_text: str,
        citations: list[CitationItem],
        anomalies_detected: int = 0,
        is_fully_cited: bool = True
    ):
        self.cleaned_text = cleaned_text
        self.citations = citations
        self.anomalies_detected = anomalies_detected
        self.is_fully_cited = is_fully_cited

class CitationValidator:
    def __init__(self):
        # Match [1], [2], [P1], [P2], etc.
        self.citation_pattern = re.compile(r"\[(?:P)?(\d+)\]")

    def validate_and_normalize(
        self,
        raw_text: str,
        retrieved_chunks: list[ScoredChunk],
        document_names: dict[str, str]
    ) -> CitationValidationResult:
        """
        Parses citation markers, validates them against retrieved chunks,
        normalizes them to sequential numbers [1], [2], ..., and returns
        the structured citations array for the UI evidence panel.
        """
        if not retrieved_chunks:
            # If no chunks were retrieved, strip any hallucinated citations
            cleaned = self.citation_pattern.sub("", raw_text).strip()
            return CitationValidationResult(
                cleaned_text=cleaned,
                citations=[],
                anomalies_detected=1 if self.citation_pattern.search(raw_text) else 0,
                is_fully_cited=False
            )

        # Mapping from chunk 1-based index (in retrieved_chunks) to ScoredChunk
        chunk_map = {idx + 1: chunk for idx, chunk in enumerate(retrieved_chunks)}

        # Find all cited indices in the text
        raw_markers = [int(m) for m in self.citation_pattern.findall(raw_text)]
        
        # Track valid vs invalid markers
        valid_used_indices: list[int] = []
        anomalies = 0

        for marker in raw_markers:
            if marker in chunk_map:
                if marker not in valid_used_indices:
                    valid_used_indices.append(marker)
            else:
                anomalies += 1

        # Build remapping dictionary: old_idx -> new 1-based sequential citation_number
        remap: dict[int, int] = {}
        citation_items: list[CitationItem] = []

        for new_num, old_num in enumerate(valid_used_indices, start=1):
            remap[old_num] = new_num
            chunk = chunk_map[old_num]
            doc_name = document_names.get(chunk.document_id, "Document")
            
            # Prepare a clean excerpt (first 250 characters of chunk)
            excerpt = chunk.text.strip()
            if len(excerpt) > 280:
                excerpt = excerpt[:280] + "..."

            citation_items.append(CitationItem(
                citation_number=new_num,
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                document_name=doc_name,
                page_number=chunk.page_number,
                section_heading=chunk.section_heading,
                excerpt=excerpt,
                similarity_score=round(chunk.score, 3)
            ))

        # Replace citation markers in text:
        # If valid, replace with remapped [new_num]; if invalid, remove marker.
        def replace_marker(match):
            val = int(match.group(1))
            if val in remap:
                return f"[{remap[val]}]"
            return ""

        cleaned_text = self.citation_pattern.sub(replace_marker, raw_text)
        # Clean up any duplicate spacing left by removed markers
        cleaned_text = re.sub(r"[ \t]+(\[[0-9]+\])", r" \1", cleaned_text)
        cleaned_text = re.sub(r"\s{2,}", " ", cleaned_text).strip()

        # Check if sentences have citations
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", cleaned_text) if len(s.strip()) > 20]
        uncited_sentences = [s for s in sentences if not self.citation_pattern.search(s)]
        is_fully_cited = len(uncited_sentences) == 0 or len(citation_items) > 0

        return CitationValidationResult(
            cleaned_text=cleaned_text,
            citations=citation_items,
            anomalies_detected=anomalies,
            is_fully_cited=is_fully_cited
        )

citation_validator = CitationValidator()
