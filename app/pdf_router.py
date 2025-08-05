"""
PDF Upload and Comparison Router
Handles PDF file uploads, processing, and comparison with cost estimations.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from models.base import get_db
from models import User, DocumentORM, PDFComparisonORM, ChatSessionORM
from app.auth import get_current_user
from app.schemas import PDFUploadResponse, ComparisonResult, PDFComparisonRequest
from app.pdf_processor import PDFProcessor, CostEstimationComparator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pdf"])

# Configure upload directory
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file types and extensions
ALLOWED_EXTENSIONS = {".pdf", ".mp4", ".webm", ".mov"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "video/mp4",
    "video/webm",
    "video/quicktime"
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB for videos

@router.post("/upload-docs/", response_model=List[PDFUploadResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    session_uuid: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload multiple PDF documents for processing and comparison
    
    Args:
        files: List of PDF files to upload
        chat_id: Optional chat session ID to associate with uploads
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of upload responses with document IDs and processing status
    """
    try:
        uploaded_docs = []
        processor = PDFProcessor()
        
        for file in files:
            # Validate file
            if not file.filename:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File name is required"
                )
            
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file_ext} not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
                )
            
            # Check file size
            file_content = await file.read()
            if len(file_content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File {file.filename} is too large. Maximum size is 50MB."
                )
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{current_user.id}_{timestamp}_{file.filename}"
            file_path = UPLOAD_DIR / safe_filename
            
            # Save file
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            
            # Get session if UUID is provided
            session_id = None
            if session_uuid:
                session_result = await db.execute(
                    select(ChatSessionORM.id).where(
                        (ChatSessionORM.session_uuid == session_uuid) &
                        (ChatSessionORM.user_id == current_user.id)
                    )
                )
                session_id = session_result.scalar_one_or_none()
                if not session_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Chat session with UUID {session_uuid} not found."
                    )

            # Create database record
            document = DocumentORM(
                user_id=current_user.id,
                session_id=session_id,
                filename=file.filename,
                filepath=str(file_path),
                filetype=file_ext,
                filesize=len(file_content),
                processed=False
            )
            
            db.add(document)
            await db.flush()  # Get the ID
            
            # Process file based on type
            if file.content_type.startswith('video/'):
                # For videos, just store the file
                document.processed = True
                message = "Video uploaded successfully"
            else:
                # Process PDFs normally
                try:
                    extracted_data = processor.extract_text_and_tables(str(file_path))
                    document.extracted_text = extracted_data.get("text", "")
                    document.extracted_tables = extracted_data.get("tables", [])
                    document.processed = True
                    message = "Document processed successfully"
                except Exception as e:
                    logger.error(f"Error processing file {file.filename}: {str(e)}")
                    message = f"Upload succeeded but processing failed: {str(e)}"
            
            await db.commit()
            
            uploaded_docs.append(PDFUploadResponse(
                document_id=document.id,
                filename=file.filename,
                filesize=len(file_content),
                processed=document.processed,
                message=message
            ))
        
        return uploaded_docs
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.post("/compare-estimation/", response_model=ComparisonResult)
async def compare_with_estimation(
    request: PDFComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Compare uploaded PDF with cost estimation
    
    Args:
        request: Comparison request with document ID and estimation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Comparison results with similarity score and analysis
    """
    try:
        # Get document
        result = await db.execute(
            select(DocumentORM).where(
                and_(
                    DocumentORM.id == request.document_id,
                    DocumentORM.user_id == current_user.id
                )
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if not document.processed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document is still being processed"
            )
        
        # Prepare PDF content for comparison
        pdf_content = {
            "text": document.extracted_text or "",
            "tables": document.extracted_tables or []
        }
        
        # Perform comparison
        comparator = CostEstimationComparator()
        comparison_result = comparator.compare_with_estimation(
            pdf_content, 
            request.estimation_data
        )
        
        # Save comparison to database
        pdf_comparison = PDFComparisonORM(
            user_id=current_user.id,
            chat_id=request.chat_id,
            document_id=request.document_id,
            estimation_json=request.estimation_data,
            comparison_score=comparison_result["match_score"],
            mismatch_details=comparison_result["mismatches"]
        )
        
        db.add(pdf_comparison)
        await db.commit()
        
        # Format response
        return ComparisonResult(
            document_id=request.document_id,
            filename=document.filename,
            match_score=comparison_result["match_score"],
            closest_matches=[
                {
                    "pdf_content": match["pdf_content"],
                    "estimation_content": match["estimation_content"],
                    "similarity": str(match["similarity"])
                }
                for match in comparison_result["closest_matches"]
            ],
            mismatches=comparison_result["mismatches"],
            suggestions=comparison_result["suggestions"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing estimation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )

@router.get("/documents/", response_model=List[Dict[str, Any]])
async def list_user_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all documents uploaded by the current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of user's documents with metadata
    """
    try:
        result = await db.execute(
            select(DocumentORM).where(
                DocumentORM.user_id == current_user.id
            ).order_by(DocumentORM.uploaded_at.desc())
        )
        documents = result.scalars().all()
        
        return [
            {
                "id": doc.id,
                "filename": doc.filename,
                "filesize": doc.filesize,
                "filetype": doc.filetype,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "processed": doc.processed,
                "has_comparisons": len(doc.comparisons) > 0 if doc.comparisons else False
            }
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )

@router.get("/comparisons/{document_id}", response_model=List[Dict[str, Any]])
async def get_document_comparisons(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all comparisons for a specific document
    
    Args:
        document_id: ID of the document
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of comparisons for the document
    """
    try:
        result = await db.execute(
            select(PDFComparisonORM).where(
                and_(
                    PDFComparisonORM.document_id == document_id,
                    PDFComparisonORM.user_id == current_user.id
                )
            ).order_by(PDFComparisonORM.created_at.desc())
        )
        comparisons = result.scalars().all()
        
        return [
            {
                "id": comp.id,
                "comparison_score": comp.comparison_score,
                "mismatch_details": comp.mismatch_details,
                "created_at": comp.created_at.isoformat(),
                "estimation_data": comp.estimation_json
            }
            for comp in comparisons
        ]
        
    except Exception as e:
        logger.error(f"Error getting comparisons: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comparisons: {str(e)}"
        )

@router.get("/files/{document_id}")
async def serve_file(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Serve uploaded file (PDF or video) to authenticated users
    """
    result = await db.execute(
        select(DocumentORM).where(
            and_(
                DocumentORM.id == document_id,
                DocumentORM.user_id == current_user.id
            )
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not Path(document.filepath).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    return FileResponse(
        document.filepath,
        media_type=document.filetype,
        filename=document.filename
    )

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document and its associated file
    
    Args:
        document_id: ID of the document to delete
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    try:
        # Get document
        result = await db.execute(
            select(DocumentORM).where(
                and_(
                    DocumentORM.id == document_id,
                    DocumentORM.user_id == current_user.id
                )
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Delete physical file
        try:
            file_path = Path(document.filepath)
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.warning(f"Could not delete file {document.filepath}: {str(e)}")
        
        # Delete from database (cascades to comparisons)
        await db.delete(document)
        await db.commit()
        
        return {"message": f"Document {document.filename} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
