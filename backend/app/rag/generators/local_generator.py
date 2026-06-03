from app.schemas.qa import QAReference


def build_grounded_answer(question: str, references: list[QAReference]) -> str:
    if not references:
        return (
            "I could not find relevant content in the selected knowledge base for this question. "
            "Please upload more material or ask a more specific question."
        )

    snippets = [f"{index + 1}. {ref.snippet}" for index, ref in enumerate(references)]
    joined = "\n".join(snippets)
    return (
        f"Question: {question}\n\n"
        "Answer based on retrieved knowledge base content:\n"
        f"{joined}\n\n"
        "This is the current local grounded-answer mode. "
        "The next step is replacing this synthesis with a real chat model such as Qwen or DeepSeek."
    )
