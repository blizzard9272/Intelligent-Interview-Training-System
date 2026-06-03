from app.tasks.celery_app import celery_app


@celery_app.task(name="question_bank.generate")
def generate_question_bank(document_id: int) -> dict:
    return {
        "document_id": document_id,
        "status": "queued",
        "message": "题库生成任务骨架已创建，后续接入大模型抽题逻辑。",
    }
