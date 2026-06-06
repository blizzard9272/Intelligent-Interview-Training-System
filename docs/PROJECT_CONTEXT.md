# Project Context

## 1. Project Goal

Build an interview training system with:

- user auth
- knowledge base management
- document upload
- real document ingestion
- RAG-based QA
- future interview simulation with LangGraph and ReAct

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
- frontend documents, QA, and history pages cleaned up for readable Chinese copy

Not implemented yet:

- online embedding provider integration
- production-ready chat model generation with Qwen or DeepSeek as the default path
- rerank and hybrid retrieval
- real question generation workflow
- interview scoring and follow-up
- reusable frontend components for chat bubbles, reference cards, and session list items
- deeper frontend polish and interaction refinement beyond the current cleanup pass

## 3. Current Backend Decisions

- Framework: FastAPI
- Database: PostgreSQL
- Migrations: Alembic
- Vector store: Chroma
- Async mode now: FastAPI BackgroundTasks
- Embedding now: local hash embedding for development
- QA generation now: conditional Qwen chat provider with local grounded synthesis fallback

## 4. Current Backend Flow

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
- return references
- save session history

## 5. Immediate Next Steps

Priority 1:

- make Qwen or DeepSeek generation the stable default answer path
- improve timeout, error handling, and prompt behavior for online chat generation

Priority 2:

- extract reusable frontend components from `frontend/src/views/qa` and `frontend/src/views/history`
- continue polishing the QA workspace interaction and overall frontend consistency

Priority 3:

- add rerank or hybrid retrieval
- add question generation

## 6. Model Decision Pending

Chosen online model setup:

- Chat model: `qwen3.6-plus-2026-04-02`
- Embedding model: `text-embedding-v4`
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`

## 7. Important Files

- `backend/app/services/ingestion_service.py`
- `backend/app/services/qa_service.py`
- `backend/app/rag/vector_store.py`
- `backend/app/api/v1/endpoints/documents.py`
- `backend/app/api/v1/endpoints/qa.py`
- `backend/app/config/*.yaml`
- `frontend/src/views/documents/DocumentsView.vue`
- `frontend/src/views/qa/QAView.vue`
- `frontend/src/views/history/HistoryView.vue`

## 8. How Future Sessions Should Resume

When continuing this project:

1. Read this file first
2. Confirm whether the next task is backend model integration, frontend component extraction, or retrieval quality improvement
3. Preserve current PostgreSQL, Chroma, and ingestion architecture
4. Do not replace local embedding until online provider integration is ready
