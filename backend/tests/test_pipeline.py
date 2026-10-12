import pytest
from app.services.retrieval import retrieval_service
from app.services.vector_store import ScoredChunk

def test_query_contextualization_followup():
    chat_history = [
        {"role": "user", "content": "What is the parental leave duration?"},
        {"role": "assistant", "content": "Full-time employees receive 16 weeks [1]."}
    ]
    follow_up = "Does it apply to adoption?"
    reformulated = retrieval_service.contextualize_query(follow_up, chat_history)

    assert "parental leave" in reformulated.lower()
    assert "adoption" in reformulated.lower()

def test_confidence_threshold_gating():
    # Low score chunks below threshold
    weak_chunks = [
        ScoredChunk(
            chunk_id="c1",
            document_id="d1",
            deployment_id="dep1",
            text="Unrelated company picnic notice.",
            page_number=1,
            section_heading="Social",
            score=0.21
        )
    ]
    confidence, is_sufficient = retrieval_service.compute_confidence(weak_chunks, threshold=0.45)
    assert is_sufficient is False
    assert confidence < 0.45

    # Strong score chunks above threshold
    strong_chunks = [
        ScoredChunk(
            chunk_id="c2",
            document_id="d1",
            deployment_id="dep1",
            text="Parental leave covers 16 weeks.",
            page_number=2,
            section_heading="Benefits",
            score=0.88
        )
    ]
    confidence, is_sufficient = retrieval_service.compute_confidence(strong_chunks, threshold=0.45)
    assert is_sufficient is True
    assert confidence >= 0.45
