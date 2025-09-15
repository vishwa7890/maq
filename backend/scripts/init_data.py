"""
Script to initialize the FAISS index and sample data for testing using Hugging Face API.
"""
import os
import json
import numpy as np
import faiss
import httpx
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
EMBEDDING_DIR = DATA_DIR / "embeddings"
QUOTES_DIR = DATA_DIR / "quotes"

# Hugging Face API Configuration
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
EMBEDDING_MODEL_API = os.getenv("EMBEDDING_MODEL_API", "sentence-transformers/all-MiniLM-L6-v2")
HUGGINGFACE_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{EMBEDDING_MODEL_API}"

# Ensure directories exist
os.makedirs(EMBEDDING_DIR, exist_ok=True)
os.makedirs(QUOTES_DIR, exist_ok=True)

# Sample quotes data
SAMPLE_QUOTES = [
    """Business-Related Content Access: This system is designed exclusively for business-related queries including Project Estimation & Services, Pricing & Plans, Business Strategy & Planning, Technology Recommendations, and Industry-Specific Solutions. Please ask questions related to project costs and timelines, service quotations and pricing, business strategy and planning, technology recommendations for business, and industry-specific solutions.""",
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
    "UI/UX design breakdown: Research phase (1-2 weeks, $5,000-$10,000), Wireframing (2-3 weeks, $8,000-$15,000), UI Design (3-4 weeks, $12,000-$25,000), Prototyping (1-2 weeks, $5,000-$10,000), Testing (1 week, $3,000-$8,000).",
    "Project Estimation Services: We provide comprehensive project estimation for software development, web development, mobile applications, and digital transformation projects. Our estimates include detailed cost breakdowns, timeline analysis, resource allocation, and risk assessment.",
    "Pricing Plans: Our pricing structure includes hourly rates, fixed-price projects, and retainer-based services. We offer competitive rates for startups, SMEs, and enterprise clients with flexible payment terms and milestone-based billing.",
    "Business Strategy Planning: We help businesses develop technology roadmaps, digital transformation strategies, market entry plans, and competitive analysis. Our strategic consulting covers technology stack selection, scalability planning, and ROI optimization.",
    "Technology Recommendations: We provide expert recommendations on programming languages, frameworks, databases, cloud platforms, and development tools. Our technology consulting covers architecture design, performance optimization, and security best practices.",
    "Industry-Specific Solutions: We specialize in solutions for healthcare, fintech, e-commerce, education, real estate, and manufacturing industries. Our domain expertise includes compliance requirements, industry standards, and sector-specific challenges."
]

async def get_embeddings_from_hf_api(texts):
    """Get embeddings from Hugging Face API"""
    if not HUGGINGFACE_API_KEY:
        raise ValueError("HUGGINGFACE_API_KEY is not set in environment variables")
    
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                HUGGINGFACE_API_URL,
                headers=headers,
                json={"inputs": texts, "options": {"wait_for_model": True}},
                timeout=60.0
            )
            response.raise_for_status()
            embeddings = response.json()
            return np.array(embeddings)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 503:
                # Model is loading, wait and retry
                print("Model is loading, waiting 20 seconds...")
                await asyncio.sleep(20)
                response = await client.post(
                    HUGGINGFACE_API_URL,
                    headers=headers,
                    json={"inputs": texts, "options": {"wait_for_model": True}},
                    timeout=60.0
                )
                response.raise_for_status()
                embeddings = response.json()
                return np.array(embeddings)
            else:
                raise

async def initialize_faiss_index():
    """Initialize and save a FAISS index with sample quotes using Hugging Face API."""
    print("Initializing FAISS index with sample data using Hugging Face API...")
    
    if not HUGGINGFACE_API_KEY or HUGGINGFACE_API_KEY == "your_huggingface_api_key_here":
        print("ERROR: Please set your HUGGINGFACE_API_KEY in the .env file")
        print("You can get a free API key from: https://huggingface.co/settings/tokens")
        return
    
    # Generate embeddings for the sample quotes using Hugging Face API
    print("Generating embeddings using Hugging Face API...")
    embeddings = await get_embeddings_from_hf_api(SAMPLE_QUOTES)
    
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
    asyncio.run(initialize_faiss_index())
    print("\nSetup complete! You can now run the application with:")
    print("uvicorn app.main:app --reload --port 8000")
    print("\nAccess the chat interface at: http://localhost:8000")
