import os
import urllib.request
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("researchpilot.download_samples")

SAMPLE_PAPERS = {
    "attention_is_all_you_need.pdf": "https://arxiv.org/pdf/1706.03762.pdf",
    "lora_low_rank_adaptation.pdf": "https://arxiv.org/pdf/2106.09685.pdf"
}

def download_samples():
    dest_dir = Path(__file__).resolve().parent / "sample_papers"
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    for filename, url in SAMPLE_PAPERS.items():
        filepath = dest_dir / filename
        if filepath.exists():
            logger.info(f"{filename} already exists. Skipping download.")
            continue
            
        logger.info(f"Downloading {filename} from {url}...")
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(filepath, "wb") as f:
                    f.write(response.read())
            logger.info(f"Successfully downloaded {filename}.")
        except Exception as e:
            logger.error(f"Failed to download {filename} from {url}: {e}")
            logger.info("Creating a fallback mock text file for testing.")
            # Create a mock text file renamed to .pdf for mock parsing (or just dummy text)
            # PyMuPDF might crash if it's not a real PDF, so we try to write a simple valid PDF or log warning.
            # We can write a simple mock 1-page PDF using reportlab!
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet
                
                doc = SimpleDocTemplate(str(filepath), pagesize=letter)
                styles = getSampleStyleSheet()
                story = [
                    Paragraph(f"Mock Scientific Paper: {filename.replace('_', ' ').replace('.pdf', '')}", styles['Title']),
                    Spacer(1, 20),
                    Paragraph("<b>Abstract:</b> This is a synthesized mock paper for test validation.", styles['Normal']),
                    Spacer(1, 20),
                    Paragraph("<b>Introduction:</b> Self-attention and low-rank adaptations are key topics in modern ML.", styles['Normal'])
                ]
                doc.build(story)
                logger.info(f"Created reportlab fallback mock PDF at {filepath}.")
            except Exception as re_err:
                logger.error(f"Could not build reportlab fallback mock: {re_err}")

if __name__ == "__main__":
    download_samples()
