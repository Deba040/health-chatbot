#!/usr/bin/env python3
# extract_pdf_text.py
from pathlib import Path
import PyPDF2

PDFDIR = Path("documents/pdfs")
OUTDIR = Path("documents/texts")
OUTDIR.mkdir(parents=True, exist_ok=True)

for pdf in PDFDIR.glob("*.pdf"):
    txtfile = OUTDIR / (pdf.stem + ".txt")
    if txtfile.exists():
        print("already extracted", txtfile)
        continue
    try:
        pdf_reader = PyPDF2.PdfReader(str(pdf))
        text_chunks = []
        for page in pdf_reader.pages:
            text_chunks.append(page.extract_text() or "")
        full = "\n\n".join(text_chunks)
        with open(txtfile, "w", encoding="utf-8") as f:
            f.write(full)
        print("extracted", txtfile)
    except Exception as e:
        print("failed:", pdf, e)
