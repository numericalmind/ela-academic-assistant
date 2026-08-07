from src.chat_engine import AcademicChatEngine


def main() -> None:
    engine = AcademicChatEngine()

    try:
        engine.initialize()

        question = input(
            "\nSorunuzu yazın: "
        )

        result = engine.answer(question)

        print("\n" + "=" * 70)
        print("CEVAP")
        print("=" * 70)
        print(result["answer"])

        print("\n" + "=" * 70)
        print("KAYNAKLAR")
        print("=" * 70)

        for source in result["sources"]:
            print(
                f"- {source['document_name']} "
                f"| chunk {source['chunk_index']} "
                f"| score {source['score']}"
            )

    finally:
        engine.close()


if __name__ == "__main__":
    main()