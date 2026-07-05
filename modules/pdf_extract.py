"""PDF -> düz metin dönüşümü.

hiring-agent projesindeki PDF-to-Markdown adımından esinlenildi, burada
sade metin çıkarımı yeterli çünkü tek bir LLM çağrısında ham CV metnini
kullanıyoruz.
"""

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Verilen PDF byte dizisinden düz metni döndürür."""
    text_parts = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts).strip()
