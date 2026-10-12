import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Header, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Document, Chunk, Deployment, generate_uuid
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    ReindexResponse,
)
from app.services.ingestion import IngestionService
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store, VectorRecord

router = APIRouter(prefix="/documents", tags=["Documents"])
ingestion_service = IngestionService(
    chunk_size=settings.CHUNK_SIZE_TOKENS,
    overlap=settings.CHUNK_OVERLAP_TOKENS
)

@router.get("", response_model=DocumentListResponse)
async def list_documents(
    deployment_id: str = settings.DEFAULT_DEPLOYMENT_ID,
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Document)
        .where(Document.deployment_id == deployment_id)
        .order_by(Document.upload_date.desc())
    )
    result = await db.execute(query)
    docs = result.scalars().all()
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=len(docs)
    )

@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    deployment_id: str = settings.DEFAULT_DEPLOYMENT_ID,
    db: AsyncSession = Depends(get_db)
):
    # Verify file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Read content
    content_bytes = await file.read()
    file_size_mb = len(content_bytes) / (1024 * 1024)
    if file_size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Save to storage directory
    storage_dir = Path(settings.STORAGE_DIR) / deployment_id
    storage_dir.mkdir(parents=True, exist_ok=True)
    saved_path = storage_dir / file.filename
    with open(saved_path, "wb") as f:
        f.write(content_bytes)

    content_hash = ingestion_service.compute_sha256(content_bytes)

    # Create Document record
    doc_record = Document(
        deployment_id=deployment_id,
        filename=file.filename,
        file_type=ext,
        file_size_bytes=len(content_bytes),
        storage_path=str(saved_path),
        content_hash=content_hash,
        status="processing"
    )
    db.add(doc_record)
    await db.commit()
    await db.refresh(doc_record)

    # Process ingestion
    try:
        chunks_data, page_count = ingestion_service.process_file(file.filename, content_bytes)
        doc_record.page_count = page_count

        if not chunks_data:
            doc_record.status = "failed"
            doc_record.error_message = "No readable text content found in document"
            await db.commit()
            return DocumentResponse.model_validate(doc_record)

        # Generate embeddings
        chunk_texts = [c.text for c in chunks_data]
        embeddings = await embedding_service.get_embeddings(chunk_texts)

        vector_records: list[VectorRecord] = []
        chunk_entities: list[Chunk] = []

        for c_data, emb in zip(chunks_data, embeddings):
            chunk_id = generate_uuid()
            chunk_entity = Chunk(
                id=chunk_id,
                document_id=doc_record.id,
                deployment_id=deployment_id,
                chunk_index=c_data.chunk_index,
                text=c_data.text,
                page_number=c_data.page_number,
                section_heading=c_data.section_heading,
                token_count=c_data.token_count
            )
            chunk_entities.append(chunk_entity)

            vector_records.append(VectorRecord(
                chunk_id=chunk_id,
                document_id=doc_record.id,
                deployment_id=deployment_id,
                text=c_data.text,
                page_number=c_data.page_number,
                section_heading=c_data.section_heading,
                embedding=emb
            ))

        db.add_all(chunk_entities)
        doc_record.chunk_count = len(chunk_entities)
        doc_record.status = "ready"
        doc_record.error_message = None
        await db.commit()

        # Add to vector store index
        vector_store.add_records(deployment_id, vector_records)
        await db.refresh(doc_record)

        return DocumentResponse.model_validate(doc_record)

    except Exception as e:
        doc_record.status = "failed"
        doc_record.error_message = f"Ingestion error: {str(e)}"
        await db.commit()
        await db.refresh(doc_record)
        return DocumentResponse.model_validate(doc_record)

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    deployment_id: str = settings.DEFAULT_DEPLOYMENT_ID,
    x_admin_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    query = select(Document).where(
        Document.id == document_id,
        Document.deployment_id == deployment_id
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove file on disk if exists
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except Exception:
            pass

    # Delete chunks and doc in DB
    await db.delete(doc)
    await db.commit()

    # Synchronize vector store
    vector_store.delete_document(deployment_id, document_id)

    return {"status": "success", "message": f"Document {document_id} and associated chunks deleted"}

@router.post("/reindex", response_model=ReindexResponse)
async def reindex_documents(
    deployment_id: str = settings.DEFAULT_DEPLOYMENT_ID,
    x_admin_key: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if x_admin_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    docs_query = select(Document).where(Document.deployment_id == deployment_id)
    result = await db.execute(docs_query)
    docs = result.scalars().all()

    total_chunks = 0
    processed_count = 0

    # Clear vectors for this deployment
    vector_store.delete_deployment(deployment_id)

    for doc in docs:
        if not os.path.exists(doc.storage_path):
            continue
        try:
            with open(doc.storage_path, "rb") as f:
                content_bytes = f.read()

            # Delete old chunks in DB
            await db.execute(delete(Chunk).where(Chunk.document_id == doc.id))

            chunks_data, page_count = ingestion_service.process_file(doc.filename, content_bytes)
            chunk_texts = [c.text for c in chunks_data]
            embeddings = await embedding_service.get_embeddings(chunk_texts)

            vector_records = []
            chunk_entities = []

            for c_data, emb in zip(chunks_data, embeddings):
                chunk_id = generate_uuid()
                c_entity = Chunk(
                    id=chunk_id,
                    document_id=doc.id,
                    deployment_id=deployment_id,
                    chunk_index=c_data.chunk_index,
                    text=c_data.text,
                    page_number=c_data.page_number,
                    section_heading=c_data.section_heading,
                    token_count=c_data.token_count
                )
                chunk_entities.append(c_entity)
                vector_records.append(VectorRecord(
                    chunk_id=chunk_id,
                    document_id=doc.id,
                    deployment_id=deployment_id,
                    text=c_data.text,
                    page_number=c_data.page_number,
                    section_heading=c_data.section_heading,
                    embedding=emb
                ))

            db.add_all(chunk_entities)
            doc.chunk_count = len(chunk_entities)
            doc.page_count = page_count
            doc.status = "ready"
            vector_store.add_records(deployment_id, vector_records)

            total_chunks += len(chunk_entities)
            processed_count += 1
        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)

    await db.commit()
    return ReindexResponse(
        status="completed",
        processed_count=processed_count,
        total_chunks=total_chunks
    )
