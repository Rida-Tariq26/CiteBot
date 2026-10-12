from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import UsageLog
from app.schemas.log import UsageLogListResponse, UsageLogResponse

router = APIRouter(prefix="/logs", tags=["Usage Logs"])

@router.get("", response_model=UsageLogListResponse)
async def list_logs(
    deployment_id: str = settings.DEFAULT_DEPLOYMENT_ID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    x_admin_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    # Metrics
    total_query = select(func.count(UsageLog.id)).where(UsageLog.deployment_id == deployment_id)
    total_res = await db.execute(total_query)
    total = total_res.scalar_one() or 0

    refusals_query = select(func.count(UsageLog.id)).where(
        UsageLog.deployment_id == deployment_id,
        UsageLog.is_refusal == True
    )
    refusals_res = await db.execute(refusals_query)
    refusal_count = refusals_res.scalar_one() or 0

    avg_latency_query = select(func.avg(UsageLog.latency_ms)).where(UsageLog.deployment_id == deployment_id)
    avg_lat_res = await db.execute(avg_latency_query)
    avg_latency = float(avg_lat_res.scalar_one() or 0.0)

    # Log list
    logs_query = (
        select(UsageLog)
        .where(UsageLog.deployment_id == deployment_id)
        .order_by(UsageLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    logs_res = await db.execute(logs_query)
    logs = logs_res.scalars().all()

    refusal_rate = round(refusal_count / total, 3) if total > 0 else 0.0

    return UsageLogListResponse(
        logs=[UsageLogResponse.model_validate(l) for l in logs],
        total=total,
        total_queries=total,
        refusal_rate=refusal_rate,
        avg_latency_ms=round(avg_latency, 1)
    )
