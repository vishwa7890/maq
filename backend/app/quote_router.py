from fastapi import APIRouter, HTTPException, status
from app.models import QuoteRequest, QuoteResponse
from app.rag_engine import retrieve_context
from app.ollama_client import generate_quote

router = APIRouter()


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_200_OK)
async def create_quote(req: QuoteRequest) -> QuoteResponse:
    """Generate a project quote leveraging RAG and a local AI model via Ollama."""
    try:
        # 1. Retrieve relevant past documents
        context_docs = retrieve_context(req.client_name, req.project_type)

        # 2. Send augmented prompt to Claude
        quote_result = generate_quote(req, context_docs)
        return quote_result  # Already conforms to QuoteResponse

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
