import sqlite3

from src.answer_builder import _build_erasmus_checklist


db = sqlite3.connect("data/academic_assistant.db")
db.row_factory = sqlite3.Row

rows = db.execute(
    """
    SELECT
        document_name,
        category,
        chunk_index,
        text
    FROM chunks
    WHERE document_name = 'staj-checklist-2.docx'
    ORDER BY chunk_index
    """
).fetchall()

results = [
    {
        "document_name": row["document_name"],
        "category": row["category"],
        "chunk_index": row["chunk_index"],
        "text": row["text"],
        "score": 1.0,
    }
    for row in rows
]

print("CHECKLIST CHUNK SAYISI:", len(results))
print("=" * 80)

for result in results:
    print("CHUNK:", result["chunk_index"] + 1)
    print(result["text"][:1200])
    print("-" * 80)

print("\nPARSER CEVABI:")
print("=" * 80)

answer = _build_erasmus_checklist(results)

print(answer)

from src.answer_builder import build_extractive_list

print("\nFULL BUILDER TEST:")
print("=" * 80)

question = (
    "Erasmus stajına gitmeden önce "
    "hangi belgeler hazırlanmalıdır?"
)

answer = build_extractive_list(
    question,
    results,
)

print(answer)

db.close()