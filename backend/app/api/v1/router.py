"""
API路由模块，定义了应用程序的主要API路由结构。
负责：汇总和组织各个功能模块的路由，包括认证auth、知识库knowledge-bases、文档documents、任务tasks、问答qa和题库question-bank等。
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, documents, interview, knowledge_bases, qa, question_bank, tasks

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(knowledge_bases.router, prefix="/knowledge-bases", tags=["knowledge-bases"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(qa.router, prefix="/qa", tags=["qa"])
api_router.include_router(question_bank.router, prefix="/question-bank", tags=["question-bank"])
api_router.include_router(interview.router, prefix="/interview", tags=["interview"])
