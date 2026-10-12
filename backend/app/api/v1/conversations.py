from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Conversation, Message
from app.schemas.conversation import ConversationResponse, MessageResponse

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.post("", response_model=ConversationResponse)
async def create_conversation(
    deployment_id: str = settings.DEFAULT_DEPLOYMENT_ID,
    title: str = "New Chat",
    db: AsyncSession = Depends(get_db)
):
    conv = Conversation(
        deployment_id=deployment_id,
        title=title
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return ConversationResponse(
        id=conv.id,
        deployment_id=conv.deployment_id,
        title=conv.title,
        messages=[],
        created_at=conv.created_at,
        updated_at=conv.updated_at
    )

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    result = await db.execute(query)
    conv = result.scalar_one_or_none()

    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages_resp = [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            citations=m.citations or [],
            confidence_score=m.confidence_score,
            is_refusal=m.is_refusal,
            created_at=m.created_at
        )
        for m in conv.messages
    ]

    return ConversationResponse(
        id=conv.id,
        deployment_id=conv.deployment_id,
        title=conv.title,
        messages=messages_resp,
        created_at=conv.created_at,
        updated_at=conv.updated_at
    )

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db)
):
    query = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(query)
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    await db.commit()
    return {"status": "success", "message": "Conversation cleared"}
