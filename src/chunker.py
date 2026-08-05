from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class Chunk:
    document_name: str
    chunk_index: int
    text: str


class TextChunker:
    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 150,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0."
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative."
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        document_name: str,
        text: str,
    ) -> list[Chunk]:
        normalized_text = self._normalize_text(text)

        if not normalized_text:
            return []

        units = self._split_into_units(normalized_text)

        chunks: list[Chunk] = []
        current_parts: list[str] = []
        current_length = 0

        for unit in units:
            if len(unit) > self.chunk_size:
                large_unit_parts = self._split_large_unit(unit)
            else:
                large_unit_parts = [unit]

            for part in large_unit_parts:
                additional_length = (
                    len(part)
                    + (2 if current_parts else 0)
                )

                if (
                    current_parts
                    and current_length + additional_length
                    > self.chunk_size
                ):
                    chunks.append(
                        Chunk(
                            document_name=document_name,
                            chunk_index=len(chunks),
                            text="\n\n".join(current_parts),
                        )
                    )

                    overlap = self._get_overlap(
                        "\n\n".join(current_parts)
                    )

                    current_parts = [overlap] if overlap else []
                    current_length = len(overlap)

                current_parts.append(part)
                current_length += (
                    len(part)
                    + (2 if len(current_parts) > 1 else 0)
                )

        if current_parts:
            chunks.append(
                Chunk(
                    document_name=document_name,
                    chunk_index=len(chunks),
                    text="\n\n".join(current_parts),
                )
            )

        return chunks

    def _normalize_text(self, text: str) -> str:
        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in str(text or "").splitlines()
        ]

        return "\n".join(
            line for line in lines if line
        ).strip()

    def _split_into_units(self, text: str) -> list[str]:
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        units: list[str] = []
        current_lines: list[str] = []

        for line in lines:
            current_lines.append(line)

            current_text = " ".join(current_lines)

            if (
                len(current_text) >= 500
                or self._looks_like_heading(line)
            ):
                units.append(current_text)
                current_lines = []

        if current_lines:
            units.append(" ".join(current_lines))

        return units

    def _looks_like_heading(self, line: str) -> bool:
        if len(line) > 100:
            return False

        return bool(
            re.match(
                r"^(\d+(\.\d+)*[.)]?\s+|"
                r"[A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ\s0-9\-]{4,})",
                line,
            )
        )

    def _split_large_unit(
        self,
        text: str,
    ) -> list[str]:
        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        parts: list[str] = []
        current = ""

        for sentence in sentences:
            if not sentence:
                continue

            if len(sentence) > self.chunk_size:
                if current:
                    parts.append(current.strip())
                    current = ""

                parts.extend(
                    self._split_by_characters(sentence)
                )
                continue

            candidate = (
                f"{current} {sentence}".strip()
            )

            if (
                current
                and len(candidate) > self.chunk_size
            ):
                parts.append(current.strip())
                current = sentence
            else:
                current = candidate

        if current:
            parts.append(current.strip())

        return parts

    def _split_by_characters(
        self,
        text: str,
    ) -> list[str]:
        parts = []
        start = 0

        while start < len(text):
            end = min(
                start + self.chunk_size,
                len(text),
            )

            if end < len(text):
                preferred_end = text.rfind(
                    " ",
                    start,
                    end,
                )

                if preferred_end > start:
                    end = preferred_end

            part = text[start:end].strip()

            if part:
                parts.append(part)

            start = end

        return parts

    def _get_overlap(
        self,
        text: str,
    ) -> str:
        if not text:
            return ""

        overlap = text[-self.chunk_overlap:]

        first_space = overlap.find(" ")

        if first_space != -1:
            overlap = overlap[first_space + 1:]

        return overlap.strip()