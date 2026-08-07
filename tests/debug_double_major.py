import sqlite3


db = sqlite3.connect("data/academic_assistant.db")
db.row_factory = sqlite3.Row

rows = db.execute(
    """
    SELECT
        chunk_index,
        text
    FROM chunks
    WHERE document_name LIKE '%Cift_Anadal%'
    ORDER BY chunk_index
    """
).fetchall()

print(f"Toplam chunk: {len(rows)}")
print("=" * 80)

for row in rows:
    text = row["text"]

    if (
        "MUAF" in text
        or "muaf" in text.lower()
        or "MAT " in text
        or "CSC " in text
    ):
        print(f"\nCHUNK {row['chunk_index'] + 1}")
        print("-" * 80)
        print(text)
        print("-" * 80)

db.close()