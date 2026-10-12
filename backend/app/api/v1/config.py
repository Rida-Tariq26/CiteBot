from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Deployment, Document
from app.schemas.deployment import (
    DeploymentPublicConfig,
    DeploymentResponse,
    DeploymentUpdate,
)

router = APIRouter(prefix="/config", tags=["Configuration"])

async def get_or_create_default_deployment(db: AsyncSession, deployment_id: str) -> Deployment:
    query = select(Deployment).where(Deployment.id == deployment_id)
    result = await db.execute(query)
    deployment = result.scalar_one_or_none()
    
    if not deployment:
        deployment = Deployment(
            id=deployment_id,
            client_name=settings.DEFAULT_CLIENT_NAME,
            accent_color=settings.DEFAULT_ACCENT_COLOR,
            confidence_threshold=settings.DEFAULT_CONFIDENCE_THRESHOLD,
            refusal_message=settings.DEFAULT_REFUSAL_MESSAGE,
            system_tone=settings.DEFAULT_SYSTEM_TONE,
            language=settings.DEFAULT_LANGUAGE,
            starter_prompts=[
                "What is the company refund and cancellation policy?",
                "How do I submit an internal expense report?",
                "What are the eligibility requirements for parental leave?"
            ]
        )
        db.add(deployment)
        await db.commit()
        await db.refresh(deployment)
    
    return deployment

@router.get("", response_model=DeploymentPublicConfig)
async def get_public_config(
    deployment_id: str = settings.DEFAULT_DEPLOYMENT_ID,
    db: AsyncSession = Depends(get_db)
):
    deployment = await get_or_create_default_deployment(db, deployment_id)
    
    # Count ready documents
    doc_count_query = select(func.count(Document.id)).where(
        Document.deployment_id == deployment.id,
        Document.status == "ready"
    )
    doc_count_res = await db.execute(doc_count_query)
    doc_count = doc_count_res.scalar_one() or 0

    return DeploymentPublicConfig(
        id=deployment.id,
        client_name=deployment.client_name,
        logo_url=deployment.logo_url,
        accent_color=deployment.accent_color,
        refusal_message=deployment.refusal_message,
        starter_prompts=deployment.starter_prompts or [],
        active_document_count=doc_count,
        language=deployment.language
    )

@router.put("", response_model=DeploymentResponse)
async def update_config(
    payload: DeploymentUpdate,
    deployment_id: str = settings.DEFAULT_DEPLOYMENT_ID,
    x_admin_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    deployment = await get_or_create_default_deployment(db, deployment_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(deployment, field, val)

    await db.commit()
    await db.refresh(deployment)

    doc_count_query = select(func.count(Document.id)).where(
        Document.deployment_id == deployment.id,
        Document.status == "ready"
    )
    doc_count_res = await db.execute(doc_count_query)
    doc_count = doc_count_res.scalar_one() or 0

    resp = DeploymentResponse.model_validate(deployment)
    resp.active_document_count = doc_count
    return resp
