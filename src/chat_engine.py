from __future__ import annotations

from foundry_local_sdk import (
    Configuration,
    FoundryLocalManager,
)

from src.answer_builder import build_extractive_list
from src.embedding import LocalEmbeddingService
from src.retriever import SemanticRetriever


FALLBACK_ANSWER = (
    "Bu bilgi yüklenen belgelerde bulunamadı."
)


class AcademicChatEngine:
    def __init__(
        self,
        chat_model_alias: str = "phi-3.5-mini",
        database_path: str = "data/academic_assistant.db",
        top_k: int = 6,
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
        except Exception as error:
            if "already been initialized" not in str(error):
                raise

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
            top_k=self.top_k,
        )

        if (
            not results
            or results[0]["score"] < 0.30
        ):
            return {
                "answer": FALLBACK_ANSWER,
                "sources": [],
            }

        extractive_results = results
        source_results = results

        question_lower = (
            normalized_question.lower()
        )

        # -------------------------------------------------
        # Erasmus checklist routing
        # -------------------------------------------------

        is_erasmus_checklist_question = (
            (
                "erasmus" in question_lower
                or "staj" in question_lower
            )
            and (
                "gitmeden önce" in question_lower
                or "hangi belgeler" in question_lower
                or "hangi evraklar" in question_lower
                or "hazırlanmalıdır" in question_lower
                or "hazırlamalıyım" in question_lower
            )
        )

        if is_erasmus_checklist_question:
            checklist_document = next(
                (
                    result["document_name"]
                    for result in results
                    if "checklist"
                    in result["document_name"].lower()
                ),
                None,
            )

            if checklist_document:
                extractive_results = (
                    self.retriever.get_document_chunks(
                        checklist_document
                    )
                )

                source_results = [
                    result
                    for result in results
                    if result["document_name"]
                    == checklist_document
                ]

        # -------------------------------------------------
        # Double Major routing
        # -------------------------------------------------

        is_double_major_question = (
            (
                "çift anadal" in question_lower
                or "cift anadal" in question_lower
                or "çap" in question_lower
            )
            and (
                "muaf" in question_lower
                or "muafiyet" in question_lower
            )
        )

        if is_double_major_question:
            double_major_document = next(
                (
                    result["document_name"]
                    for result in results
                    if (
                        "cift_anadal"
                        in result["document_name"].lower()
                        or "bilgisayarmuhmatematik"
                        in result["document_name"].lower()
                    )
                ),
                None,
            )

            if double_major_document:
                extractive_results = (
                    self.retriever.get_document_chunks(
                        double_major_document
                    )
                )

                source_results = [
                    result
                    for result in results
                    if result["document_name"]
                    == double_major_document
                ]

        # -------------------------------------------------
        # TÜBİTAK 2209-A application conditions routing
        # -------------------------------------------------

        is_2209_conditions_question = (
            (
                "2209-a" in question_lower
                or "2209 a" in question_lower
                or "2209a" in question_lower
            )
            and (
                "şart" in question_lower
                or "koşul" in question_lower
                or "kimler başvurabilir" in question_lower
            )
        )

        if is_2209_conditions_question:
            tubitak_document = next(
                (
                    result["document_name"]
                    for result in results
                    if "2209-a"
                    in result["document_name"].lower()
                ),
                None,
            )

            if tubitak_document:
                extractive_results = (
                    self.retriever.get_document_chunks(
                        tubitak_document
                    )
                )

                source_results = [
                    result
                    for result in results
                    if result["document_name"]
                    == tubitak_document
                ]

        # -------------------------------------------------
        # Extractive answer
        # -------------------------------------------------

        extractive_answer = build_extractive_list(
            normalized_question,
            extractive_results,
        )

        if extractive_answer:
            return {
                "answer": extractive_answer,
                "sources": self._build_sources(
                    source_results
                ),
            }

        # -------------------------------------------------
        # General RAG / LLM answer
        # -------------------------------------------------

        context = self._build_context(
            results
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "Sen bir akademik belge asistanısın. "
                    "Soruyu yalnızca verilen belge metnine göre cevapla. "
                    "Belgede açıkça belirtilen bilgileri kullan. "
                    "Belge dışı bilgi ekleme. "
                    "Kısa ve açık cevap ver. "
                    "Aynı bilgiyi tekrar etme."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{context}\n\n"
                    f"Soru: {normalized_question}\n\n"
                    "Yalnızca doğrudan cevabı yaz."
                ),
            },
        ]

        try:
            response = self.chat_client.complete_chat(
                messages
            )

        except Exception:
            return {
                "answer": (
                    "Model cevap üretirken bir hata oluştu. "
                    "Lütfen tekrar deneyin."
                ),
                "sources": self._build_sources(
                    results
                ),
            }

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

        return "\n\n".join(
            sections
        )

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