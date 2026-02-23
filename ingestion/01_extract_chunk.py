import os
import csv
from datetime import datetime
from pypdf import PdfReader

PDF_DIR = "data"
OUT_CSV = "data/processed/chunks.csv"

CHUNK_SIZE = 1200   
OVERLAP = 200       


def chunk_text(text: str, chunk_size: int, overlap: int):
    text = (text or "").replace("\x00", " ").strip()
    if not text:
        return []
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(n, start + chunk_size)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def extract_pdf_pages(pdf_path: str):
    reader = PdfReader(pdf_path)
    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        try:
            pages.append((idx, page.extract_text() or ""))
        except Exception:
            pages.append((idx, ""))
    return pages


def main():
    if not os.path.isdir(PDF_DIR):
        raise FileNotFoundError(f"Missing folder: {PDF_DIR}")

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        raise FileNotFoundError(f"No PDFs found in {PDF_DIR}")

    rows = []
    for fn in sorted(pdf_files):
        path = os.path.join(PDF_DIR, fn)
        pages = extract_pdf_pages(path)

        for page_num, page_text in pages:
            chunks = chunk_text(page_text, CHUNK_SIZE, OVERLAP)
            for j, ch in enumerate(chunks, start=1):
                rows.append({
                    "doc_name": fn,
                    "doc_source": path,
                    "doc_type": "pdf",
                    "page_num": page_num,
                    "chunk_id": j,
                    "chunk_text": ch,
                    "created_at": datetime.utcnow().isoformat()
                })

        print(f"Processed {fn}: {len(pages)} pages")

    fieldnames = ["doc_name", "doc_source", "doc_type", "page_num", "chunk_id", "chunk_text", "created_at"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"\nDone! Wrote {len(rows)} chunks to: {OUT_CSV}")


if __name__ == "__main__":
    main()

