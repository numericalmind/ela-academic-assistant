from __future__ import annotations

from foundry_local_sdk import (
    Configuration,
    FoundryLocalManager,
)

from src.embedding import LocalEmbeddingService
from src.retriever import SemanticRetriever
from src.answer_builder import build_extractive_list

FALLBACK_ANSWER = (
    "Bu bilgi yüklenen belgelerde bulunamadı."
)


class AcademicChatEngine:
    def __init__(
        self,
        chat_model_alias: str = "phi-3.5-mini",
        database_path: str = "data/academic_assistant.db",
        top_k: int = 3,
    ) -> None:
        self.chat_model_alias = chat_model_alias
        self.database_path = database_path
        self.top_k = top_k

        self.embedding_service = None
        self.retriever = None
        self.chat_model = None
        self.chat_client = None

    def initialize(self) -> None:
        print("Initializing embedding service...")

        self.embedding_service = LocalEmbeddingService()
        self.embedding_service.initialize()

        self.retriever = SemanticRetriever(
            embedding_service=self.embedding_service,
            database_path=self.database_path,
        )

        print(
            f"Finding chat model: "
            f"{self.chat_model_alias}"
        )

        config = Configuration(
            app_name="ela_academic_assistant_chat",
            log_level="info",
        )

        try:
            FoundryLocalManager.initialize(config)
        except Exception:
            # Manager was probably initialized earlier
            # by the embedding service.
            pass

        manager = FoundryLocalManager.instance

        self.chat_model = manager.catalog.get_model(
            self.chat_model_alias
        )

        if self.chat_model is None:
            raise RuntimeError(
                f"Chat model not found: "
                f"{self.chat_model_alias}"
            )

        print("Downloading chat model if necessary...")

        self.chat_model.download(
            lambda progress: print(
                f"\rChat model download: "
                f"{progress:.1f}%",
                end="",
                flush=True,
            )
        )

        print("\nLoading chat model...")

        self.chat_model.load()

        self.chat_client = (
            self.chat_model.get_chat_client()
        )
        self.chat_client.settings.temperature = 0.0
        self.chat_client.settings.top_p = 0.8
        self.chat_client.settings.max_tokens = 350
        print("Academic chat engine is ready.")

    def answer(
        self,
        question: str,
    ) -> dict:
        if (
            self.retriever is None
            or self.chat_client is None
        ):
            raise RuntimeError(
                "Chat engine is not initialized."
            )

        normalized_question = str(
            question or ""
        ).strip()

        if not normalized_question:
            raise ValueError(
                "Question cannot be empty."
            )

        results = self.retriever.search(
            normalized_question,
            top_k=2,
        )

        if (
            not results
            or results[0]["score"] < 0.30
        ):
            return {
                "answer": FALLBACK_ANSWER,
                "sources": [],
            }
        extractive_answer = build_extractive_list(
            normalized_question,
            results,
        )

        if extractive_answer:
            return {
                "answer": extractive_answer,
                "sources": self._build_sources(
                    results
                ),
            }
        context = self._build_context(results)

        messages = [
            {
                "role": "system",
                "content": (
                    "Sen bir akademik belge asistanısın. "
                    "Soruyu yalnızca verilen belge metnine göre cevapla. "
                    "Belgede açıkça listelenen tüm gerekli unsurları çıkar; "
                    "hiçbirini atlama ve belge dışı bilgi ekleme. "
                    "Çıktıda yalnızca tire ile başlayan kısa maddeler yaz. "
                    "Soru, Cevap, Giriş, Sonuç veya Kaynaklar gibi "
                    "başlıklar kullanma. Aynı bilgiyi tekrar etme."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{context}\n\n"
                    f"Soru: {normalized_question}\n\n"
                    "Belgede belirtilen tüm gerekli unsurları "
                    "yalnızca madde işaretleriyle yaz."
                ),
            },
        ]

        response = self.chat_client.complete_chat(
            messages
        )

        answer = (
            response.choices[0]
            .message.content
            .strip()
        )

        if not answer:
            answer = FALLBACK_ANSWER

        return {
            "answer": answer,
            "sources": self._build_sources(
                results
            ),
        }

    def _build_context(
        self,
        results: list[dict],
    ) -> str:
        sections = []

        for position, result in enumerate(
            results,
            start=1,
        ):
            sections.append(
                "\n".join(
                    [
                        f"[BELGE {position}]",
                        (
                            "Dosya: "
                            f"{result['document_name']}"
                        ),
                        (
                            "Kategori: "
                            f"{result['category']}"
                        ),
                        (
                            "Parça: "
                            f"{result['chunk_index'] + 1}"
                        ),
                        "Metin:",
                        result["text"],
                    ]
                )
            )

        return "\n\n".join(sections)

    def _build_sources(
        self,
        results: list[dict],
    ) -> list[dict]:
        return [
            {
                "document_name": result[
                    "document_name"
                ],
                "category": result["category"],
                "chunk_index": (
                    result["chunk_index"] + 1
                ),
                "score": round(
                    result["score"],
                    4,
                ),
            }
            for result in results
        ]

    def close(self) -> None:
        if self.chat_model is not None:
            self.chat_model.unload()

        if self.embedding_service is not None:
            self.embedding_service.close()

        self.chat_client = None
        self.chat_model = None
        self.retriever = None
        self.embedding_service = None