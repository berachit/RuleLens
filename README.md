# RuleLens — Academic Regulations Contradiction Finder

> **Evidence first. Answer second.**  
> RuleLens is a verifiable AI assistant for university academic regulations. It answers queries grounded exclusively in a fixed regulatory corpus, providing exact citations and surfacing unresolved contradictions.

---

## 1. Project Mission & Core Rules

RuleLens is **not** a generic chatbot. Every query is classified into one of three primary public states:
- **`ANSWERED`**: The corpus contains sufficient, consistent evidence. Complete page-level provenance and citations are provided.
- **`NOT_COVERED`**: The corpus lacks sufficient information. The system refuses to answer rather than guessing or using external model knowledge.
- **`CONFLICT`**: Competing or contradictory provisions exist in the corpus. RuleLens presents both sides without arbitrarily picking a winner.

### Non-Negotiables
1. **The corpus is the sole authority.** Web search and LLM general knowledge are prohibited.
2. **Page-level provenance.** Every chunk preserves document ID, document name, page number, section, and chunk ID.
3. **No fabricated citations.** Citations must strictly originate from retrieved evidence metadata.
4. **Honest health states.** Infrastructure errors (DB offline, provider timeout) are reported as technical issues, never turned into false `NOT_COVERED` answers.

---

## 2. Architecture Overview

```
RuleLens/
├── backend/                  # FastAPI asynchronous REST API
│   ├── app/
│   │   ├── api/              # Route definitions (/api/health, /api/documents, /api/chat)
│   │   ├── config.py         # Pydantic BaseSettings loading from .env
│   │   ├── db/               # SQLAlchemy models & pgvector connection layer
│   │   └── services/         # Redis connection with graceful degradation & LLM abstraction
│   ├── tests/                # Automated pytest suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # React 18 + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/       # Header, HeroComposer, ChatInterface, SourceViewer, StatusBadge
│   │   ├── services/         # API client & health polling
│   │   └── index.css         # Editorial Minimalist tokens (OKLCH, Instrument Serif, Inter)
│   └── package.json
├── data/                     # Demo University regulations corpus (Phase 2)
│   └── raw/
├── evaluation/               # Benchmark suite & contradiction specs
│   └── contradictions.md
└── docker-compose.yml        # PostgreSQL (pgvector) & Redis services
```

---

## 3. Quickstart & Setup Guide

### Prerequisites
- **Python 3.11+** (Tested on Python 3.14)
- **Node.js 18+** and **npm**
- **Docker** (optional, for pgvector and Redis)

---

### Step 1: Database & Services (Docker or Local)

To start PostgreSQL with pgvector and Redis via Docker Compose:
```bash
docker compose up -d
```

*Note: If running PostgreSQL locally, ensure pgvector extension is available and configure credentials in `backend/.env`.*

---

### Step 2: Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Copy environment template:
   ```bash
   cp .env.example .env
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database schema (optional during scaffolding):
   ```bash
   python -m app.db.init_db
   ```

5. Run automated tests:
   ```bash
   python -m pytest tests/ -v
   ```

6. Start the FastAPI backend server:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

Verify backend health at [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health) and interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

---

### Step 3: Frontend Setup

1. In a separate terminal, navigate to `frontend`:
   ```bash
   cd frontend
   ```

2. Copy environment template:
   ```bash
   cp .env.example .env
   ```

3. Install Node dependencies:
   ```bash
   npm install
   ```

4. Start Vite development server:
   ```bash
   npm run dev
   ```

5. Open your browser at [http://localhost:5173](http://localhost:5173).

---

## 4. UI & Design System

RuleLens adopts an **Editorial Atelier Minimalist** design:
- **Display Typography**: `Instrument Serif` (brand and editorial titles)
- **Interface Typography**: `Inter` (functional UI, citations, body)
- **Palette**: Warm neutrals, hairline borders (`0.5px`), and restrained emerald accents.
- **ChatGPT-Style Composer**: The centered question composer is the dominant interaction.
- **Provenance Source Inspector**: Split-screen desktop panel and mobile sheet allowing instant inspection of cited pages and chunks.

---

## 5. Verification Checklist

- [x] Backend starts and serves `GET /api/health` with latency metrics and honest status.
- [x] Database configuration and Redis settings are cleanly isolated in `.env`.
- [x] Redis failure degrades gracefully without crashing the app.
- [x] Data models preserve complete provenance: Document → Page → Chunk → Citation.
- [x] 6,630-word Demo University 2026 corpus generated (Markdown + Table + PDF).
- [x] 3 deliberate contradictions planted and documented in `evaluation/contradictions.md`.
- [x] Embeddings generated with `BAAI/bge-small-en-v1.5` (384-dimensional).
- [x] Multi-provider LLM abstraction implemented (Gemini, Groq, Deterministic fallback).
- [x] Evidence sufficiency & contradiction engine classifying queries into `ANSWERED`, `NOT_COVERED`, and `CONFLICT`.
- [x] Provenance invariant strictly enforced on all citations.
- [x] Dark mode toggle with system default (`prefers-color-scheme: dark`) and `localStorage` persistence.
- [x] Frontend builds cleanly (`npm run build`) without TypeScript or lint warnings.
- [x] All 16 automated tests pass (`pytest backend/tests/ -v`).
- [x] No secrets or API keys committed.

---

## 6. Next Implementation Phase

- **Phase 4: Evaluation Benchmark & Suite**
  - Canonical `evaluation/questions.json` (20 answerable, 25 unanswerable refusals, 3 contradiction cases).
  - Executable benchmark script `run_eval.py` reporting accuracy, refusal accuracy, contradiction detection rate, and citation precision.
  - Evaluation results artifact and benchmark comparison.
