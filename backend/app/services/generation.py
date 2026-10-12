import json
import re
from typing import AsyncGenerator, Optional
import httpx
from app.core.config import settings
from app.services.vector_store import ScoredChunk
from app.services.citation import citation_validator, CitationValidationResult

SYSTEM_PROMPT_TEMPLATE = """You are CiteBot, an AI knowledge assistant for {client_name}.
Your defining behavior is that you NEVER answer from general knowledge and NEVER present an unsupported claim as fact.
You answer questions using ONLY the provided document passages.

STRICT OPERATING RULES:
1. Every single sentence that asserts a fact MUST end with a citation marker, e.g. [P1] or [P2], referring to the passage number.
2. Only use passages provided below under "PASSAGES". Do not invent or assume any facts.
3. If the provided passages do not contain sufficient evidence to answer the question, or if you are uncertain, you MUST decline using this exact message:
"{refusal_message}"
4. If different passages contradict or conflict with each other, present BOTH perspectives clearly with their respective citations (e.g. "Document A states X [P1], while Document B specifies Y [P2]").
5. Tone: Maintain a {system_tone} tone. Keep your answer concise, direct, and factual.

PASSAGES:
{passages_text}
"""

class GenerationService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.openai_key = settings.OPENAI_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY

    def build_prompt(
        self,
        client_name: str,
        refusal_message: str,
        system_tone: str,
        chunks: list[ScoredChunk]
    ) -> str:
        passages_parts = []
        for idx, chunk in enumerate(chunks, start=1):
            heading_info = f" | Section: {chunk.section_heading}" if chunk.section_heading else ""
            page_info = f" | Page: {chunk.page_number}" if chunk.page_number else ""
            passages_parts.append(
                f"[P{idx}] (DocID: {chunk.document_id}{page_info}{heading_info}):\n{chunk.text.strip()}"
            )
        
        passages_text = "\n\n".join(passages_parts) if passages_parts else "No relevant passages found."
        
        return SYSTEM_PROMPT_TEMPLATE.format(
            client_name=client_name,
            refusal_message=refusal_message,
            system_tone=system_tone,
            passages_text=passages_text
        )

    async def generate_response(
        self,
        query: str,
        chunks: list[ScoredChunk],
        document_names: dict[str, str],
        client_name: str,
        refusal_message: str,
        system_tone: str,
        is_sufficient: bool
    ) -> tuple[str, CitationValidationResult, bool]:
        """
        Generates response and passes it through the Citation Validation Layer.
        Returns: (raw_generated_text, validated_result, is_refusal)
        """
        # If retrieval confidence is below threshold, directly return refusal
        if not is_sufficient or not chunks:
            val_result = citation_validator.validate_and_normalize(refusal_message, [], document_names)
            return refusal_message, val_result, True

        # Call configured LLM provider
        raw_text = ""
        if self.provider == "openai" and self.openai_key:
            raw_text = await self._call_openai(query, chunks, client_name, refusal_message, system_tone)
        elif self.provider == "gemini" and self.gemini_key:
            raw_text = await self._call_gemini(query, chunks, client_name, refusal_message, system_tone)
        else:
            raw_text = self._generate_offline(query, chunks, refusal_message)

        # Check if the output is a refusal
        is_refusal = (
            refusal_message.lower() in raw_text.lower() or
            "couldn't find" in raw_text.lower() or
            "do not contain" in raw_text.lower()
        )

        # Pass through the Citation Validation Layer
        val_result = citation_validator.validate_and_normalize(
            raw_text,
            chunks,
            document_names
        )

        return raw_text, val_result, is_refusal

    async def _call_openai(
        self,
        query: str,
        chunks: list[ScoredChunk],
        client_name: str,
        refusal_message: str,
        system_tone: str
    ) -> str:
        prompt = self.build_prompt(client_name, refusal_message, system_tone, chunks)
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ]
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": messages,
                    "temperature": 0.0
                }
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    async def _call_gemini(
        self,
        query: str,
        chunks: list[ScoredChunk],
        client_name: str,
        refusal_message: str,
        system_tone: str
    ) -> str:
        prompt = self.build_prompt(client_name, refusal_message, system_tone, chunks)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{prompt}\n\nUser Question: {query}"}]}
            ],
            "generationConfig": {"temperature": 0.0}
        }
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()

    def _generate_offline(
        self,
        query: str,
        chunks: list[ScoredChunk],
        refusal_message: str
    ) -> str:
        """
        High-fidelity offline generator for testing, seed demos, and air-gapped environments.
        Synthesizes factual answers directly from top chunks with [P1], [P2] markers.
        """
        if not chunks:
            return refusal_message

        # Detect potential conflicts across different chunks
        top_chunks = chunks[:3]
        if len(top_chunks) >= 2 and top_chunks[0].document_id != top_chunks[1].document_id:
            # Check for conflict keywords in text
            t1 = top_chunks[0].text.lower()
            t2 = top_chunks[1].text.lower()
            conflict_words = ["however", "whereas", "differs", "updated", "effective", "supersedes", "revised"]
            if any(w in t1 or w in t2 for w in conflict_words):
                return (
                    f"The retrieved documents present differing information on this topic. "
                    f"First, {top_chunks[0].text.strip()[:180]}... [P1]. "
                    f"Conversely, {top_chunks[1].text.strip()[:180]}... [P2]."
                )

        # Standard extraction synthesis
        primary_chunk = top_chunks[0]
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", primary_chunk.text) if len(s.strip()) > 20]
        
        if not sentences:
            return f"{primary_chunk.text.strip()} [P1]"

        # Pick top relevant sentence matching query terms
        query_terms = set(re.findall(r"\w+", query.lower()))
        scored_sentences = []
        for s in sentences:
            s_terms = set(re.findall(r"\w+", s.lower()))
            overlap = len(query_terms.intersection(s_terms))
            scored_sentences.append((overlap, s))

        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        best_sentence = scored_sentences[0][1] if scored_sentences else sentences[0]

        answer = f"Based on the documentation, {best_sentence} [P1]."
        if len(top_chunks) > 1 and len(sentences) > 1:
            second_sentence = scored_sentences[1][1] if len(scored_sentences) > 1 else sentences[1]
            answer += f" Additionally, {second_sentence} [P1]."

        return answer

generation_service = GenerationService()
