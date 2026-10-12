import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_spa_and_widget_serving():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "<div id=\"root\">" in resp.text

        widget_resp = await client.get("/widget.js")
        assert widget_resp.status_code == 200
        assert "citebot-widget-root" in widget_resp.text
