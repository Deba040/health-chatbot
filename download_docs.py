#!/usr/bin/env python3
# download_docs.py (safe version)

import csv, os, re, requests, hashlib, time
from urllib.parse import urlparse
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from tqdm import tqdm

# Config
CSV_IN = "urls_to_download.csv"
OUTDIR = Path("documents")
PDFDIR = OUTDIR / "pdfs"
HTMLDIR = OUTDIR / "raw_html"
TEXTDIR = OUTDIR / "texts"
META_CSV = OUTDIR / "metadata.csv"
USER_AGENT = "RAG-DocDownloader/1.0 (+contact@example.com)"

os.makedirs(PDFDIR, exist_ok=True)
os.makedirs(HTMLDIR, exist_ok=True)
os.makedirs(TEXTDIR, exist_ok=True)

def safe_name(s: str) -> str:
    """Make a safe filename from topic or url"""
    s = re.sub(r"[^\w\-_\. ]", "_", s)
    return s[:200]

def sha256sum(path: Path) -> str:
    """Compute SHA256 checksum of a file"""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def download_pdf(url: str, outpath: Path) -> str:
    """Download a PDF and return checksum"""
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, stream=True, timeout=30, verify=True)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    with open(outpath, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, desc=outpath.name
    ) as pbar:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))
    return sha256sum(outpath)

def download_html(url: str, outpath: Path) -> str:
    """Download HTML page, save raw and a plaintext version, return checksum"""
    headers = {"User-Agent": USER_AGENT}
    r = requests.get(url, headers=headers, timeout=30, verify=True)
    r.raise_for_status()

    with open(outpath, "w", encoding="utf-8") as f:
        f.write(r.text)

    # Extract plaintext
    soup = BeautifulSoup(r.text, "lxml")
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    paragraphs = [p.get_text().strip() for p in soup.find_all("p") if p.get_text().strip()]
    txt = "\n\n".join(paragraphs[:500])  # limit size

    txtname = safe_name(outpath.stem) + ".txt"
    txtpath = TEXTDIR / txtname
    with open(txtpath, "w", encoding="utf-8") as tf:
        tf.write((title or "") + "\n\n" + txt)

    return sha256sum(outpath)

# --- Main ---
rows = []
with open(CSV_IN, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for r in reader:
        rows.append(r)

metadata = []
for r in rows:
    url = r.get("url").strip()
    source = r.get("source", "").strip()
    topic = r.get("topic", "").strip()
    date_accessed = datetime.utcnow().isoformat() + "Z"

    print(f"\n--- Processing: {url}  (topic={topic})")
    headers = {"User-Agent": USER_AGENT}

    try:
        head = requests.head(url, headers=headers, allow_redirects=True, timeout=15, verify=True)
        ctype = head.headers.get("content-type", "").lower()
    except Exception as e:
        print("HEAD failed, trying GET:", e)
        ctype = ""

    filename, checksum, note = "", "", ""
    try:
        if url.lower().endswith(".pdf") or "application/pdf" in ctype:
            fname = safe_name(os.path.basename(urlparse(url).path) or f"{topic}.pdf")
            outpath = PDFDIR / fname
            if not outpath.exists():
                checksum = download_pdf(url, outpath)
            else:
                checksum = sha256sum(outpath)
            filename = str(outpath.relative_to(OUTDIR))
        elif "text/html" in ctype or not ctype:
            fname = safe_name(topic + "_page") + ".html"
            outpath = HTMLDIR / fname
            checksum = download_html(url, outpath)
            filename = str(outpath.relative_to(OUTDIR))
        else:
            note = f"Skipped unsupported type: {ctype}"
            print(note)
    except Exception as e:
        note = f"Error: {e}"
        print("FAILED:", url, e)

    metadata.append({
        "url": url,
        "source": source,
        "topic": topic,
        "filename": filename,
        "content_type": ctype,
        "sha256": checksum,
        "date_accessed": date_accessed,
        "note": note,
    })

    time.sleep(1)  # polite delay

# Write metadata
with open(META_CSV, "w", newline="", encoding="utf-8") as mf:
    fieldnames = ["url","source","topic","filename","content_type","sha256","date_accessed","note"]
    writer = csv.DictWriter(mf, fieldnames=fieldnames)
    writer.writeheader()
    for m in metadata:
        writer.writerow(m)

print("\n✅ Done. Metadata written to", META_CSV)
