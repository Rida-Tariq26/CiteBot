import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.models.entities import Deployment, Document, Chunk, generate_uuid
from app.services.ingestion import IngestionService
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store, VectorRecord
from sqlalchemy import select, delete

async def seed():
    print("[Seed] Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    demo_docs_dir = BASE_DIR.parent / "demo_docs"
    if not demo_docs_dir.exists():
        print(f"[Seed] Error: {demo_docs_dir} does not exist")
        return

    ingestion = IngestionService(chunk_size=350, overlap=50)

    async with AsyncSessionLocal() as db:
        # 1. Get or create deployment
        query = select(Deployment).where(Deployment.id == settings.DEFAULT_DEPLOYMENT_ID)
        res = await db.execute(query)
        dep = res.scalar_one_or_none()

        if not dep:
            print("[Seed] Creating default Acme deployment...")
            dep = Deployment(
                id=settings.DEFAULT_DEPLOYMENT_ID,
                client_name="Acme Corporation Knowledge Base",
                logo_url=None,
                accent_color="#2563EB",
                confidence_threshold=0.40,
                refusal_message="I couldn't find this information in the Acme Corporation documentation. Please verify your query or contact People Operations / Customer Support.",
                system_tone="direct, professional, and precise",
                language="en",
                starter_prompts=[
                    "What is the home office stipend amount and what does it cover?",
                    "How many weeks of paid parental leave are offered, and who qualifies?",
                    "What are the expense approval thresholds for staff vs contractors?",
                    "Can I get a refund on an annual subscription after 45 days?"
                ]
            )
            db.add(dep)
            await db.commit()
            await db.refresh(dep)
        else:
            print("[Seed] Default deployment exists.")

        # 2. Ingest demo documents
        doc_files = list(demo_docs_dir.glob("*.md"))
        print(f"[Seed] Found {len(doc_files)} demo documents.")

        for doc_file in doc_files:
            filename = doc_file.name
            with open(doc_file, "rb") as f:
                content_bytes = f.read()

            content_hash = ingestion.compute_sha256(content_bytes)

            # Check if document already exists
            existing_doc_res = await db.execute(
                select(Document).where(
                    Document.deployment_id == dep.id,
                    Document.filename == filename
                )
            )
            existing_doc = existing_doc_res.scalar_one_or_none()
            if existing_doc:
                print(f"[Seed] Document '{filename}' already registered. Removing old chunks to re-index...")
                await db.execute(delete(Chunk).where(Chunk.document_id == existing_doc.id))
                doc_record = existing_doc
            else:
                # Save file to storage
                storage_dir = Path(settings.STORAGE_DIR) / dep.id
                storage_dir.mkdir(parents=True, exist_ok=True)
                target_path = storage_dir / filename
                with open(target_path, "wb") as f_out:
                    f_out.write(content_bytes)

                doc_record = Document(
                    deployment_id=dep.id,
                    filename=filename,
                    file_type=".md",
                    file_size_bytes=len(content_bytes),
                    storage_path=str(target_path),
                    content_hash=content_hash,
                    status="processing"
                )
                db.add(doc_record)
                await db.commit()
                await db.refresh(doc_record)

            # Parse and chunk
            chunks_data, page_count = ingestion.process_file(filename, content_bytes)
            chunk_texts = [c.text for c in chunks_data]
            embeddings = await embedding_service.get_embeddings(chunk_texts)

            vector_records = []
            chunk_entities = []

            for c_data, emb in zip(chunks_data, embeddings):
                chunk_id = generate_uuid()
                c_entity = Chunk(
                    id=chunk_id,
                    document_id=doc_record.id,
                    deployment_id=dep.id,
                    chunk_index=c_data.chunk_index,
                    text=c_data.text,
                    page_number=c_data.page_number,
                    section_heading=c_data.section_heading,
                    token_count=c_data.token_count
                )
                chunk_entities.append(c_entity)
                vector_records.append(VectorRecord(
                    chunk_id=chunk_id,
                    document_id=doc_record.id,
                    deployment_id=dep.id,
                    text=c_data.text,
                    page_number=c_data.page_number,
                    section_heading=c_data.section_heading,
                    embedding=emb
                ))

            db.add_all(chunk_entities)
            doc_record.chunk_count = len(chunk_entities)
            doc_record.page_count = page_count
            doc_record.status = "ready"
            doc_record.error_message = None
            await db.commit()

            vector_store.add_records(dep.id, vector_records)
            print(f"[Seed] Successfully indexed '{filename}' ({len(chunk_entities)} chunks).")

    print("[Seed] Seed process completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed())
