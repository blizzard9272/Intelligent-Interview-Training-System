# Project Context

## 1. Project Goal

Build an interview training system with:

- user auth
- knowledge base management
- document upload and ingestion
- retrieval-augmented QA
- question generation
- interview simulation
- interview summary and long-term training analysis

## 2. Current Status

Implemented:

- FastAPI backend skeleton
- PostgreSQL + Alembic setup
- JWT auth
- knowledge base CRUD
- document upload
- task records
- real ingestion pipeline for `txt`, `md`, `pdf`
- local embedding for offline development
- Chroma persistence
- retrieval-backed QA with references
- frontend auth flow and protected routing
- frontend knowledge base and document management pages
- frontend QA page with knowledge base selection, session switching, answer display, and references
- QA session persistence and session detail retrieval
- frontend history page with real session list and detail rendering
- global API error popup on the frontend with Element Plus `ElMessage`
- backend exception handling with request logging
- QA fallback behavior:
  - answer from retrieved document context first
  - when no useful references exist, allow model fallback and prefix with `据我所知，`
- reusable frontend components extracted from QA and document pages
- question generation module with persistence
- interview session persistence
- interview page with multi-round follow-up flow
- automatic interview summary generation and persistence after session completion
- interview question selection by knowledge base, difficulty, and question type

Not implemented yet:

- rerank or hybrid retrieval
- richer interview orchestration strategy such as document-scoped drills and recent-question preference
- long-term interview analytics and weak-point tracking
- dedicated automated unit and integration tests for interview and question-generation modules
- LangGraph-based interview workflow

## 3. What Was Completed Today

Today the project moved from a basic interview MVP to a more usable training workflow:

- implemented interview summary generation as a reusable backend capability
- reused the `interview_summary` prompt and added local fallback when model generation fails
- persisted the generated summary as a session turn with role `interview_summary`
- exposed summary content and summary metadata in interview API responses
- added interview summary rendering to the frontend interview page
- added interview start filters for:
  - difficulty
  - question type
- returned question difficulty and tags through the interview API
- updated the interview page to support focused interview sessions
- verified the latest changes with backend compile and frontend build

## 4. Current Backend Decisions

- Framework: FastAPI
- Database: PostgreSQL
- Migrations: Alembic
- Vector store: Chroma
- Async mode now: FastAPI BackgroundTasks
- Embedding now: local hash embedding for development
- QA generation now: conditional Qwen chat provider with local grounded synthesis fallback
- Interview summary persistence now: stored as `InterviewTurn(role="interview_summary")`
- Interview question strategy now: filter on `QuestionBank.difficulty` and `QuestionBank.tags`

## 5. Current Mainline Flow

Auth flow:

- register
- login
- get current user

Knowledge base flow:

- create knowledge base
- list knowledge bases

Document flow:

- upload file
- create document record
- create ingestion task
- background ingestion
- parse file
- clean text
- split chunks
- compute local embeddings
- write to Chroma
- update task and document state

QA flow:

- accept question
- validate knowledge base access
- embed query
- retrieve chunks from Chroma
- generate answer through configured chat provider when available
- fall back to local grounded synthesis when online chat is unavailable
- if no retrieved references are useful, allow model-knowledge fallback with prefix `据我所知，`
- return references
- save session history

Question generation flow:

- select knowledge base and optional document
- read completed document chunks
- generate structured interview questions
- persist question, reference answer, tags, and difficulty

Interview flow:

- start interview session
- select a question by knowledge base and optional difficulty / question type
- persist turns for interviewer, candidate, feedback, follow-up, and summary
- generate follow-up questions until the configured round limit
- automatically generate and persist a session summary after completion

## 6. Recommended Next Steps

Priority 1:

- add interview orchestration controls:
  - source document filtering
  - recent-question preference
  - configurable question count or drill mode

Priority 2:

- add persistence-backed training analysis:
  - weak-point aggregation
  - repeated mistake themes
  - summary-based review suggestions

Priority 3:

- add automated tests for:
  - interview session start
  - filtered question selection
  - follow-up generation
  - summary generation fallback

Priority 4:

- explore rerank or hybrid retrieval to improve QA and question quality

## 7. Important Files

- `backend/app/services/qa_service.py`
- `backend/app/services/question_bank_service.py`
- `backend/app/services/interview_service.py`
- `backend/app/api/v1/endpoints/interview.py`
- `backend/app/schemas/interview.py`
- `backend/app/config/prompt.yaml`
- `frontend/src/views/documents/DocumentsView.vue`
- `frontend/src/views/qa/QAView.vue`
- `frontend/src/views/history/HistoryView.vue`
- `frontend/src/views/interview/InterviewView.vue`
- `frontend/src/api/interview.ts`

## 8. How Future Sessions Should Resume

When continuing this project:

1. Read this file and `docs/DEVELOPMENT_PLAN.md` first.
2. Keep the current PostgreSQL + Chroma + FastAPI architecture.
3. Treat the current interview module as the active mainline module.
4. Prefer building deeper interview training orchestration before more frontend polishing.
5. If adding summary persistence fields to the session table later, do it only when the current turn-based storage becomes a real limitation.
