import pytest
from app.services.citation import citation_validator
from app.services.vector_store import ScoredChunk

def test_citation_mapping_and_reordering():
    chunks = [
        ScoredChunk(
            chunk_id="chunk_1",
            document_id="doc_a",
            deployment_id="dep_1",
            text="Employees receive 15 days of PTO.",
            page_number=3,
            section_heading="PTO Policy",
            score=0.92
        ),
        ScoredChunk(
            chunk_id="chunk_2",
            document_id="doc_b",
            deployment_id="dep_1",
            text="Unused PTO rolls over up to 5 days max.",
            page_number=4,
            section_heading="Rollover",
            score=0.85
        )
    ]
    doc_names = {"doc_a": "Handbook.pdf", "doc_b": "Benefits.docx"}

    raw_text = "Employees receive 15 days of PTO [P1]. Unused PTO rolls over up to 5 days [P2]."
    result = citation_validator.validate_and_normalize(raw_text, chunks, doc_names)

    assert "[1]" in result.cleaned_text
    assert "[2]" in result.cleaned_text
    assert len(result.citations) == 2
    assert result.citations[0].document_name == "Handbook.pdf"
    assert result.citations[0].page_number == 3
    assert result.citations[1].document_name == "Benefits.docx"
    assert result.anomalies_detected == 0

def test_hallucinated_citation_stripped():
    chunks = [
        ScoredChunk(
            chunk_id="chunk_1",
            document_id="doc_a",
            deployment_id="dep_1",
            text="Employees receive 15 days of PTO.",
            page_number=3,
            section_heading="PTO Policy",
            score=0.92
        )
    ]
    doc_names = {"doc_a": "Handbook.pdf"}

    # Model hallucinates [P9] which does not exist in retrieved chunks
    raw_text = "Employees receive 15 days of PTO [P1]. Health insurance covers dental [P9]."
    result = citation_validator.validate_and_normalize(raw_text, chunks, doc_names)

    # [1] is kept, [9] is stripped
    assert "[1]" in result.cleaned_text
    assert "[9]" not in result.cleaned_text
    assert "[P9]" not in result.cleaned_text
    assert len(result.citations) == 1
    assert result.anomalies_detected == 1
