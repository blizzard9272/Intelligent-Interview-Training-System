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
- frontend skeleton with auth, knowledge base, document pages

Not implemented yet:

- online embedding provider integration
- real chat model generation with Qwen or DeepSeek
- rerank and hybrid retrieval
- question generation workflow
- interview scoring and follow-up
- frontend QA page real interaction

## 3. Current Backend Decisions

- Framework: FastAPI
- Database: PostgreSQL
- Migrations: Alembic
- Vector store: Chroma
- Async mode now: FastAPI BackgroundTasks
- Embedding now: local hash embedding for development
- QA generation now: local grounded synthesis from retrieved snippets

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
- build grounded answer
- return references
- save session history

## 5. Immediate Next Steps

Priority 1:

- integrate real chat model provider
- replace local answer synthesis with Qwen or DeepSeek generation

Priority 2:

- build frontend QA page real interaction
- allow selecting knowledge base and viewing references

Priority 3:

- add rerank or hybrid retrieval
- add question generation

## 6. Model Decision Pending

Need user confirmation for first online chat model:

- Qwen
- DeepSeek

Suggested first choice:

- Qwen if DashScope API key is available

## 7. Important Files

- `backend/app/services/ingestion_service.py`
- `backend/app/services/qa_service.py`
- `backend/app/rag/vector_store.py`
- `backend/app/api/v1/endpoints/documents.py`
- `backend/app/api/v1/endpoints/qa.py`
- `backend/app/config/*.yaml`

## 8. How Future Sessions Should Resume

When continuing this project:

1. Read this file first
2. Confirm whether the next task is backend model integration or frontend QA integration
3. Preserve current PostgreSQL, Chroma, and ingestion architecture
4. Do not replace local embedding until online provider integration is ready
