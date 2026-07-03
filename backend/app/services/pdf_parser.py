try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    fitz = None
    HAS_FITZ = False
import os
import re
from typing import Dict, Any, List
import hashlib
from backend.app.config import settings

def extract_pdf_data(file_path: str) -> Dict[str, Any]:
    """
    Extracts text, metadata, and performs basic heuristics to guess title/abstract.
    """
    # Calculate file hash for ID
    hasher = hashlib.md5()
    if os.path.exists(file_path):
        try:
            with open(file_path, 'rb') as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
        except Exception:
            pass
    file_id = hasher.hexdigest()

    if not HAS_FITZ or fitz is None:
        title = os.path.basename(file_path).replace("_", " ").replace(".pdf", "")
        return {
            "id": file_id,
            "title": title or "Untitled Research Paper",
            "authors": "Unknown Authors",
            "abstract": "PyMuPDF (fitz) is not installed. This is a simulated fallback abstract.",
            "full_text": "PyMuPDF (fitz) is not installed. This is a simulated fallback paper text snippet.",
            "pages": [{"page": 1, "text": "PyMuPDF (fitz) is not installed. This is simulated page 1 text."}],
            "year": "2026"
        }

    doc = fitz.open(file_path)
    metadata = doc.metadata
    
    # Extract complete text page by page
    full_text = ""
    pages_text = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages_text.append({"page": i + 1, "text": text})
        full_text += f"\n--- Page {i + 1} ---\n{text}"
        
    # Heuristic for abstract search
    abstract = ""
    # Look in the first 2 pages
    first_pages_text = "\n".join([p["text"] for p in pages_text[:2]])
    abstract_match = re.search(
        r'(?:abstract|ABSTRACT)\s*[:.\-\s]*(.*?)(?:\n\s*\n|\n\s*(?:introduction|INTRODUCTION|1\s+|I\s*\.\s+))',
        first_pages_text, 
        re.DOTALL | re.IGNORECASE
    )
    if abstract_match:
        abstract = abstract_match.group(1).strip()
    else:
        # Fallback: take first 1000 chars of page 1 if abstract isn't explicitly found
        if pages_text:
            cleaned_p1 = re.sub(r'\s+', ' ', pages_text[0]["text"][:1200])
            abstract = cleaned_p1 + "..."
            
    # Title heuristic
    title = metadata.get("title")
    if not title or title.strip() == "" or len(title) < 5:
        # Take the first line of page 1 that is not empty
        if pages_text:
            lines = [l.strip() for l in pages_text[0]["text"].split('\n') if l.strip()]
            if lines:
                title = lines[0]
                # If title is too short, merge with second line
                if len(title) < 15 and len(lines) > 1:
                    title = title + " " + lines[1]
    
    # Authors heuristic
    authors = metadata.get("author")
    if not authors:
        # Look at the first lines of page 1 after title
        authors = "Unknown Authors"
        
    doc.close()
    
    return {
        "id": file_id,
        "title": title or "Untitled Research Paper",
        "authors": authors or "Unknown Authors",
        "abstract": abstract,
        "full_text": full_text,
        "pages": pages_text,
        "year": metadata.get("creationDate", "")[:4] if metadata.get("creationDate") else None
    }

def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Splits text into chunks of size chunk_size with chunk_overlap overlap.
    """
    words = text.split()
    chunks = []
    
    # Quick chunking based on word count (approx 6 characters per word -> 1000 chars ≈ 170 words)
    words_per_chunk = int(chunk_size / 6)
    overlap_words = int(chunk_overlap / 6)
    
    if len(words) <= words_per_chunk:
        return [text]
        
    i = 0
    while i < len(words):
        chunk_words = words[i:i + words_per_chunk]
        chunks.append(" ".join(chunk_words))
        i += words_per_chunk - overlap_words
        if i + words_per_chunk - overlap_words >= len(words) and i < len(words):
            # Add final slice and break
            chunks.append(" ".join(words[i:]))
            break
            
    return chunks
