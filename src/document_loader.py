from pathlib import Path
import pdfplumber
from docx import Document


class DocumentLoader:
    def __init__(self, documents_path: str):
        self.documents_path = Path(documents_path)

    def load_documents(self):
        documents = []

        for file in self.documents_path.rglob("*"):
            if file.suffix.lower() == ".pdf":
                text = self._read_pdf(file)

            elif file.suffix.lower() == ".docx":
                text = self._read_docx(file)

            else:
                continue

            documents.append(
                {
                    "name": file.name,
                    "path": str(file),
                    "text": text,
                }
            )

        return documents

    def _read_pdf(self, file_path):
        text = ""

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

        return text.strip()

    def _read_docx(self, file_path):
        document = Document(file_path)

        return "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )