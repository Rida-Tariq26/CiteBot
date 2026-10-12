from typing import Optional
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store, ScoredChunk

class RetrievalResult:
    def __init__(
        self,
        chunks: list[ScoredChunk],
        confidence_score: float,
        is_sufficient: bool,
        reformulated_query: str
    ):
        self.chunks = chunks
        self.confidence_score = confidence_score
        self.is_sufficient = is_sufficient
        self.reformulated_query = reformulated_query

class RetrievalService:
    def __init__(self):
        pass

    def contextualize_query(self, current_query: str, chat_history: list[dict]) -> str:
        """
        Reformulates conversational follow-up questions to resolve pronouns
        and maintain topic context for semantic vector retrieval.
        """
        if not chat_history:
            return current_query

        # Look at last user turn and assistant response
        recent_user_turns = [m["content"] for m in chat_history if m.get("role") == "user"]
        if not recent_user_turns:
            return current_query

        last_user_query = recent_user_turns[-1]
        
        # Check if query has demonstratives / short ambiguous follow-ups
        short_followup_patterns = [
            "what about", "how about", "does this", "does it", "is there any",
            "can you explain", "who qualifies", "why", "and for", "what if"
        ]
        q_lower = current_query.lower()
        is_followup = any(p in q_lower for p in short_followup_patterns) or len(current_query.split()) < 5

        if is_followup:
            return f"{last_user_query} - {current_query}"
        return current_query

    def compute_confidence(self, chunks: list[ScoredChunk], threshold: float) -> tuple[float, bool]:
        """
        Calculates query-level confidence score based on top-k cosine similarity scores.
        """
        if not chunks:
            return 0.0, False

        top_score = max(c.score for c in chunks)
        # Average of top 3 scores if available
        top_k_scores = sorted([c.score for c in chunks], reverse=True)[:3]
        avg_top = sum(top_k_scores) / len(top_k_scores)
        
        # Combined confidence metric
        confidence = round(float((top_score * 0.7) + (avg_top * 0.3)), 3)
        # Clamp to [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))
        
        is_sufficient = confidence >= threshold
        return confidence, is_sufficient

    async def retrieve(
        self,
        deployment_id: str,
        query: str,
        chat_history: list[dict],
        confidence_threshold: float,
        top_k: int = 6,
        active_document_ids: Optional[set[str]] = None
    ) -> RetrievalResult:
        reformulated = self.contextualize_query(query, chat_history)
        query_vector = await embedding_service.get_embedding(reformulated)
        
        chunks = vector_store.search(
            deployment_id=deployment_id,
            query_vector=query_vector,
            top_k=top_k,
            active_document_ids=active_document_ids
        )

        confidence, is_sufficient = self.compute_confidence(chunks, confidence_threshold)

        return RetrievalResult(
            chunks=chunks,
            confidence_score=confidence,
            is_sufficient=is_sufficient,
            reformulated_query=reformulated
        )

retrieval_service = RetrievalService()
