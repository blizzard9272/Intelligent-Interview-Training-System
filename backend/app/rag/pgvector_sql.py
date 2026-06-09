from __future__ import annotations

import json
from typing import Any

from sqlalchemy.types import UserDefinedType


class PGVector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int | None = None) -> None:
        self.dimensions = dimensions

    def get_col_spec(self, **kw: Any) -> str:
        if self.dimensions is None:
            return "vector"
        return f"vector({self.dimensions})"

    def bind_processor(self, dialect):
        def process(value: Any) -> str | None:
            if value is None:
                return None
            if isinstance(value, str):
                return value
            return json.dumps([float(item) for item in value], ensure_ascii=False)

        return process

    def result_processor(self, dialect, coltype):
        def process(value: Any) -> list[float] | None:
            if value is None:
                return None
            if isinstance(value, list):
                return [float(item) for item in value]
            if isinstance(value, str):
                parsed = json.loads(value)
                return [float(item) for item in parsed]
            return [float(item) for item in value]

        return process
