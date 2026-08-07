import sqlite3

db = sqlite3.connect("data/academic_assistant.db")

rows = db.execute("""
SELECT
    chunk_index,
    text
FROM chunks
WHERE document_name LIKE '%Matematik-Bolumu%'
""").fetchall()

print(f"Toplam chunk: {len(rows)}")
print("=" * 80)

for chunk_index, text in rows:
    if "BEŞİNCİ YARIYIL" in text:
        print(f"\nCHUNK: {chunk_index + 1}")
        print("-" * 80)
        print(text[:2000])
        print("-" * 80)

db.close()