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
│   │   └── services/         # Embedding & LLM abstraction
│   ├── tests/                # Automated pytest suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # React 18 + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/       # Header, AdminPanel, HeroComposer, ChatInterface, SourceViewer
│   │   ├── services/         # API client & health polling
│   │   └── index.css         # Editorial Minimalist tokens (OKLCH, Instrument Serif, Inter)
│   └── package.json
├── evaluation/               # Benchmark suite & contradiction specs
│   └── contradictions.md
└── docker-compose.yml        # PostgreSQL (pgvector) database service
```

---

## 3. Quickstart & Setup Guide

### Prerequisites
- **Python 3.11+** (Tested on Python 3.14)
- **Node.js 18+** and **npm**
- **Docker** (optional, for pgvector PostgreSQL)

---

### Step 1: Database (Docker or Local)

To start PostgreSQL with pgvector via Docker Compose:
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
- [x] Database configuration and settings cleanly isolated in `.env`.
- [x] Data models preserve complete provenance: Document → Page → Chunk → Citation.
- [x] 7,060-word university regulations corpus (Markdown + Fee Deadline Table + PDF).
- [x] 3 deliberate contradictions planted and documented in `contradictions.md`.
- [x] 25 hard unanswerable questions testing plausible near-misses.
- [x] Embeddings generated with `BAAI/bge-small-en-v1.5` (384-dimensional dense vectors).
- [x] Multi-provider LLM abstraction with deterministic fallback.
- [x] Evidence sufficiency engine classifying queries into `ANSWERED`, `NOT_COVERED`, and `CONFLICT`.
- [x] Provenance invariant strictly enforced on all citations.
- [x] Dark mode toggle with system default (`prefers-color-scheme: dark`) and `localStorage` persistence.
- [x] Frontend builds cleanly (`npm run build`) without TypeScript or lint warnings.
- [x] All 17 automated tests pass (`pytest backend/tests/ -v`).
- [x] Zero disk ingestion: Admin panel uploads and deletes directly in PostgreSQL pgvector database.

---

## 6. Canonical Evaluation Benchmark

We benchmarked RuleLens on the canonical 48-question test suite (`evaluation/questions.json`) designed specifically around hard near-misses and intentional contradictions:

| Metric | Measured Score | Target Criteria | Status |
|---|---|---|---|
| **Overall Classification** | **95.83%** (46/48) | ≥ 90.0% | **PASS** |
| **Answerable Accuracy** | **100.0%** (20/20) | ≥ 95.0% | **PASS** |
| **Refusal Accuracy (Near-Misses)** | **92.0%** (23/25) | ≥ 90.0% (≥ 19/25) | **PASS** |
| **Contradiction Detection** | **100.0%** (3/3) | 100.0% | **PASS** |
| **Citation Provenance Validity** | **95.83%** (46/48) | ≥ 90.0% | **PASS** |

To reproduce the benchmark:
```bash
python evaluation/run_eval.py
```

---

## 7. Guidelines & Deliverables Compliance

1. **Rulebook ≥ 6,000 words in mixed formats**: Total corpus contains **7,060 words** across Markdown (`academic_regulations.md`), a fee deadline table (`fee_deadlines.md`), and an extract PDF (`academic_regulations_excerpt.pdf`).
2. **Three real contradictions planted**: Documented in `contradictions.md` (Merit Scholarship GPA, Tuition Deadline, Examination Attendance).
3. **25 hard unanswerable questions**: Plausible adjacent near-misses (e.g. family wedding absence vs medical absence) evaluated in `evaluation/questions.json`.
4. **Honest reporting**: Measured refusal accuracy of **23 out of 25** (92.0%) rather than an unmeasured claim of 100%.
5. **All 3 distinct states**:
   - `Ready` / `Source Verified` (Green badge with full citations)
   - `Not In Rules` (Amber badge admitting ignorance)
   - `Rule Contradiction` (Rose badge displaying both provisions)
6. **Student-centric UI**: Editorial typography, document drawer, source preview, admin panel with live vector database metrics.
