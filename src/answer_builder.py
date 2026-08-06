from __future__ import annotations

import re


LIST_QUESTION_PATTERNS = (
    "hangi bilgiler",
    "hangi belgeler",
    "hangi evraklar",
    "nelerdir",
    "neler olmalı",
    "neler bulunmalı",
)


def build_extractive_list(
    question: str,
    results: list[dict],
) -> str | None:
    normalized_question = question.lower()

    is_list_question = any(
        pattern in normalized_question
        for pattern in LIST_QUESTION_PATTERNS
    )

    if not is_list_question:
        return None

    combined_text = "\n".join(
        result["text"]
        for result in results
    )

    raw_items = re.findall(
        r"\*\s*([^*\n]+)",
        combined_text,
    )

    cleaned_items: list[str] = []
    seen: set[str] = set()

    for raw_item in raw_items:
        item = re.sub(
            r"\s+",
            " ",
            raw_item,
        ).strip(" .;:-")
        
        item = re.split(
            r"\.\s+(?=[A-ZÇĞİÖŞÜ])",
            item,
            maxsplit=1,
        )[0].strip()

        if len(item) < 3:
            continue

        key = item.lower()

        if key in seen:
            continue

        seen.add(key)
        cleaned_items.append(item)

    if not cleaned_items:
        return None

    return "\n".join(
        f"- {item}"
        for item in cleaned_items[:8]
    )