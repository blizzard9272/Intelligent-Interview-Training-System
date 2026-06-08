import chromadb

from app.utils import ensure_chroma_dir, get_chroma_config


class ChromaVectorStore:
    def __init__(self) -> None:
        persist_directory = ensure_chroma_dir()
        chroma_config = get_chroma_config()
        self.client = chromadb.PersistentClient(path=str(persist_directory))
        self.collection = self.client.get_or_create_collection(name=chroma_config.storage.collection_name)

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

    def get_document_chunks(self, user_id: int, document_id: int) -> dict:
        return self.collection.get(
            where={
                "$and": [
                    {"user_id": user_id},
                    {"document_id": document_id},
                ]
            },
            include=["documents", "metadatas"],
        )

    def query(
        self,
        query_embedding: list[float],
        user_id: int,
        knowledge_base_id: int,
        top_k: int | None = None,
        extra_filters: list[dict[str, object]] | None = None,
    ) -> dict:
        chroma_config = get_chroma_config()
        requested_top_k = top_k or chroma_config.retrieval.default_top_k
        requested_top_k = min(requested_top_k, chroma_config.retrieval.max_top_k)
        filters = [
            {"user_id": user_id},
            {"knowledge_base_id": knowledge_base_id},
        ]
        if extra_filters:
            filters.extend(extra_filters)
        return self.collection.query(
            query_embeddings=[query_embedding],
            n_results=requested_top_k,
            where={"$and": filters},
            include=["documents", "metadatas", "distances"],
        )
