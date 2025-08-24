"""RAG engine responsible for embedding queries and retrieving relevant context using FAISS.

At the moment we store the FAISS index on disk under `data/embeddings/quote_index.faiss` and a
JSON mapping file `data/quotes/index_map.json` which maps vector IDs ➜ original text.

To rebuild the index, run the helper script in `scripts/rebuild_index.py` (to be created) or
follow README instructions.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import List
from dotenv import load_dotenv

import faiss
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path(os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))
EMBEDDING_FILE = Path(os.getenv("FAISS_INDEX_PATH", str(DATA_DIR / "embeddings/quote_index.faiss")))
MAPPING_FILE = Path(os.getenv("FAISS_INDEX_MAP", str(DATA_DIR / "quotes/index_map.json")))

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Lazy singletons ------------------------------------------------------------
_model_instance: SentenceTransformer | None = None
_index_instance: faiss.IndexFlatIP | None = None


def _get_model() -> SentenceTransformer:
    global _model_instance
    if _model_instance is None:
        _model_instance = SentenceTransformer(MODEL_NAME)
    return _model_instance


def _get_index() -> faiss.Index:
    global _index_instance
    if _index_instance is None:
        if not EMBEDDING_FILE.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {EMBEDDING_FILE}. Have you built embeddings?"
            )
        _index_instance = faiss.read_index(str(EMBEDDING_FILE))
    return _index_instance


def build_index():
    """Build FAISS index from quotes in `data/quotes` and save it to disk."""
    model = _get_model()
    quote_dir = DATA_DIR / "quotes"

    if not quote_dir.exists() or not any(quote_dir.iterdir()):
        print(f"⚠️ Warning: Quote directory '{quote_dir}' is empty or doesn't exist.")
        print("Skipping index build. Please add .txt quote files to this directory.")
        return

    # Read all quote files
    quote_files = list(quote_dir.glob("*.txt"))
    documents = [q.read_text(encoding="utf-8") for q in quote_files]
    
    # Create embeddings
    print(f"Found {len(documents)} documents. Creating embeddings...")
    embeddings = model.encode(documents, show_progress_bar=True)
    
    # Build FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
    index.add(embeddings)
    
    # Create mapping from index ID to document content
    mapping = {str(i): doc for i, doc in enumerate(documents)}
    
    # Ensure output directories exist
    EMBEDDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    MAPPING_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Save index and mapping
    faiss.write_index(index, str(EMBEDDING_FILE))
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)
        
    print(f"✅ FAISS index saved to {EMBEDDING_FILE}")
    print(f"✅ Mapping file saved to {MAPPING_FILE}")


def retrieve_context(client_name: str, project_type: str, k: int = 3) -> List[str]:
    """Return *k* most relevant quote snippets.

    Parameters
    ----------
    client_name : str
        Name of the client provided by user.
    project_type : str
        Type/description of the project.
    k : int, optional
        Number of documents to return, by default 3.
    """

    query = f"{client_name} {project_type}"

    model = _get_model()
    index = _get_index()

    vec = model.encode([query])
    # FAISS expects shape (n_vectors, dim)
    D, I = index.search(vec, k)

    # FAISS returns -1 for padded IDs when fewer than k hits
    ids = [idx for idx in I[0] if idx != -1]

    if not ids:
        return []

    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        mapping = json.load(f)

    return [mapping[str(i)] for i in ids if str(i) in mapping]


def get_rag_context(query: str, max_results: int = 3) -> str:
    """
    Retrieve relevant context from RAG index for a given query.
    Returns formatted string with top matching documents.
    """
    try:
        # Load index mapping
        with open(MAPPING_FILE) as f:
            id_to_text = json.load(f)
        
        # Encode query
        model = _get_model()
        index = _get_index()
        query_embedding = model.encode([query])
        
        # Search index
        distances, indices = index.search(query_embedding, max_results)
        
        # Format results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx in id_to_text:
                results.append(f"Document {i+1} (relevance: {dist:.2f}):\n{id_to_text[idx]}")
        
        return "\n\n".join(results) if results else "No relevant documents found"
    except Exception as e:
        return f"Error retrieving RAG context: {str(e)}"
