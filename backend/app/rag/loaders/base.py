from pathlib import Path


class BaseLoader:
    def load(self, file_path: str) -> str:
        raise NotImplementedError


class TextLoader(BaseLoader):
    def load(self, file_path: str) -> str:
        return Path(file_path).read_text(encoding="utf-8")
