import os
import logging
from typing import List, Dict, Any
from backend.app.config import settings

logger = logging.getLogger("researchpilot.vector_store")

# Global variables to store clients
_chroma_client = None
_collection = None
_in_memory_store = [] # Fallback database

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    
    # Initialize Chroma client
    _chroma_client = chromadb.PersistentClient(
        path=str(settings.CHROMA_DIR)
    )
    # Get or create collection
    _collection = _chroma_client.get_or_create_collection(
        name="research_papers",
        metadata={"hnsw:space": "cosine"}
    )
    logger.info("ChromaDB initialized successfully.")
except Exception as e:
    logger.warning(f"Failed to initialize ChromaDB: {e}. Falling back to in-memory store.")

def _get_gemini_embeddings(texts: List[str], is_query: bool = False) -> List[List[float]]:
    """
    Generate embeddings using Google Gemini API.
    If API Key is missing or service fails, returns mock embeddings.
    """
    if not settings.GEMINI_API_KEY:
        # Fallback to mock embedding vectors (1536 dimensions)
        import hashlib
        mock_embeddings = []
        for text in texts:
            # Seed vector with md5 hash of text
            h = hashlib.md5(text.encode('utf-8')).hexdigest()
            val = int(h, 16) / (16**32) # float between 0 and 1
            vector = [val * 0.1 for _ in range(768)] # 768 dims
            mock_embeddings.append(vector)
        return mock_embeddings

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        task_type = "retrieval_query" if is_query else "retrieval_document"
        
        # Batch call
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=texts,
            task_type=task_type
        )
        # Handle single vs batch response
        embeddings = result.get('embedding', [])
        if embeddings and isinstance(embeddings[0], float):
            return [embeddings]
        return embeddings
    except Exception as e:
        logger.error(f"Error calling Gemini Embedding API: {e}. Using mock embeddings.")
        # Fallback
        import hashlib
        mock_embeddings = []
        for text in texts:
            h = hashlib.md5(text.encode('utf-8')).hexdigest()
            val = int(h, 16) / (16**32)
            vector = [val * 0.1 for _ in range(768)]
            mock_embeddings.append(vector)
        return mock_embeddings

def add_documents(paper_id: str, title: str, chunks: List[str]):
    """
    Indexes paper chunks in the vector database (or fallback).
    """
    if not chunks:
        return
        
    embeddings = _get_gemini_embeddings(chunks, is_query=False)
    ids = [f"{paper_id}_{i}" for i in range(len(chunks))]
    metadatas = [{"paper_id": paper_id, "title": title, "chunk_index": i} for i in range(len(chunks))]
    
    if _collection is not None:
        try:
            _collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=chunks
            )
            logger.info(f"Indexed {len(chunks)} chunks in ChromaDB for paper {paper_id}")
            return
        except Exception as e:
            logger.error(f"Error adding to ChromaDB: {e}. Appending to in-memory fallback.")
            
    # Fallback to in-memory keyword matching
    for i, (chunk, metadata) in enumerate(zip(chunks, metadatas)):
        _in_memory_store.append({
            "id": ids[i],
            "paper_id": paper_id,
            "title": title,
            "text": chunk,
            "metadata": metadata
        })

def query_documents(query: str, paper_ids: List[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Queries vector store for relevant chunks matching the query.
    """
    if not query.strip():
        return []
        
    if _collection is not None:
        try:
            # Generate query embedding
            query_vector = _get_gemini_embeddings([query], is_query=True)[0]
            
            # Setup filter if paper_ids are provided
            where = None
            if paper_ids:
                if len(paper_ids) == 1:
                    where = {"paper_id": paper_ids[0]}
                else:
                    where = {"paper_id": {"$in": paper_ids}}
                    
            results = _collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
                where=where
            )
            
            output = []
            if results and results['documents']:
                for doc, meta, dist, id_ in zip(
                    results['documents'][0], 
                    results['metadatas'][0], 
                    results['distances'][0],
                    results['ids'][0]
                ):
                    output.append({
                        "id": id_,
                        "paper_id": meta["paper_id"],
                        "title": meta["title"],
                        "text": doc,
                        "score": float(1 - dist) # convert distance to similarity score
                    })
            return output
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}. Falling back to in-memory query.")
            
    # Fallback keyword matching (simple regex score count)
    query_words = [w.lower() for w in query.split() if len(w) > 2]
    matched = []
    for item in _in_memory_store:
        # Check if paper_ids filter matches
        if paper_ids and item["paper_id"] not in paper_ids:
            continue
            
        # Score based on keyword counts
        score = 0
        text_lower = item["text"].lower()
        for w in query_words:
            if w in text_lower:
                score += text_lower.count(w)
                
        if score > 0 or not query_words: # If query has no long words, match all
            matched.append((score, item))
            
    matched.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "id": item["id"],
            "paper_id": item["paper_id"],
            "title": item["title"],
            "text": item["text"],
            "score": score / (len(query_words) + 1) if query_words else 0.5
        }
        for score, item in matched[:limit]
    ]
