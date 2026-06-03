from pathlib import Path

import chromadb

from app.core.config import settings


class ChromaVectorStore:
    def __init__(self) -> None:
        persist_directory = Path(settings.chroma_persist_directory)
        persist_directory.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(persist_directory))
        self.collection = self.client.get_or_create_collection(name=settings.vector_collection_name)

    def add_chunks(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        self.collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def delete_document_chunks(self, document_id: int) -> None:
        self.collection.delete(where={"document_id": document_id})

    def query(
        self,
        query_embedding: list[float],
        user_id: int,
        knowledge_base_id: int,
        top_k: int = 4,
    ) -> dict:
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={
                "$and": [
                    {"user_id": user_id},
                    {"knowledge_base_id": knowledge_base_id},
                ]
            },
            include=["documents", "metadatas", "distances"],
        )
