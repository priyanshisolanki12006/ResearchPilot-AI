import sys
from pathlib import Path

# Inject project root paths to resolve ModuleNotFoundError regardless of current working directory
current_file = Path(__file__).resolve()
project_root = str(current_file.parent.parent.parent.parent) # Capstone Project/
backend_root = str(current_file.parent.parent.parent)        # Capstone Project/backend/

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import os
import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.mcp.tools import search_tools
from backend.app.services import pdf_parser
from backend.app.services import vector_store

logger = logging.getLogger("researchpilot.mcp.server")

# Try to import FastMCP, define fallback if not available
try:
    from mcp.server.fastmcp import FastMCP
    mcp_app = FastMCP("ResearchPilotAI")
    HAS_MCP = True
except ImportError:
    logger.warning("mcp SDK not found. FastMCP will not run as an external process, but local tool execution will work.")
    HAS_MCP = False
    class MockMCP:
        def tool(self):
            return lambda func: func
    mcp_app = MockMCP()

# Secure path validation
def validate_safe_path(path_str: str) -> Path:
    """
    Validates that file paths remain strictly inside the configured workspace upload directory.
    Prevents path traversal attacks.
    """
    target_path = Path(path_str).resolve()
    allowed_dir = settings.UPLOAD_DIR.resolve()
    
    # Check if target is inside allowed upload directory
    if not str(target_path).startswith(str(allowed_dir)):
        raise PermissionError(f"Access Denied: Path '{path_str}' is outside the authorized sandbox.")
    return target_path

# Register Tools

@mcp_app.tool()
def search_arxiv(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search arXiv database for research papers containing the keywords.
    """
    # Safe validation of limits
    limit = min(max(1, limit), 20)
    return search_tools.search_arxiv(query, limit)

@mcp_app.tool()
def search_semantic_scholar(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search Semantic Scholar for paper abstracts, citation and reference data.
    """
    limit = min(max(1, limit), 20)
    return search_tools.search_semantic_scholar(query, limit)

@mcp_app.tool()
def query_crossref(doi: str) -> Dict[str, Any]:
    """
    Query CrossRef for DOI-specific scientific publication metadata.
    """
    return search_tools.query_crossref(doi)

@mcp_app.tool()
def read_pdf_content(file_path: str) -> Dict[str, Any]:
    """
    Extract text, abstract heuristics, and document metadata from a PDF file.
    Only allows reading from the secure upload directory.
    """
    try:
        safe_path = validate_safe_path(file_path)
        if not safe_path.exists():
            return {"error": f"File not found: {file_path}"}
        return pdf_parser.extract_pdf_data(str(safe_path))
    except Exception as e:
        logger.error(f"Error in read_pdf_content tool: {e}")
        return {"error": str(e)}

@mcp_app.tool()
def vector_semantic_search(query: str, paper_ids: List[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Query the vector store for semantic matches of the query string.
    Filters by paper_ids if provided.
    """
    limit = min(max(1, limit), 15)
    return vector_store.query_documents(query, paper_ids, limit)

# Direct tool runner class for agents, bypassing MCP protocol layer for local speed
class LocalTools:
    @staticmethod
    def search_arxiv(query: str, limit: int = 5) -> List[Dict[str, Any]]:
        return search_arxiv(query, limit)
        
    @staticmethod
    def search_semantic_scholar(query: str, limit: int = 5) -> List[Dict[str, Any]]:
        return search_semantic_scholar(query, limit)
        
    @staticmethod
    def query_crossref(doi: str) -> Dict[str, Any]:
        return query_crossref(doi)
        
    @staticmethod
    def read_pdf_content(file_path: str) -> Dict[str, Any]:
        return read_pdf_content(file_path)
        
    @staticmethod
    def vector_semantic_search(query: str, paper_ids: List[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        return vector_semantic_search(query, paper_ids, limit)
