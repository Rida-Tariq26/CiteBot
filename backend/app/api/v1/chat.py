import asyncio
import json
import time
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Deployment, Document, Conversation, Message, UsageLog
from app.schemas.chat import ChatRequest, ChatResponse, CitationItem
from app.services.retrieval import retrieval_service
from app.services.generation import generation_service
from app.api.v1.config import get_or_create_default_deployment

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    start_time = time.time()
    deployment_id = payload.deployment_id or settings.DEFAULT_DEPLOYMENT_ID
    deployment = await get_or_create_default_deployment(db, deployment_id)

    # Validate or create conversation
    conv: Conversation
    if payload.conversation_id:
        conv_query = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == payload.conversation_id)
        )
        res = await db.execute(conv_query)
        conv = res.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation
        title = payload.message[:40] + ("..." if len(payload.message) > 40 else "")
        conv = Conversation(deployment_id=deployment.id, title=title)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    # Fetch document name mappings
    docs_query = select(Document).where(
        Document.deployment_id == deployment.id,
        Document.status == "ready"
    )
    docs_res = await db.execute(docs_query)
    active_docs = docs_res.scalars().all()
    doc_map = {d.id: d.filename for d in active_docs}
    active_doc_ids = set(doc_map.keys())

    # Build chat history for contextualization safely without lazy loading
    msgs_query = (
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc())
        .limit(6)
    )
    msgs_res = await db.execute(msgs_query)
    recent_msgs = list(reversed(msgs_res.scalars().all()))
    chat_history = [{"role": m.role, "content": m.content} for m in recent_msgs]

    # Record User message
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=payload.message
    )
    db.add(user_msg)

    # Retrieval
    retrieval_res = await retrieval_service.retrieve(
        deployment_id=deployment.id,
        query=payload.message,
        chat_history=chat_history,
        confidence_threshold=deployment.confidence_threshold,
        top_k=settings.DEFAULT_TOP_K,
        active_document_ids=active_doc_ids
    )

    # Generation & Citation Validation
    raw_text, val_result, is_refusal = await generation_service.generate_response(
        query=payload.message,
        chunks=retrieval_res.chunks,
        document_names=doc_map,
        client_name=deployment.client_name,
        refusal_message=deployment.refusal_message,
        system_tone=deployment.system_tone,
        is_sufficient=retrieval_res.is_sufficient
    )

    # Convert citations to dictionaries for JSON storage
    citations_data = [c.model_dump() for c in val_result.citations]

    # Record Assistant message
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=val_result.cleaned_text,
        citations=citations_data,
        confidence_score=retrieval_res.confidence_score,
        is_refusal=is_refusal
    )
    db.add(assistant_msg)

    # Record usage log
    latency_ms = int((time.time() - start_time) * 1000)
    log = UsageLog(
        deployment_id=deployment.id,
        conversation_id=conv.id,
        query_text=payload.message,
        response_summary=val_result.cleaned_text[:200],
        citation_count=len(val_result.citations),
        confidence_score=retrieval_res.confidence_score,
        is_refusal=is_refusal,
        latency_ms=latency_ms
    )
    db.add(log)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatResponse(
        conversation_id=conv.id,
        message_id=assistant_msg.id,
        content=val_result.cleaned_text,
        citations=val_result.citations,
        is_refusal=is_refusal,
        confidence_score=retrieval_res.confidence_score,
        has_conflicts="differing" in val_result.cleaned_text.lower() or "conversely" in val_result.cleaned_text.lower()
    )

@router.post("/stream")
async def chat_stream_endpoint(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sentence-buffered SSE stream emitting verified tokens and validated citations
    """
    deployment_id = payload.deployment_id or settings.DEFAULT_DEPLOYMENT_ID
    deployment = await get_or_create_default_deployment(db, deployment_id)

    # Conversation handling
    if payload.conversation_id:
        conv_query = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == payload.conversation_id)
        )
        res = await db.execute(conv_query)
        conv = res.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        title = payload.message[:40] + ("..." if len(payload.message) > 40 else "")
        conv = Conversation(deployment_id=deployment.id, title=title)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)

    docs_query = select(Document).where(
        Document.deployment_id == deployment.id,
        Document.status == "ready"
    )
    docs_res = await db.execute(docs_query)
    active_docs = docs_res.scalars().all()
    doc_map = {d.id: d.filename for d in active_docs}
    active_doc_ids = set(doc_map.keys())

    msgs_query = (
        select(Message)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc())
        .limit(6)
    )
    msgs_res = await db.execute(msgs_query)
    recent_msgs = list(reversed(msgs_res.scalars().all()))
    chat_history = [{"role": m.role, "content": m.content} for m in recent_msgs]

    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=payload.message
    )
    db.add(user_msg)
    await db.commit()

    retrieval_res = await retrieval_service.retrieve(
        deployment_id=deployment.id,
        query=payload.message,
        chat_history=chat_history,
        confidence_threshold=deployment.confidence_threshold,
        top_k=settings.DEFAULT_TOP_K,
        active_document_ids=active_doc_ids
    )

    raw_text, val_result, is_refusal = await generation_service.generate_response(
        query=payload.message,
        chunks=retrieval_res.chunks,
        document_names=doc_map,
        client_name=deployment.client_name,
        refusal_message=deployment.refusal_message,
        system_tone=deployment.system_tone,
        is_sufficient=retrieval_res.is_sufficient
    )

    citations_data = [c.model_dump() for c in val_result.citations]
    assistant_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=val_result.cleaned_text,
        citations=citations_data,
        confidence_score=retrieval_res.confidence_score,
        is_refusal=is_refusal
    )
    db.add(assistant_msg)
    await db.commit()

    async def event_generator():
        # 1. Send conversation info event
        yield f"event: session\ndata: {json.dumps({'conversation_id': conv.id, 'message_id': assistant_msg.id})}\n\n"
        
        # 2. Stream tokens/words smoothly
        words = val_result.cleaned_text.split(" ")
        for i, word in enumerate(words):
            chunk_delta = word + (" " if i < len(words) - 1 else "")
            yield f"event: delta\ndata: {json.dumps({'delta': chunk_delta})}\n\n"
            await asyncio.sleep(0.015)

        # 3. Send validated citations and evidence panel data
        yield f"event: citations\ndata: {json.dumps({'citations': citations_data, 'confidence_score': retrieval_res.confidence_score, 'is_refusal': is_refusal})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
