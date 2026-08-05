from src.chunker import TextChunker
from src.document_loader import DocumentLoader


def main() -> None:
    loader = DocumentLoader("documents")
    chunker = TextChunker(
        chunk_size=1200,
        chunk_overlap=150,
    )

    documents = loader.load_documents()

    print("=" * 60)
    print(f"{len(documents)} document(s) loaded.\n")

    total_chunks = 0

    for document in documents:
        chunks = chunker.chunk_document(
            document_name=document["name"],
            text=document["text"],
        )

        total_chunks += len(chunks)

        print(document["name"])
        print(f"{len(chunks)} chunk(s) created.")

        for chunk in chunks[:2]:
            print("-" * 60)
            print(
                f"Chunk {chunk.chunk_index + 1} "
                f"({len(chunk.text)} characters)"
            )
            print(chunk.text[:300])

        print("=" * 60)

    print(f"\nTotal chunks: {total_chunks}")


if __name__ == "__main__":
    main()