from app.tasks.celery_app import celery_app


@celery_app.task(name="question_bank.generate")
def generate_question_bank(document_id: int) -> dict:
    return {
        "document_id": document_id,
        "status": "pending",
        "message": "题库生成的真实逻辑已转移到 QuestionBankService，后续可在这里接入异步包装。",
    }
