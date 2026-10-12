import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings

@pytest.mark.asyncio
async def test_get_config():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "Acme" in data["client_name"]
        assert len(data["starter_prompts"]) > 0
        assert data["active_document_count"] >= 3

@pytest.mark.asyncio
async def test_list_documents():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/documents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3
        filenames = [d["filename"] for d in data["documents"]]
        assert "Acme_Employee_Handbook_2026.md" in filenames

@pytest.mark.asyncio
async def test_chat_factual_query_with_citations():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "How many weeks of paid parental leave are offered, and who qualifies?"
        }
        resp = await client.post("/api/v1/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_refusal"] is False
        assert len(data["citations"]) > 0
        assert "[1]" in data["content"]
        # Verify first citation
        c1 = data["citations"][0]
        assert c1["citation_number"] == 1
        assert "Handbook" in c1["document_name"]
        assert len(c1["excerpt"]) > 0

@pytest.mark.asyncio
async def test_chat_out_of_scope_query_triggers_refusal():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "message": "What is the secret recipe for Martian chocolate lava cake?"
        }
        resp = await client.post("/api/v1/chat", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_refusal"] is True
        assert len(data["citations"]) == 0
        assert "couldn't find" in data["content"].lower() or "documentation" in data["content"].lower()

@pytest.mark.asyncio
async def test_chat_multiturn_conversational_retrieval():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Turn 1
        t1 = await client.post("/api/v1/chat", json={"message": "What is the parental leave duration?"})
        assert t1.status_code == 200
        conv_id = t1.json()["conversation_id"]

        # Turn 2: Follow-up question using pronoun
        t2 = await client.post("/api/v1/chat", json={
            "message": "Does it apply to adoptive parents?",
            "conversation_id": conv_id
        })
        assert t2.status_code == 200
        t2_data = t2.json()
        assert t2_data["is_refusal"] is False
        assert len(t2_data["citations"]) > 0

@pytest.mark.asyncio
async def test_usage_logs_audit_trail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/logs", headers={"x-admin-key": settings.ADMIN_API_KEY})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] > 0
        assert len(data["logs"]) > 0
        assert data["logs"][0]["latency_ms"] >= 0
