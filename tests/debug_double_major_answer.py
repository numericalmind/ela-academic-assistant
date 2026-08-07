import sqlite3

from src.answer_builder import _build_double_major_exemptions


print("DEBUG BASLADI")

db = sqlite3.connect(
    "data/academic_assistant.db"
)

db.row_factory = sqlite3.Row

rows = db.execute(
    """
    SELECT
        document_name,
        category,
        chunk_index,
        text
    FROM chunks
    WHERE document_name LIKE '%Cift_Anadal%'
    ORDER BY chunk_index
    """
).fetchall()

print("BULUNAN CHUNK SAYISI:", len(rows))

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

print(
    "DOSYA:",
    results[0]["document_name"]
    if results
    else "DOSYA BULUNAMADI",
)

answer = _build_double_major_exemptions(
    results
)

print("=" * 80)
print("CAP PARSER CEVABI:")
print(repr(answer))
print("=" * 80)

db.close()