# CiteBot — Development Specification

## 1. Project Overview

CiteBot is a standalone, white-label knowledge-assistant product. A business uploads its own documents — policies, manuals, contracts, reports, knowledge bases, FAQs — and CiteBot turns them into a conversational assistant that answers questions using only that content, with every claim backed by a visible, clickable citation back to the exact source passage.

CiteBot is not a general chatbot wrapper. Its defining behavior is that it never answers from general knowledge and never presents an unsupported claim as fact. If the uploaded documents don't contain the answer, CiteBot says so explicitly instead of guessing. This "cited or declined" behavior is the product's core identity and must be enforced at the architecture level, not just prompted for.

CiteBot is built to be deployed per-client (one instance/config per customer) as a productized service, demoed live, and delivered as a finished, branded deliverable — not a prototype or internal tool.

## 2. Product Goal

Give any business a trustworthy way to let visitors, employees, or customers query its documents in natural language, with:

- Zero hallucinated facts
- Full source traceability for every answer
- A professional, demo-ready interface suitable for showing to paying clients
- A codebase structured so it can be reconfigured for a new client's documents in hours, not days

## 3. Target Users & Use Cases

**Buyers (who commissions CiteBot):**
- Small-to-mid businesses wanting a "chat with our docs" feature on their website
- Teams needing an internal assistant over policy/procedure documents
- Consultants, agencies, or firms with dense reference material (compliance, HR handbooks, product manuals, research reports)

**End users (who talks to CiteBot):**
- A customer trying to find an answer in a product manual or policy without reading the whole document
- An employee looking up an internal procedure
- A researcher or analyst checking what a set of reports actually says

**Primary use cases:**
1. "What does section X of this policy say about Y?" — direct lookup with citation
2. "Summarize our refund policy" — synthesis across multiple passages, each cited
3. "Does this contract cover Z?" — yes/no with supporting excerpt, or explicit "not covered" if absent
4. Ambiguous or out-of-scope question — CiteBot declines and explains why, rather than guessing

## 4. Core Features

1. **Document ingestion** — upload PDF, DOCX, TXT, and Markdown files; the system chunks, embeds, and indexes them, preserving page/section metadata.
2. **Conversational chat interface** — multi-turn chat with memory of the current session's conversation.
3. **Inline citations** — every factual sentence in an answer carries a citation marker (e.g. `[1]`) linking to the source passage.
4. **Source panel** — a side panel or expandable section showing the exact retrieved passage(s), the source document name, and page/section number for each citation.
5. **Confidence-gated answering** — the system computes a retrieval-confidence signal per query; below threshold, it refuses to answer from guesswork and instead returns a defined "insufficient evidence" response.
6. **Conflicting-source handling** — when retrieved passages disagree, CiteBot surfaces both positions with their respective citations rather than silently picking one.
7. **Admin/config panel** — per-deployment settings: branding (name, logo, color), system prompt tone, refusal message wording, which documents are active, language.
8. **Document management** — list, re-index, or remove uploaded documents without redeploying the app.
9. **Embeddable widget** — a lightweight script-tag widget clients can drop into their own website, in addition to the standalone chat page.
10. **Usage logging** — store query/response/citation history per deployment for the client's own review (not used to retrain or share across clients).

## 5. User Flow

1. **Entry** — user lands on the chat page (standalone) or opens the embedded widget on a client's site.
2. **Empty state** — a welcome message states what CiteBot can answer about (derived from the active document set) and shows 2-3 example questions.
3. **Query submission** — user types a question; input is validated (non-empty, length-capped) before submission.
4. **Loading state** — a visible "searching documents" indicator appears immediately; streamed token output begins as soon as generation starts.
5. **Retrieval** — the backend retrieves the top-k relevant chunks, computes a confidence score.
6. **Branch:**
   - **Sufficient evidence** → generate a cited answer, stream it with inline markers, render the source panel.
   - **Insufficient evidence** → return the standard decline response (configurable wording), optionally suggesting a rephrase or listing which documents are loaded.
   - **Conflicting evidence** → generate an answer that explicitly presents both sides, each with its own citation.
7. **Follow-up** — user can ask a follow-up question; prior conversation turns are included as context for retrieval and generation.
8. **Citation interaction** — clicking a citation marker scrolls to / highlights the exact passage in the source panel; it does not leave the page.
9. **Session end** — conversation is available for the session; a "new chat" action clears context.

## 6. AI/RAG & Citation Logic

- **Chunking:** documents are split into overlapping chunks (target ~300-500 tokens, ~15% overlap) with metadata: document name, page number or section heading, chunk ID.
- **Embedding & storage:** chunks are embedded and stored in a vector database alongside their metadata, so every chunk returned from retrieval carries a traceable source reference.
- **Retrieval:** on each query, the system retrieves the top-k (configurable, default 5-8) most relevant chunks, using semantic similarity; a lightweight re-ranking step may reorder by relevance before generation.
- **Confidence scoring:** retrieval returns a similarity/relevance score per chunk. A query-level confidence score is derived (e.g. top-chunk score plus score spread) and compared against a configurable threshold.
- **Generation constraints:** the generation prompt must instruct the model to:
  - Answer only from the supplied chunks, never from general knowledge
  - Attach a citation marker to every sentence that asserts a fact
  - Map each citation marker to a specific chunk ID server-side (not trust the model's own numbering blindly — validate that every marker in the output corresponds to a real retrieved chunk)
  - Decline explicitly when chunks don't support an answer, using the configured refusal message rather than inventing one
- **Citation validation (server-side, post-generation):** before returning a response to the client, the backend parses citation markers out of the generated text and verifies each one references an actually-retrieved chunk. Any marker that doesn't resolve is stripped and logged as a generation anomaly; the response is not sent to the user with a dangling citation.
- **Conflicting sources:** if top retrieved chunks from different documents contain contradictory statements on the same point, the generation prompt instructs the model to present both, each with its own citation, rather than resolving the conflict itself.

## 7. Source Verification & Evidence Handling

- **Evidence requirement:** no sentence in a final answer may be presented as fact without a resolved citation to a retrieved chunk.
- **Insufficient evidence response:** a fixed, configurable message (e.g. "I couldn't find this in the current documents. Try rephrasing, or this may not be covered.") — never a best-guess answer.
- **Unsupported claims:** if the model's draft output contains an uncited factual sentence, the backend either (a) regenerates with a stricter prompt, or (b) strips the sentence and flags it, depending on configured strictness level.
- **Traceability:** every citation in the UI must be clickable and resolve to the literal passage and its document/page, so a user can verify the claim themselves without trusting the model.
- **Audit trail:** each response is stored with the chunks it was generated from, so a client can later audit any answer CiteBot gave.

## 8. Frontend & UI/UX

**Visual identity:** CiteBot should look like a polished, trustworthy SaaS product — not a generic chat demo. Clean typography, generous whitespace, a restrained color palette (one accent color, configurable per client), and clear visual separation between the conversation and the evidence panel.

**Layout:**
- Two-pane desktop layout: chat conversation on the left/center, collapsible source/evidence panel on the right.
- Mobile: source panel becomes a bottom sheet or modal triggered by tapping a citation.

**Key UI elements:**
- Message bubbles with distinct styling for user vs. CiteBot
- Inline citation chips (e.g. small numbered badges) inside assistant messages, clickable
- Source panel showing: document name, page/section, the exact excerpt (highlighted), and a "view full document" option if available
- Typing/streaming indicator during generation
- Empty state with example questions drawn from the active document set
- "No documents loaded" state for a fresh deployment, with a clear admin call-to-action
- Branding slot (logo, name, accent color) driven by per-deployment config

**UX requirements:**
- Response streaming (token-by-token or chunked) so the user sees progress, not a blank wait
- Citation markers appear only once the full response (and validated citations) are ready, to avoid showing unresolved references mid-stream — or, if streaming citations live, they must be visually marked "pending" until validated
- Clear, non-alarming styling for the decline/insufficient-evidence state (not styled as an error)
- Keyboard-accessible input and citation navigation

## 9. Backend & API Architecture

**Services:**
- **Ingestion service** — handles file upload, parsing (PDF/DOCX/TXT/MD), chunking, embedding, and writing to the vector store plus a metadata store.
- **Retrieval service** — given a query (and conversation context), returns ranked chunks with scores.
- **Generation service** — builds the constrained prompt, calls the LLM, streams output.
- **Citation validation layer** — sits between generation and the API response; parses and verifies citation markers against retrieved chunks before the response is returned.
- **Config service** — serves per-deployment settings (branding, thresholds, refusal wording, active documents).
- **Admin API** — document upload/list/delete, re-indexing, deployment configuration, usage log retrieval.

**API surface (REST, versioned, e.g. `/api/v1/...`):**
- `POST /chat` — accepts message + conversation ID, returns streamed response with resolved citations
- `POST /documents` — upload a document
- `GET /documents` — list active documents
- `DELETE /documents/{id}` — remove a document
- `GET /config` — fetch deployment branding/settings
- `PUT /config` — update deployment settings (admin-authenticated)
- `GET /conversations/{id}` — fetch conversation history

**Separation of concerns:** the generation service must never write directly to the response stream without passing through the citation validation layer first.

## 10. Database & Data Model

- **Documents** — id, deployment_id, filename, upload date, status (processing/ready/failed), page/section index
- **Chunks** — id, document_id, text, page/section reference, embedding vector, token count
- **Deployments** — id, client name, branding config, active document IDs, confidence threshold, refusal message, language
- **Conversations** — id, deployment_id, created_at, messages[]
- **Messages** — id, conversation_id, role (user/assistant), content, citations[] (chunk IDs + resolved excerpt), confidence score, timestamp
- **Usage logs** — query, response summary, citation count, confidence score, timestamp, deployment_id

Vector embeddings are stored in a dedicated vector database; relational/document data (deployments, conversations, documents metadata) in a standard database. The two must be kept in sync via the ingestion and deletion flows (deleting a document removes both its chunks from the vector store and its metadata record).

## 11. Security & Privacy

- Each deployment's documents and conversations are isolated from every other deployment (no cross-tenant data access).
- Admin endpoints (document upload/delete, config changes) require authentication; end-user chat endpoints may be public (for embeddable widget use) but rate-limited.
- Uploaded documents and derived chunks are stored only for the owning deployment; no document content is used to improve a shared/global model.
- File upload validation: type whitelist, size cap, and malware/content scanning before ingestion.
- All API traffic over HTTPS; secrets (API keys, DB credentials) managed via environment variables, never hardcoded.
- Input sanitization on chat messages to prevent prompt-injection attacks from user input or from malicious content embedded in uploaded documents (treat document content as untrusted text, not instructions).

## 12. Error Handling & Edge Cases

- **Upload failure** (corrupt file, unsupported type, size limit) → clear inline error, upload not silently dropped
- **Ingestion failure** (parsing error mid-document) → document marked "failed" with a reason, not left in a stuck "processing" state
- **Empty document set** → chat input disabled or warns the user no documents are loaded yet
- **Retrieval returns nothing** → treated as insufficient evidence, not a system error
- **LLM API failure/timeout** → user-facing retry option, no silent failure or infinite spinner
- **Malformed/unresolvable citation from the model** → stripped before display, logged server-side for monitoring, never shown broken in the UI
- **Very long user query** → validated/truncated with a clear message before submission
- **Conversation context overflow** (long chat history) → oldest turns summarized or dropped from context, with generation still working
- **Concurrent uploads** → queued and processed without blocking the chat interface

## 13. Performance & Scalability

- Retrieval and generation should be designed to handle multiple concurrent deployments, each with isolated document sets, without cross-contamination of results.
- Ingestion should run as an asynchronous background job so large document uploads don't block the UI.
- Vector store and chunking strategy should scale to at least tens of thousands of chunks per deployment without a significant retrieval latency increase.
- Response streaming should begin within a short, bounded time after query submission, independent of total answer length.
- Architecture should allow horizontal scaling of the retrieval/generation services independently of the ingestion service.

## 14. Deployment Requirements

- Fully containerized (Docker) for both the ingestion/backend services and the frontend, so a new client deployment can be stood up from a config file plus their documents.
- Environment-based configuration for API keys, database connections, and per-deployment branding.
- A documented deployment path (e.g. Docker Compose for self-hosting, plus a cloud deployment guide for a common provider).
- A deployment checklist/runbook so a new client instance can be launched without re-reading the full codebase each time.

## 15. Testing & Quality Assurance

- Unit tests for chunking, citation-marker parsing, and citation validation logic (these are the product's core trust mechanism and must be reliably tested).
- Integration tests covering the full flow: upload → ingest → query → cited response.
- Test cases specifically for: insufficient-evidence queries, conflicting-source queries, malformed citation output from the model, and empty-document-set state.
- Manual QA checklist for UI states: loading, streaming, empty, error, decline, and citation-click interactions.

## 16. Deliverables

- Full source code (frontend, backend, ingestion pipeline), organized into clearly separated modules per section 9
- Dockerfile(s) and deployment guide
- Admin configuration guide (how to onboard a new client/deployment)
- A seeded demo deployment with sample documents, ready to showcase live on the Contra profile
- Short handover documentation covering architecture, environment variables, and how to add a new client deployment

## 17. Acceptance Criteria

- [ ] Uploading a set of documents results in a queryable, cited chat assistant within the defined ingestion time
- [ ] Every factual sentence in a generated answer carries a citation that resolves to an actual retrieved passage
- [ ] Queries with no supporting evidence in the documents trigger the decline response, never a guessed answer
- [ ] Conflicting information across documents is presented as conflicting, with both sources cited
- [ ] Clicking any citation shows the exact source passage, document name, and location
- [ ] The interface reflects deployment-specific branding (name, logo, accent color) without code changes
- [ ] No deployment can access another deployment's documents or conversations
- [ ] The system handles upload failure, empty-document state, and LLM/API failure without breaking the UI
- [ ] The full stack runs via the documented Docker-based deployment path from a clean environment
- [ ] A live demo deployment is functional and ready to present to prospective Contra clients
