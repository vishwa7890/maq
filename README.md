# Lumina Quo with RAG + Knowledge Graph

A FastAPI-based chat application that combines Retrieval-Augmented Generation (RAG) with a knowledge graph to provide intelligent responses about business services, products, and project estimates.

## Features

* **Chat Interface** - Interactive web interface for natural language queries
* **Knowledge Graph** - Structured representation of business entities and relationships
* **RAG Integration** - Retrieval-augmented generation for context-aware responses
* **Vector Search (FAISS)** - Efficient semantic search for relevant information
* **Ollama Integration** - Local LLM inference with Mistral model

## Project Structure

```
ai_quotemaster_rag/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application and routes
│   ├── chat_router.py    # Chat API endpoints
│   ├── models.py         # Pydantic models
│   ├── rag_engine.py     # Vector search and retrieval
│   ├── knowledge_graph.py # Business knowledge graph
│   └── ollama_client.py  # Ollama LLM integration
├── data/
│   ├── embeddings/       # FAISS index for vector search
│   └── quotes/           # Document store for RAG
├── static/               # Frontend assets
│   └── index.html        # Chat interface
└── requirements.txt      # Python dependencies
```

## Quick Start

1. **Set up the environment**
   ```bash
   # Create and activate virtual environment
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac

   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Set up Ollama**
   ```bash
   # Install Ollama from https://ollama.ai/
   # Then pull the Mistral model
   ollama pull mistral
   ```

3. **Set up FAISS index**
   - Place your FAISS index at `data/embeddings/quote_index.faiss`
   - Ensure the mapping JSON is at `data/quotes/index_map.json`

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Access the application**
   - Chat interface: http://localhost:8000
   - API documentation: http://localhost:8000/docs

## API Endpoints

- `POST /api/chat` - Send a chat message and get a response
- `GET /api/chat/estimates/recent` - Get recent estimates
- `POST /api/chat/estimate/uiux` - Get a UI/UX estimate (structured input)

## Configuration

Environment variables:
- `OLLAMA_MODEL` - The Ollama model to use (default: "mistral")
- `MAX_PROMPT_LENGTH` - Maximum length of the prompt (default: 8000)

## Features in Detail

### Knowledge Graph
- Stores business entities (products, services) and their relationships
- Provides contextual information for more accurate responses
- Can be extended with additional entity types and relationships

### RAG Integration
- Retrieves relevant information from the document store
- Combines retrieved information with the knowledge graph context
- Provides more accurate and relevant responses

### Chat Interface
- Clean, responsive web interface
- Real-time message streaming
- Message history management

* Script for building the FAISS index.
* Voice transcription endpoint.
* Authentication (API key / OAuth).
