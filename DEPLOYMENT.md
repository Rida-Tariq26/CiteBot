# CiteBot — Production Deployment Runbook

This guide covers production deployment options for CiteBot, including Docker Compose and cloud VPS providers.

---

## 1. Environment Configuration

Create a `.env` file in the root directory:

```ini
APP_NAME=CiteBot
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# LLM Provider: "openai" or "mock" (offline zero-cost)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-openai-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Admin Security
ADMIN_API_KEY=your-secure-random-admin-secret-key-change-me

# Default Deployment Settings
DEFAULT_CLIENT_NAME="Acme Knowledge Assistant"
DEFAULT_ACCENT_COLOR="#2563EB"
DEFAULT_CONFIDENCE_THRESHOLD=0.45
```

---

## 2. Docker Compose Deployment (Recommended)

1. Build and start the container stack:
   ```bash
   docker compose up -d --build
   ```
2. Verify logs:
   ```bash
   docker compose logs -f
   ```
3. Test health check:
   ```bash
   curl http://localhost:8000/health
   ```
4. Access the web interface at `http://localhost:8000` (or behind an Nginx reverse proxy with SSL).

---

## 3. Reverse Proxy & SSL Setup (Nginx + Let's Encrypt)

```nginx
server {
    server_name citebot.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE Streaming headers
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/citebot.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/citebot.yourdomain.com/privkey.pem;
}
```

---

## 4. Disaster Recovery & Backups

All state is persisted in two locations:
1. `backend/citebot.db` (SQLite relational database of deployments, documents metadata, conversations, and usage logs).
2. `backend/storage/` (Raw document files and `vector_store.json` vector indices).

To perform a backup:
```bash
tar -czvf citebot-backup-$(date +%F).tar.gz backend/citebot.db backend/storage/
```
