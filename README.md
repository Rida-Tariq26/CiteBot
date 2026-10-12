# CiteBot — Factual AI Document Assistant

[![Tests](https://img.shields.io/badge/tests-13%20passed-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)]()
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()

> **"Cited or Declined"**: CiteBot is a standalone, white-label AI knowledge-assistant that answers questions using **only** uploaded enterprise documents. Every single factual claim is backed by a visible, clickable citation linking directly to the source passage. If the answer cannot be proven from the documents, CiteBot explicitly declines instead of hallucinating.

---

## Key Features

1. **Deterministic Citations (`[1]`, `[2]`)**:
   Every factual sentence carries an inline citation chip. Clicking a citation highlights the exact excerpt, document name, section heading, and page number in the Evidence Panel.
2. **Confidence-Gated Refusal ("Cited or Declined")**:
   Computes retrieval relevance confidence per query against a configurable threshold. If confidence falls below the cutoff, it returns a defined refusal response with zero guesswork.
3. **Contradiction & Conflicting Source Handling**:
   When different documents contain differing policies or terms (e.g. employee handbook vs. contractor addendum), CiteBot surfaces both perspectives with their respective citations rather than guessing.
4. **Multi-Turn Contextual Retrieval**:
   Maintains conversation memory across turns, automatically resolving conversational follow-ups and pronouns to retrieve the correct context.
5. **Turnkey White-Label Customization**:
   Admin Drawer allows live configuration of client name, custom accent color, refusal message wording, and confidence thresholds without code changes.
6. **Multi-Format Ingestion**:
   Native parsing and chunking for **PDF**, **DOCX**, **Markdown**, and **TXT** with structural section tracking and token-based chunk overlap.
7. **Embeddable Website Widget (`widget.js`)**:
   A standalone, isolated `<script>` tag widget that clients can drop into any external website.
8. **Audit Trail & Usage Logging**:
   Complete query logs, citation metrics, latency tracking, and refusal rates for client review.

---

## Quickstart

### Option A: Local Development (Instant Zero-Config)

#### 1. Setup Backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python scripts/seed_demo.py
python -m uvicorn app.main:app --port 8000 --reload
```

#### 2. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:5173`.

---

### Option B: Production Docker Deployment

```bash
docker compose up -d --build
```

Access the unified full-stack application at `http://localhost:8000`.

---

## Architecture Overview

```
CiteBot/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST & SSE Streaming API endpoints
│   │   │   ├── chat.py      # POST /chat and /chat/stream
│   │   │   ├── documents.py # Ingestion, list, delete, reindex
│   │   │   ├── config.py    # Public branding & admin settings
│   │   │   ├── conversations.py # Multi-turn sessions
│   │   │   └── logs.py      # Usage analytics & audit trails
│   │   ├── core/            # Config & async database engine
│   │   ├── models/          # SQLAlchemy async models
│   │   ├── schemas/         # Pydantic validation schemas
│   │   └── services/        # RAG pipeline services
│   │       ├── ingestion.py # PDF/DOCX/MD parsers & token chunker
│   │       ├── embeddings.py# Offline hash vectorizer & OpenAI
│   │       ├── vector_store.py # Persistent cosine similarity vector engine
│   │       ├── retrieval.py # Contextualizer & confidence scorer
│   │       ├── generation.py# Constrained prompts & LLM client
│   │       └── citation.py  # Server-side citation validator & cleaner
│   ├── scripts/
│   │   └── seed_demo.py     # Demo database seeder
│   └── tests/               # 13 automated unit & E2E integration tests
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Header.jsx
│   │   │   ├── ChatArea.jsx
│   │   │   ├── SourcePanel.jsx
│   │   │   ├── AdminDrawer.jsx
│   │   │   └── CitationChip.jsx
│   │   ├── App.jsx          # Root application
│   │   └── main.jsx
│   └── public/
│       └── widget.js        # Standalone embeddable website widget
├── demo_docs/               # Seeded enterprise sample knowledge base
├── Dockerfile               # Multi-stage production container
├── docker-compose.yml       # Production Compose configuration
├── DEPLOYMENT.md            # Production deployment runbook
└── docs/
    └── ADMIN_GUIDE.md       # Client onboarding and tuning guide
```

---

## Demo Knowledge Base

CiteBot comes pre-seeded with 3 realistic enterprise documents in `demo_docs/`:
- `Acme_Employee_Handbook_2026.md` (Parental leave, remote work stipend, PTO rollover, $50 expense threshold)
- `Acme_Customer_Support_and_Refund_Policy.md` (30-day money-back guarantee, hardware warranty, SLA credits)
- `Acme_Contract_Vendor_Addendum_2026.md` (Vendor terms, Net 30, $75 expense threshold conflict case)

### Sample Test Questions
| Query | Expected Outcome |
| :--- | :--- |
| *"How many weeks of paid parental leave are offered, and who qualifies?"* | Answers 16 weeks, citing Employee Handbook § 3 `[1]`. |
| *"What is the home office stipend amount and what does it cover?"* | Answers $1,200, citing Employee Handbook § 2 `[1]`. |
| *"What are the expense approval thresholds for staff vs contractors?"* | Detects conflict ($50 for staff vs $75 for contractors), citing both `[1]` and `[2]`. |
| *"What is the secret recipe for Martian chocolate cake?"* | Declines gracefully with refusal notice (confidence below threshold). |

---

## Running the Automated Test Suite

```bash
cd backend
.venv\Scripts\python -m pytest tests -v
```

All 13 automated tests cover:
- Preserving section headings and page indices across Markdown and PDF chunks
- Chunk overlap and boundary handling
- Inline citation remapping and normalization (`[1]`, `[2]`)
- Stripping hallucinated citations from model outputs
- Out-of-scope confidence gating and refusal triggering
- Conversational query contextualization for multi-turn pronouns
- Static SPA and `widget.js` bundle delivery
- End-to-end API integration
