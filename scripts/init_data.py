"""
Script to initialize the FAISS index and sample data for testing.
"""
import os
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
EMBEDDING_DIR = DATA_DIR / "embeddings"
QUOTES_DIR = DATA_DIR / "quotes"
MODEL_NAME = "all-MiniLM-L6-v2"  # Same as in rag_engine.py

# Ensure directories exist
os.makedirs(EMBEDDING_DIR, exist_ok=True)
os.makedirs(QUOTES_DIR, exist_ok=True)

# Sample quotes data
SAMPLE_QUOTES = [
    "Website development typically takes 8-12 weeks and costs between $10,000-$30,000",
    "E-commerce website development usually takes 12-16 weeks with costs ranging from $25,000-$60,000",
    "Mobile app development typically takes 16-24 weeks with costs between $30,000-$100,000",
    "UI/UX design services typically cost $5,000-$20,000 depending on project scope",
    "Backend API development usually takes 4-8 weeks with costs from $10,000-$30,000",
    "Custom CRM development typically takes 12-20 weeks with costs between $40,000-$100,000",
    "Digital marketing services typically cost $2,000-$10,000 per month",
    "SEO optimization services usually cost $500-$5,000 per month depending on competition",
    "Content management system (CMS) setup typically takes 2-4 weeks and costs $3,000-$10,000",
    "Custom plugin development usually takes 2-6 weeks with costs from $2,000-$15,000",
    "UI/UX design services typically include research, wireframing, prototyping, and testing phases. Complete UI/UX projects range from $15,000-$50,000 with timelines of 4-12 weeks depending on complexity.",
    "UI/UX design breakdown: Research phase (1-2 weeks, $5,000-$10,000), Wireframing (2-3 weeks, $8,000-$15,000), UI Design (3-4 weeks, $12,000-$25,000), Prototyping (1-2 weeks, $5,000-$10,000), Testing (1 week, $3,000-$8,000)."
]

def initialize_faiss_index():
    """Initialize and save a FAISS index with sample quotes."""
    print("Initializing FAISS index with sample data...")
    
    # Initialize the sentence transformer model
    model = SentenceTransformer(MODEL_NAME)
    
    # Generate embeddings for the sample quotes
    print("Generating embeddings...")
    embeddings = model.encode(SAMPLE_QUOTES, show_progress_bar=True)
    
    # Create and save the FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
    index.add(embeddings.astype('float32'))
    
    # Save the index and mapping
    index_file = EMBEDDING_DIR / "quote_index.faiss"
    mapping_file = QUOTES_DIR / "index_map.json"
    
    faiss.write_index(index, str(index_file))
    print(f"Saved FAISS index to {index_file}")
    
    # Save the mapping of index to quote text
    mapping = {str(i): quote for i, quote in enumerate(SAMPLE_QUOTES)}
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    print(f"Saved quote mapping to {mapping_file}")
    
    # Save sample quotes as individual files
    for i, quote in enumerate(SAMPLE_QUOTES):
        quote_file = QUOTES_DIR / f"sample_quote_{i:02d}.txt"
        with open(quote_file, 'w') as f:
            f.write(quote)
    
    print(f"Saved {len(SAMPLE_QUOTES)} sample quote files")

if __name__ == "__main__":
    print("Initializing sample data for Business Knowledge Chat...")
    initialize_faiss_index()
    print("\nSetup complete! You can now run the application with:")
    print("uvicorn app.main:app --reload --port 8000")
    print("\nAccess the chat interface at: http://localhost:8000")
