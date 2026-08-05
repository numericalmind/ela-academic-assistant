from pathlib import Path

from src.chunker import TextChunker
from src.database import ChunkDatabase
from src.document_loader import DocumentLoader


def get_category(document_path: str) -> str:
    path_parts = Path(document_path).parts

    if "documents" not in path_parts:
        return "unknown"

    documents_index = path_parts.index("documents")

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

    try:
        documents = loader.load_documents()

        print("=" * 60)
        print(
            f"{len(documents)} document(s) loaded.\n"
        )

        saved_chunks = 0

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

            saved_chunks += saved_count

            print(
                f"{document['name']} "
                f"→ {saved_count} chunk(s) saved "
                f"[{category}]"
            )

        print("=" * 60)
        print(
            f"{saved_chunks} chunk(s) processed."
        )
        print(
            f"{database.count_chunks()} "
            f"chunk(s) currently stored in SQLite."
        )

        print("\nStored documents:")

        for (
            document_name,
            category,
            chunk_count,
        ) in database.list_documents():
            print(
                f"- {document_name} "
                f"[{category}] "
                f"({chunk_count} chunk(s))"
            )

    finally:
        database.close()


if __name__ == "__main__":
    main()