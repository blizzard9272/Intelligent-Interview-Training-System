import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
import sys

CURRENT_FILE = Path(__file__).resolve()
BACKEND_ROOT = CURRENT_FILE.parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select

from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.qa_service import QAService


@dataclass
class EvalCaseResult:
    case_id: str
    question: str
    knowledge_base_id: int
    hit_expected_document: bool
    hit_expected_file: bool
    hit_expected_keyword: bool
    reference_count: int
    matched_document_ids: list[int]
    matched_file_names: list[str]


def load_cases(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Evaluation dataset must be a JSON list.")
    return data


def normalize_text(value: str) -> str:
    return value.strip().lower()


def evaluate_case(service: QAService, user_id: int, case: dict) -> EvalCaseResult:
    question = str(case["question"]).strip()
    knowledge_base_id = int(case["knowledge_base_id"])
    expected_document_ids = [int(item) for item in case.get("expected_document_ids", [])]
    expected_file_names = [normalize_text(str(item)) for item in case.get("expected_file_names", [])]
    expected_keywords = [normalize_text(str(item)) for item in case.get("expected_keywords", [])]

    references = service.retrieve_references_for_question(
        user_id=user_id,
        knowledge_base_id=knowledge_base_id,
        question=question,
    )

    matched_document_ids = [item.document_id for item in references]
    matched_file_names = [item.file_name for item in references]
    normalized_file_names = [normalize_text(item.file_name) for item in references]
    normalized_snippets = [normalize_text(item.snippet) for item in references]

    hit_expected_document = (
        True
        if not expected_document_ids
        else any(document_id in matched_document_ids for document_id in expected_document_ids)
    )
    hit_expected_file = (
        True
        if not expected_file_names
        else any(file_name in normalized_file_names for file_name in expected_file_names)
    )
    hit_expected_keyword = (
        True
        if not expected_keywords
        else any(keyword in snippet for keyword in expected_keywords for snippet in normalized_snippets)
    )

    return EvalCaseResult(
        case_id=str(case.get("id", question[:40])),
        question=question,
        knowledge_base_id=knowledge_base_id,
        hit_expected_document=hit_expected_document,
        hit_expected_file=hit_expected_file,
        hit_expected_keyword=hit_expected_keyword,
        reference_count=len(references),
        matched_document_ids=matched_document_ids,
        matched_file_names=matched_file_names,
    )


def build_summary(results: list[EvalCaseResult]) -> dict:
    total = len(results)
    if total == 0:
        return {
            "total_cases": 0,
            "document_hit_rate": 0.0,
            "file_hit_rate": 0.0,
            "keyword_hit_rate": 0.0,
            "average_reference_count": 0.0,
        }

    return {
        "total_cases": total,
        "document_hit_rate": round(sum(item.hit_expected_document for item in results) / total, 3),
        "file_hit_rate": round(sum(item.hit_expected_file for item in results) / total, 3),
        "keyword_hit_rate": round(sum(item.hit_expected_keyword for item in results) / total, 3),
        "average_reference_count": round(mean(item.reference_count for item in results), 2),
    }


def resolve_user_id(raw_user: str | None) -> int:
    with SessionLocal() as db:
        if raw_user is None:
            user = db.scalar(select(User).order_by(User.id.asc()))
            if not user:
                raise ValueError("No users found. Please create a user first or pass --user-id explicitly.")
            return int(user.id)

        if raw_user.isdigit():
            return int(raw_user)

        user = db.scalar(select(User).where(User.username == raw_user))
        if not user:
            raise ValueError(f"User '{raw_user}' not found.")
        return int(user.id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate current RAG retrieval quality against a small offline dataset.")
    parser.add_argument(
        "--dataset",
        default=str(Path("backend") / "evals" / "rag_eval_dataset.sample.json"),
        help="Path to a JSON evaluation dataset.",
    )
    parser.add_argument(
        "--user-id",
        dest="user_id",
        default=None,
        help="User id or username. If omitted, the first user in the database is used.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write a JSON report.",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    cases = load_cases(dataset_path)
    user_id = resolve_user_id(args.user_id)

    with SessionLocal() as db:
        service = QAService(db)
        results = [evaluate_case(service, user_id, case) for case in cases]

    report = {
        "dataset": str(dataset_path),
        "user_id": user_id,
        "summary": build_summary(results),
        "results": [
          {
            "case_id": item.case_id,
            "question": item.question,
            "knowledge_base_id": item.knowledge_base_id,
            "hit_expected_document": item.hit_expected_document,
            "hit_expected_file": item.hit_expected_file,
            "hit_expected_keyword": item.hit_expected_keyword,
            "reference_count": item.reference_count,
            "matched_document_ids": item.matched_document_ids,
            "matched_file_names": item.matched_file_names,
          }
          for item in results
        ],
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
