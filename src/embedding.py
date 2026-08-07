from __future__ import annotations

from foundry_local_sdk import (
    Configuration,
    FoundryLocalManager,
)


class LocalEmbeddingService:
    def __init__(
        self,
        model_alias: str = "qwen3-embedding-0.6b",
    ) -> None:
        self.model_alias = model_alias
        self.model = None
        self.client = None

    def initialize(self) -> None:
        config = Configuration(
            app_name="ela_academic_assistant",
            log_level="info",
        )

        try:
            FoundryLocalManager.initialize(config)
        except Exception as error:
            if "already been initialized" not in str(error):
                raise

        manager = FoundryLocalManager.instance

        print(
            f"Finding embedding model: "
            f"{self.model_alias}"
        )

        self.model = manager.catalog.get_model(
            self.model_alias
        )

        if self.model is None:
            raise RuntimeError(
                f"Embedding model not found: "
                f"{self.model_alias}"
            )

        print("Downloading model if necessary...")

        self.model.download(
            lambda progress: print(
                f"\rDownload progress: "
                f"{progress:.1f}%",
                end="",
                flush=True,
            )
        )

        print("\nLoading embedding model...")

        self.model.load()

        self.client = (
            self.model.get_embedding_client()
        )

        print("Embedding model is ready.")

    def embed_text(
        self,
        text: str,
    ) -> list[float]:
        if self.client is None:
            raise RuntimeError(
                "Embedding service is not initialized."
            )

        normalized_text = str(
            text or ""
        ).strip()

        if not normalized_text:
            raise ValueError(
                "Text cannot be empty."
            )

        response = self.client.generate_embedding(
            normalized_text
        )

        return list(
            response.data[0].embedding
        )

    def close(self) -> None:
        if self.model is not None:
            self.model.unload()

        self.client = None
        self.model = None