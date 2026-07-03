import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger("researchpilot.mcp.search_tools")

def search_arxiv(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search arXiv via XML API. Returns standardized metadata.
    """
    if not query:
        return []
    
    encoded_query = urllib.parse.quote(query)
    url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&max_results={limit}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'ResearchPilotAI/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        
        # XML namespace map
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        papers = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns)
            title_text = title.text.strip() if title is not None else "Unknown Title"
            
            # Remove linebreaks from titles
            title_text = " ".join(title_text.split())
            
            summary = entry.find('atom:summary', ns)
            summary_text = summary.text.strip() if summary is not None else "No summary available."
            summary_text = " ".join(summary_text.split())
            
            id_url = entry.find('atom:id', ns)
            id_text = id_url.text.strip() if id_url is not None else ""
            arxiv_id = id_text.split('/abs/')[-1].split('v')[0] if '/abs/' in id_text else ""
            
            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns)
                if name is not None:
                    authors.append(name.text.strip())
            
            published = entry.find('atom:published', ns)
            year = published.text.split('-')[0] if published is not None else "Unknown"
            
            papers.append({
                "source": "arxiv",
                "id": arxiv_id,
                "title": title_text,
                "authors": ", ".join(authors) if authors else "Unknown Authors",
                "abstract": summary_text,
                "url": id_text,
                "year": year,
                "doi": ""
            })
        return papers
    except Exception as e:
        logger.error(f"Error searching arXiv: {e}")
        return []

def search_semantic_scholar(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search Semantic Scholar API.
    """
    if not query:
        return []
        
    encoded_query = urllib.parse.quote(query)
    fields = "title,authors,venue,year,externalIds,abstract"
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit={limit}&fields={fields}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'ResearchPilotAI/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        papers = []
        for item in data.get('data', []):
            authors = [a.get('name') for a in item.get('authors', []) if a.get('name')]
            ext_ids = item.get('externalIds', {})
            doi = ext_ids.get('DOI', '')
            arxiv_id = ext_ids.get('ArXiv', '')
            
            paper_id = item.get('paperId', '')
            url_link = f"https://www.semanticscholar.org/paper/{paper_id}"
            
            papers.append({
                "source": "semantic_scholar",
                "id": paper_id,
                "title": item.get('title', 'Unknown Title'),
                "authors": ", ".join(authors) if authors else "Unknown Authors",
                "abstract": item.get('abstract', 'No abstract available.'),
                "url": url_link,
                "year": str(item.get('year', 'Unknown')),
                "doi": doi,
                "arxiv_id": arxiv_id
            })
        return papers
    except Exception as e:
        logger.error(f"Error searching Semantic Scholar: {e}")
        return []

def query_crossref(doi: str) -> Dict[str, Any]:
    """
    Lookup paper metadata from CrossRef by DOI.
    """
    if not doi:
        return {}
        
    # Standardize DOI formatting
    doi = doi.strip()
    if doi.startswith("http"):
        doi = doi.split("doi.org/")[-1]
        
    encoded_doi = urllib.parse.quote(doi)
    url = f"https://api.crossref.org/works/{encoded_doi}"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'mailto:support@researchpilot.ai'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        message = data.get('message', {})
        
        # Parse authors
        authors = []
        for author in message.get('author', []):
            given = author.get('given', '')
            family = author.get('family', '')
            if given or family:
                authors.append(f"{given} {family}".strip())
                
        # Parse published year
        year = "Unknown"
        pub_parts = message.get('published-print', {}).get('date-parts', [])
        if not pub_parts:
            pub_parts = message.get('published-online', {}).get('date-parts', [])
        if pub_parts and pub_parts[0]:
            year = str(pub_parts[0][0])
            
        return {
            "source": "crossref",
            "doi": doi,
            "title": message.get('title', ['Unknown Title'])[0] if message.get('title') else 'Unknown Title',
            "authors": ", ".join(authors) if authors else "Unknown Authors",
            "abstract": message.get('abstract', 'No abstract available.'),
            "journal": message.get('container-title', [''])[0] if message.get('container-title') else '',
            "year": year,
            "url": message.get('URL', '')
        }
    except Exception as e:
        logger.error(f"Error querying CrossRef: {e}")
        return {}
