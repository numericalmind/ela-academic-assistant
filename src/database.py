from __future__ import annotations

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

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_name TEXT NOT NULL,
                category TEXT NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
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
                    text
                )
                VALUES (?, ?, ?, ?)
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

    def count_chunks(self) -> int:
        row = self.connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM chunks
            """
        ).fetchone()

        return int(row[0])

    def list_documents(self) -> list[tuple[str, str, int]]:
        rows = self.connection.execute(
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

        return rows

    def close(self) -> None:
        self.connection.close()