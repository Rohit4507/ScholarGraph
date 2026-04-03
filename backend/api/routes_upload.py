"""
ScholarGraph AI — Document Upload API Routes
Handles file upload, document processing, and ingestion pipeline.
"""

import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from config import get_settings
from database.session import get_db
from database.models import Document
from ingestion.pdf_loader import PDFLoader
from ingestion.text_cleaner import TextCleaner
from ingestion.semantic_chunker import SemanticChunker
from embeddings.generator import EmbeddingGenerator
from embeddings.pinecone_store import PineconeStore
from agents.document_classifier import DocumentClassifierAgent
from agents.concept_extractor import ConceptExtractionAgent
from auth.jwt_handler import get_current_user, get_optional_user

settings = get_settings()
router = APIRouter()


@router.post("/")
async def upload_document(
    file: UploadFile = File(...),
    subject: str = Form(""),
    doc_type: str = Form(""),  # syllabus, pyq, lecture_notes
    semester: str = Form(""),
    year: Optional[str] = Form(None),  # form sends string; convert to int below
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """
    Upload and process a document (PDF).
    
    Pipeline:
    1. Save file to disk
    2. Extract text (PyMuPDF + OCR fallback)
    3. Clean text
    4. Auto-classify document type (if not provided)
    5. Extract concepts and topics
    6. Chunk text semantically
    7. Generate embeddings
    8. Store in Pinecone vector database
    
    Returns processing results with extracted topics and chunk count.
    """
    # Parse year from form (form data is always string)
    year_parsed: Optional[int] = None
    if year is not None and str(year).strip():
        try:
            year_parsed = int(year)
        except (ValueError, TypeError):
            year_parsed = None
    year = year_parsed

    # Validate file type
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Supported: {settings.ALLOWED_EXTENSIONS}",
        )

    # Save file
    file_id = str(uuid.uuid4())
    safe_name = f"{file_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    content = await file.read()

    # Check file size
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    try:
        # ── Step 1: Extract Text ────────────────────────────────
        loader = PDFLoader()
        doc_content = loader.extract(file_path)

        # ── Step 2: Clean Text ──────────────────────────────────
        cleaner = TextCleaner()
        cleaned_text = cleaner.clean(doc_content.full_text)

        # ── Step 3: Auto-Classify ───────────────────────────────
        classifier = DocumentClassifierAgent()
        if not doc_type:
            classification = classifier.classify(cleaned_text)
            doc_type = classification.get("doc_type", "lecture_notes")
        else:
            classification = {"doc_type": doc_type, "confidence": 1.0, "method": "user_provided"}

        # ── Step 4: Extract Concepts ────────────────────────────
        extractor = ConceptExtractionAgent()
        concepts = extractor.extract(cleaned_text, subject)
        topics = [t["name"] for t in concepts.get("topics", [])]

        # ── Step 5: Chunk Text ──────────────────────────────────
        chunker = SemanticChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        chunks = chunker.chunk_text(cleaned_text, doc_type, subject)

        # ── Step 6: Generate Embeddings ─────────────────────────
        embedder = EmbeddingGenerator()
        chunk_texts = [c.text for c in chunks]
        embeddings = embedder.embed_batch(chunk_texts)

        # ── Step 7: Store in Pinecone ───────────────────────────
        store = PineconeStore()
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            tenant_id = ""
            if current_user and hasattr(current_user, "tenant_id"):
                tenant_id = current_user.tenant_id or ""

            vectors.append({
                "id": f"{file_id}_{i:04d}",
                "values": embedding,
                "metadata": {
                    "text": chunk.text[:1000],
                    "doc_type": doc_type,
                    "subject": subject,
                    "section": chunk.section_heading,
                    "page": chunk.start_page or 0,
                    "year": year or 0,
                    "document_id": file_id,
                    "tenant_id": tenant_id,
                },
            })

        namespace = ""
        if current_user and hasattr(current_user, "tenant_id"):
            namespace = current_user.tenant_id or ""
        upserted_count = store.upsert_vectors(vectors, namespace=namespace)

        # ── Step 8: Save to Database ────────────────────────────
        doc_record = Document(
            id=file_id,
            filename=safe_name,
            original_name=file.filename,
            doc_type=doc_type,
            subject=subject,
            semester=semester,
            year=year,
            file_path=file_path,
            file_size_bytes=len(content),
            page_count=doc_content.total_pages,
            processing_status="completed",
            extracted_text=cleaned_text[:10000],
            chunk_count=len(chunks),
            uploaded_by=current_user.id if current_user else None,
            tenant_id=current_user.tenant_id if current_user and hasattr(current_user, "tenant_id") else None,
        )
        db.add(doc_record)
        db.commit()

        return {
            "status": "success",
            "document_id": file_id,
            "filename": file.filename,
            "doc_type": doc_type,
            "classification": classification,
            "pages": doc_content.total_pages,
            "total_words": doc_content.total_words,
            "chunks_created": len(chunks),
            "vectors_stored": upserted_count,
            "topics_extracted": topics[:20],
            "concepts": concepts.get("key_concepts", [])[:15],
        }

    except Exception as e:
        # Update status to failed
        doc_record = Document(
            id=file_id,
            filename=safe_name,
            original_name=file.filename,
            doc_type=doc_type or "unknown",
            subject=subject,
            file_path=file_path,
            file_size_bytes=len(content),
            processing_status="failed",
        )
        db.add(doc_record)
        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(e)}",
        )


@router.get("/documents")
async def list_documents(
    subject: Optional[str] = None,
    doc_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_optional_user),
):
    """List all uploaded documents with optional filtering."""
    query = db.query(Document)

    if subject:
        query = query.filter(Document.subject == subject)
    if doc_type:
        query = query.filter(Document.doc_type == doc_type)
    if current_user and hasattr(current_user, "tenant_id") and current_user.tenant_id:
        query = query.filter(Document.tenant_id == current_user.tenant_id)

    documents = query.order_by(Document.created_at.desc()).all()

    return {
        "total": len(documents),
        "documents": [
            {
                "id": doc.id,
                "filename": doc.original_name,
                "doc_type": doc.doc_type,
                "subject": doc.subject,
                "status": doc.processing_status,
                "pages": doc.page_count,
                "chunks": doc.chunk_count,
                "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
            }
            for doc in documents
        ],
    }
