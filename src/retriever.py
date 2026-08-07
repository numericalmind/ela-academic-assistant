from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np

from src.embedding import LocalEmbeddingService


class SemanticRetriever:
    def __init__(
        self,
        embedding_service: LocalEmbeddingService,
        database_path: str = "data/academic_assistant.db",
    ) -> None:
        self.embedding_service = embedding_service
        self.database_path = Path(database_path)

        if not self.database_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.database_path}"
            )

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[dict]:
        normalized_query = str(query or "").strip()

        if not normalized_query:
            raise ValueError(
                "Query cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than 0."
            )

        query_embedding = np.asarray(
            self.embedding_service.embed_text(
                normalized_query
            ),
            dtype=np.float32,
        )

        stored_chunks = self._load_chunks()

        results = []

        for chunk in stored_chunks:
            stored_embedding = np.asarray(
                json.loads(chunk["embedding"]),
                dtype=np.float32,
            )

            similarity = self._cosine_similarity(
                query_embedding,
                stored_embedding,
            )

            lexical_bonus = (
                self._calculate_lexical_bonus(
                    normalized_query,
                    chunk["text"],
                )
            )

            final_score = (
                similarity + lexical_bonus
            )

            results.append(
                {
                    "id": chunk["id"],
                    "document_name": chunk[
                        "document_name"
                    ],
                    "category": chunk["category"],
                    "chunk_index": chunk[
                        "chunk_index"
                    ],
                    "text": chunk["text"],
                    "score": final_score,
                }
            )

        results.sort(
            key=lambda result: result["score"],
            reverse=True,
        )

        return results[:top_k]

    def get_document_chunks(
        self,
        document_name: str,
    ) -> list[dict]:
        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = sqlite3.Row

        try:
            rows = connection.execute(
                """
                SELECT
                    id,
                    document_name,
                    category,
                    chunk_index,
                    text
                FROM chunks
                WHERE document_name = ?
                ORDER BY chunk_index
                """,
                (document_name,),
            ).fetchall()

            return [
                {
                    "id": row["id"],
                    "document_name": row[
                        "document_name"
                    ],
                    "category": row["category"],
                    "chunk_index": row[
                        "chunk_index"
                    ],
                    "text": row["text"],
                    "score": 0.0,
                }
                for row in rows
            ]

        finally:
            connection.close()

    def _load_chunks(
        self,
    ) -> list[sqlite3.Row]:
        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = sqlite3.Row

        try:
            rows = connection.execute(
                """
                SELECT
                    id,
                    document_name,
                    category,
                    chunk_index,
                    text,
                    embedding
                FROM chunks
                WHERE embedding IS NOT NULL
                """
            ).fetchall()

            if not rows:
                raise RuntimeError(
                    "No embedded chunks were found "
                    "in the database."
                )

            return rows

        finally:
            connection.close()

    @staticmethod
    def _calculate_lexical_bonus(
        query: str,
        text: str,
    ) -> float:
        query_lower = query.lower()
        text_lower = text.lower()

        bonus = 0.0

        important_phrases = (
            "beşinci yarıyıl",
            "altıncı yarıyıl",
            "yedinci yarıyıl",
            "sekizinci yarıyıl",
            "gitmeden önce",
            "proje ortağı",
            "davet mektubu",
        )

        for phrase in important_phrases:
            if (
                phrase in query_lower
                and phrase in text_lower
            ):
                bonus += 0.25

        return bonus

    @staticmethod
    def _cosine_similarity(
        first_vector: np.ndarray,
        second_vector: np.ndarray,
    ) -> float:
        if first_vector.shape != second_vector.shape:
            raise ValueError(
                "Embedding dimensions do not match."
            )

        denominator = (
            np.linalg.norm(first_vector)
            * np.linalg.norm(second_vector)
        )

        if denominator == 0:
            return 0.0

        return float(
            np.dot(
                first_vector,
                second_vector,
            )
            / denominator
        )