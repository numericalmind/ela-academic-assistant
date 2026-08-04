from src.document_loader import DocumentLoader

loader = DocumentLoader("documents")

documents = loader.load_documents()

print("=" * 60)

print(f"{len(documents)} document(s) loaded.\n")

for document in documents:
    print(document["name"])
    print(document["text"][:300])
    print("-" * 60)