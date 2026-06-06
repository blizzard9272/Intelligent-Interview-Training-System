from typing import Literal

from app.utils.config_handler import get_prompt_config

PromptName = Literal["qa", "question_generation", "interview_summary"]


def get_prompt_text(prompt_name: PromptName) -> str:
    prompt_config = get_prompt_config()
    prompt_mapping = {
        "qa": prompt_config.qa.system_prompt,
        "question_generation": prompt_config.question_generation.system_prompt,
        "interview_summary": prompt_config.interview_summary.system_prompt,
    }
    try:
        return prompt_mapping[prompt_name]
    except KeyError as exc:
        raise KeyError(f"Unknown prompt name: {prompt_name}") from exc
