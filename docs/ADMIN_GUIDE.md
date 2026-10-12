# CiteBot — Admin & Client Onboarding Guide

CiteBot is an enterprise, factual document assistant product designed to be deployed for a client in **under an hour**. This guide explains how to onboard a new client, configure branding, upload documents, and tune confidence thresholds.

---

## 1. Fast Onboarding Workflow (Under 30 Minutes)

1. **Clone & Configure Environment**:
   ```bash
   cp .env.example .env
   # Set OPENAI_API_KEY if using OpenAI, or leave as mock for zero-cost offline demos
   ```
2. **Launch Application**:
   - Via Docker: `docker compose up -d`
   - Or local dev: 
     - Backend: `cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000`
     - Frontend: `cd frontend && npm run dev`
3. **Open the Admin Drawer**:
   - Navigate to `http://localhost:5173` (or production URL).
   - Click the **Admin** button in the top right.
4. **Upload Client Documents**:
   - Go to the **Documents** tab.
   - Drag and drop the client's PDF, DOCX, TXT, or Markdown documents (e.g. employee handbooks, refund policies, product manuals).
   - Ingestion automatically parses structural headings, computes page indices, generates token chunks (~400 tokens with 15% overlap), and embeds them.
5. **Customize Client Branding**:
   - Go to the **Branding & Rules** tab.
   - Enter the **Client Name** (e.g., *"Acme Corporation"*).
   - Select their **Accent Color** (e.g. `#2563EB` or custom brand hex).
   - Tune the **Confidence Threshold** (default: `0.45`).
   - Customize the **Refusal Message** (e.g. *"I couldn't find this information in the Acme Corporation policies..."*).
   - Add 3–4 **Starter Questions** specific to their business.
   - Click **Save Settings**.
6. **Deliver to Client**:
   - Share the standalone application URL, or
   - Copy the embed snippet from the **Embed Widget** tab and send it to their webmaster.

---

## 2. Tuning the Confidence Threshold

The confidence threshold controls the **"cited or declined" invariant**:

| Threshold Range | Behavior | Recommended Use Case |
| :--- | :--- | :--- |
| **0.30 – 0.40** | Lenient retrieval. Answers broader questions with looser semantic matches. | General marketing FAQs and broad knowledge bases. |
| **0.45 (Default)** | Balanced. Strict factual alignment with generous coverage. | Company internal handbooks, operations policies, HR guidelines. |
| **0.55 – 0.70** | Highly conservative. Refuses unless an exact, highly direct passage is found. | Legal contracts, regulatory compliance, medical guidelines. |

---

## 3. Embeddable Widget Integration

Clients can embed CiteBot onto their website with a single `<script>` tag:

```html
<script
  src="https://your-citebot-domain.com/widget.js"
  data-deployment-id="default"
  data-api-url="https://your-citebot-domain.com"
  defer
></script>
```

- Injects an isolated, shadow-DOM floating chat launcher in the bottom right corner.
- Completely isolated from host CSS rules.
- Supports mobile and desktop screens.
