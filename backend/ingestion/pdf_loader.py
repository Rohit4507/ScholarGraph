"""
ScholarGraph AI — PDF Text Extraction
Uses PyMuPDF (fitz) for fast, high-quality text extraction from PDFs.
Falls back to OCR for scanned/image-based pages.
"""

import os
import fitz  # PyMuPDF
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class PageContent:
    """Represents extracted content from a single PDF page."""
    page_number: int
    text: str
    word_count: int
    has_images: bool
    is_scanned: bool = False
    metadata: Dict = field(default_factory=dict)


@dataclass
class DocumentContent:
    """Complete extracted content from a PDF document."""
    filename: str
    total_pages: int
    pages: List[PageContent]
    full_text: str
    total_words: int
    metadata: Dict = field(default_factory=dict)


class PDFLoader:
    """
    Production-grade PDF text extractor using PyMuPDF.
    
    Features:
    - Fast native text extraction for digital PDFs
    - Automatic detection of scanned/image-only pages
    - Page-level metadata extraction
    - Fallback to OCR for image-based content
    """

    # Minimum character threshold to consider a page as having text
    MIN_TEXT_THRESHOLD = 30

    def __init__(self, ocr_fallback: bool = True):
        """
        Initialize PDF loader.
        
        Args:
            ocr_fallback: Whether to attempt OCR on scanned pages
        """
        self.ocr_fallback = ocr_fallback

    def extract(self, file_path: str) -> DocumentContent:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Absolute path to the PDF file
            
        Returns:
            DocumentContent with all extracted text and metadata
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If the file is not a valid PDF
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {e}")

        pages: List[PageContent] = []
        all_text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract text using PyMuPDF's native text extraction
            text = page.get_text("text").strip()
            
            # Detect if page has images
            image_list = page.get_images(full=True)
            has_images = len(image_list) > 0
            
            # Determine if page is scanned (very little or no text but has images)
            is_scanned = len(text) < self.MIN_TEXT_THRESHOLD and has_images
            
            # If scanned and OCR fallback is enabled, try OCR
            if is_scanned and self.ocr_fallback:
                ocr_text = self._ocr_page(page)
                if ocr_text:
                    text = ocr_text
                    is_scanned = True

            word_count = len(text.split()) if text else 0

            page_content = PageContent(
                page_number=page_num + 1,
                text=text,
                word_count=word_count,
                has_images=has_images,
                is_scanned=is_scanned,
                metadata={
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "rotation": page.rotation,
                    "image_count": len(image_list),
                },
            )
            pages.append(page_content)
            if text:
                all_text_parts.append(text)

        full_text = "\n\n".join(all_text_parts)
        total_words = sum(p.word_count for p in pages)

        # Extract document-level metadata
        doc_metadata = doc.metadata or {}

        result = DocumentContent(
            filename=os.path.basename(file_path),
            total_pages=len(doc),
            pages=pages,
            full_text=full_text,
            total_words=total_words,
            metadata={
                "title": doc_metadata.get("title", ""),
                "author": doc_metadata.get("author", ""),
                "subject": doc_metadata.get("subject", ""),
                "creator": doc_metadata.get("creator", ""),
                "producer": doc_metadata.get("producer", ""),
                "creation_date": doc_metadata.get("creationDate", ""),
                "file_size_bytes": os.path.getsize(file_path),
            },
        )

        doc.close()
        return result

    def _ocr_page(self, page) -> Optional[str]:
        """
        Attempt OCR on a scanned page using Tesseract.
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            Extracted text or None if OCR fails
        """
        try:
            from ingestion.ocr_engine import OCREngine
            
            # Render page as image
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            
            ocr = OCREngine()
            return ocr.extract_from_bytes(img_bytes)
        except Exception:
            return None

    def extract_pages(self, file_path: str, page_numbers: List[int]) -> List[PageContent]:
        """Extract text from specific pages only."""
        full_doc = self.extract(file_path)
        return [p for p in full_doc.pages if p.page_number in page_numbers]

    def get_page_count(self, file_path: str) -> int:
        """Get the number of pages in a PDF without full extraction."""
        doc = fitz.open(file_path)
        count = len(doc)
        doc.close()
        return count
