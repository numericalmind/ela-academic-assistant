from src.embedding import LocalEmbeddingService
from src.retriever import SemanticRetriever


def main():
    service = LocalEmbeddingService()
    service.initialize()

    retriever = SemanticRetriever(service)

    query = input("Ask a question: ")

    results = retriever.search(query, top_k=3)

    print("\n" + "=" * 70)

    for i, result in enumerate(results, start=1):
        print(f"\nResult {i}")
        print(f"Score      : {result['score']:.4f}")
        print(f"Document   : {result['document_name']}")
        print(f"Category   : {result['category']}")
        print(f"Chunk      : {result['chunk_index'] + 1}")
        print("-" * 70)
        print(result["text"][:600])

    print("\n" + "=" * 70)

    service.close()


if __name__ == "__main__":
    main()