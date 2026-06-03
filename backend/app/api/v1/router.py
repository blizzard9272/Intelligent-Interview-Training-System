from fastapi import APIRouter

from app.api.v1.endpoints import auth, documents, knowledge_bases, qa, question_bank, tasks

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(knowledge_bases.router, prefix="/knowledge-bases", tags=["knowledge-bases"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(qa.router, prefix="/qa", tags=["qa"])
api_router.include_router(question_bank.router, prefix="/question-bank", tags=["question-bank"])
