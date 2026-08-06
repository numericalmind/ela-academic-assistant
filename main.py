from pathlib import Path

from src.chunker import TextChunker
from src.database import ChunkDatabase
from src.document_loader import DocumentLoader
from src.embedding import LocalEmbeddingService


def get_category(document_path: str) -> str:
    path_parts = Path(document_path).parts

    if "documents" not in path_parts:
        return "unknown"

    documents_index = path_parts.index(
        "documents"
    )

    if documents_index + 1 >= len(path_parts):
        return "unknown"

    return path_parts[documents_index + 1]


def main() -> None:
    loader = DocumentLoader("documents")

    chunker = TextChunker(
        chunk_size=1200,
        chunk_overlap=150,
    )

    database = ChunkDatabase(
        "data/academic_assistant.db"
    )

    embedding_service = None

    try:
        documents = loader.load_documents()

        print("=" * 60)
        print(
            f"{len(documents)} document(s) loaded.\n"
        )

        total_chunks = 0

        for document in documents:
            chunks = chunker.chunk_document(
                document_name=document["name"],
                text=document["text"],
            )

            category = get_category(
                document["path"]
            )

            saved_count = (
                database.replace_document_chunks(
                    document_name=document["name"],
                    category=category,
                    chunks=chunks,
                )
            )

            total_chunks += saved_count

            print(
                f"{document['name']} "
                f"→ {saved_count} chunk(s) saved "
                f"[{category}]"
            )

        print("=" * 60)
        print(
            f"{total_chunks} chunk(s) stored."
        )

        chunks_to_embed = (
            database.get_chunks_without_embeddings()
        )

        print(
            f"{len(chunks_to_embed)} chunk(s) "
            f"need embeddings."
        )

        if chunks_to_embed:
            embedding_service = (
                LocalEmbeddingService()
            )

            embedding_service.initialize()

            for position, chunk in enumerate(
                chunks_to_embed,
                start=1,
            ):
                print(
                    f"[{position}/{len(chunks_to_embed)}] "
                    f"Embedding: "
                    f"{chunk['document_name']} "
                    f"chunk {chunk['chunk_index'] + 1}"
                )

                vector = (
                    embedding_service.embed_text(
                        chunk["text"]
                    )
                )

                database.save_embedding(
                    chunk_id=chunk["id"],
                    embedding=vector,
                )

        print("=" * 60)
        print(
            f"Chunks in SQLite: "
            f"{database.count_chunks()}"
        )

        print(
            f"Embeddings in SQLite: "
            f"{database.count_embeddings()}"
        )

    finally:
        if embedding_service is not None:
            embedding_service.close()

        database.close()


if __name__ == "__main__":
    main()