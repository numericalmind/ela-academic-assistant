from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.chunker import Chunk


class ChunkDatabase:
    def __init__(
        self,
        database_path: str = "data/academic_assistant.db",
    ) -> None:
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.connection = sqlite3.connect(
            self.database_path
        )

        self.connection.row_factory = sqlite3.Row

        self._create_table()
        self._ensure_embedding_column()

    def _create_table(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_name TEXT NOT NULL,
                category TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                embedding TEXT,
                created_at TEXT NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_chunks_document_name
            ON chunks(document_name)
            """
        )

        self.connection.commit()

    def _ensure_embedding_column(self) -> None:
        columns = self.connection.execute(
            "PRAGMA table_info(chunks)"
        ).fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        if "embedding" not in column_names:
            self.connection.execute(
                """
                ALTER TABLE chunks
                ADD COLUMN embedding TEXT
                """
            )

            self.connection.commit()

    def replace_document_chunks(
        self,
        document_name: str,
        category: str,
        chunks: list[Chunk],
    ) -> int:
        with self.connection:
            self.connection.execute(
                """
                DELETE FROM chunks
                WHERE document_name = ?
                """,
                (document_name,),
            )

            self.connection.executemany(
                """
                INSERT INTO chunks (
                    document_name,
                    category,
                    chunk_index,
                    text,
                    embedding
                )
                VALUES (?, ?, ?, ?, NULL)
                """,
                [
                    (
                        chunk.document_name,
                        category,
                        chunk.chunk_index,
                        chunk.text,
                    )
                    for chunk in chunks
                ],
            )

        return len(chunks)

    def get_chunks_without_embeddings(
        self,
    ) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT
                id,
                document_name,
                category,
                chunk_index,
                text
            FROM chunks
            WHERE embedding IS NULL
            ORDER BY id
            """
        ).fetchall()

    def save_embedding(
        self,
        chunk_id: int,
        embedding: list[float],
    ) -> None:
        serialized_embedding = json.dumps(
            embedding
        )

        with self.connection:
            self.connection.execute(
                """
                UPDATE chunks
                SET embedding = ?
                WHERE id = ?
                """,
                (
                    serialized_embedding,
                    chunk_id,
                ),
            )

    def count_chunks(self) -> int:
        row = self.connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM chunks
            """
        ).fetchone()

        return int(row["total"])

    def count_embeddings(self) -> int:
        row = self.connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM chunks
            WHERE embedding IS NOT NULL
            """
        ).fetchone()

        return int(row["total"])

    def list_documents(
        self,
    ) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT
                document_name,
                category,
                COUNT(*) AS chunk_count
            FROM chunks
            GROUP BY document_name, category
            ORDER BY document_name
            """
        ).fetchall()

    def close(self) -> None:
        self.connection.close()