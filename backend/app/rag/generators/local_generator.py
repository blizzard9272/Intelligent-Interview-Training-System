from app.schemas.qa import QAReference
from app.utils import get_model_config, get_prompt_text, get_rag_config


def build_grounded_answer(question: str, references: list[QAReference]) -> str:
    rag_config = get_rag_config()
    model_config = get_model_config()
    system_prompt = get_prompt_text("qa").strip()

    if not references:
        if not rag_config.answering.fallback_when_empty:
            return ""
        return (
            "当前知识库中没有检索到可直接参考的内容。"
            "如果在线模型可用，我会基于通用知识补充回答；否则建议你上传更多相关资料或把问题问得更具体一些。"
        )

    snippets = [
        f"{index + 1}. {ref.snippet[: rag_config.answering.max_reference_snippet_length]}"
        for index, ref in enumerate(references)
    ]
    joined = "\n".join(snippets)
    answer = (
        f"System guidance:\n{system_prompt}\n\n"
        f"Question: {question}\n\n"
        "Answer based on retrieved knowledge base content:\n"
        f"{joined}\n\n"
        "This is the current local grounded-answer mode. "
        f"The configured chat profile is {model_config.chat.provider}/{model_config.chat.model_name}, "
        "and the next step is replacing this synthesis with a real chat model runtime."
    )
    if rag_config.answering.include_references:
        return answer
    return answer.replace("Answer based on retrieved knowledge base content:\n", "Answer:\n")
