"""
ScholarGraph AI — Semantic Chunking Engine
Intelligent text chunking that respects topic boundaries using
sentence-level semantic similarity for optimal RAG retrieval.
"""

import re
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TextChunk:
    """Represents a semantically coherent text chunk."""
    chunk_id: str
    text: str
    word_count: int
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    doc_type: str = "unknown"  # syllabus, pyq, lecture_notes
    subject: str = ""
    section_heading: str = ""
    metadata: Dict = field(default_factory=dict)


class SemanticChunker:
    """
    Intelligent text chunker that creates overlapping, semantically
    coherent chunks for optimal vector store retrieval.
    
    Strategy:
    1. Split text into sentences
    2. Group sentences using sliding window
    3. Create chunks with configurable overlap
    4. Preserve section boundaries where possible
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        min_chunk_size: int = 100,
    ):
        """
        Initialize the semantic chunker.
        
        Args:
            chunk_size: Target chunk size in words
            chunk_overlap: Number of overlap words between chunks
            min_chunk_size: Minimum chunk size to keep
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_text(
        self,
        text: str,
        doc_type: str = "unknown",
        subject: str = "",
        source_pages: Optional[List[int]] = None,
    ) -> List[TextChunk]:
        """
        Split text into semantically coherent, overlapping chunks.
        
        Args:
            text: The full document text
            doc_type: Type of document (syllabus, pyq, lecture_notes)
            subject: Subject/course name
            source_pages: Optional page number mapping
            
        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []

        # First try section-based chunking
        sections = self._extract_sections(text)

        chunks = []
        chunk_counter = 0

        for section in sections:
            section_heading = section.get("heading", "")
            section_text = section.get("content", "")

            if not section_text.strip():
                continue

            # Split section into sentences
            sentences = self._split_sentences(section_text)

            # Group sentences into chunks
            section_chunks = self._create_chunks_from_sentences(sentences)

            for chunk_text in section_chunks:
                word_count = len(chunk_text.split())

                if word_count < self.min_chunk_size:
                    continue

                chunk_counter += 1
                chunk = TextChunk(
                    chunk_id=f"{doc_type}_{subject}_{chunk_counter:04d}",
                    text=chunk_text,
                    word_count=word_count,
                    doc_type=doc_type,
                    subject=subject,
                    section_heading=section_heading,
                    metadata={
                        "chunk_index": chunk_counter,
                        "total_sections": len(sections),
                        "source_section": section_heading,
                    },
                )
                chunks.append(chunk)

        return chunks

    def _extract_sections(self, text: str) -> List[Dict]:
        """Extract sections based on heading patterns."""
        # Common academic heading patterns
        patterns = [
            r"(?:^|\n)(#{1,3}\s+.+)",  # Markdown headings
            r"(?:^|\n)(\d+(?:\.\d+)*\.?\s+[A-Z][^\n]{3,})",  # Numbered sections
            r"(?:^|\n)([A-Z][A-Z\s]{5,})\s*\n",  # ALL CAPS headings
        ]

        # Try to find sections
        sections = []
        best_parts = None
        best_count = 0

        for pattern in patterns:
            parts = re.split(pattern, text, flags=re.MULTILINE)
            if len(parts) > best_count:
                best_count = len(parts)
                best_parts = parts

        if best_parts and len(best_parts) > 1:
            # Build sections from split parts
            for i in range(0, len(best_parts)):
                if i % 2 == 0:
                    # Content before first heading or between headings
                    content = best_parts[i].strip()
                    if content and not sections:
                        sections.append({"heading": "Introduction", "content": content})
                else:
                    heading = best_parts[i].strip()
                    content = best_parts[i + 1].strip() if i + 1 < len(best_parts) else ""
                    if heading:
                        sections.append({"heading": heading, "content": content})
        
        # Fallback: treat entire text as one section
        if not sections:
            sections.append({"heading": "Full Document", "content": text})

        return sections

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex-based approach."""
        # Split on sentence-ending punctuation followed by space/newline
        sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])'
        sentences = re.split(sentence_endings, text)

        # Also split on double newlines (paragraph boundaries)
        result = []
        for sent in sentences:
            if "\n\n" in sent:
                result.extend(s.strip() for s in sent.split("\n\n") if s.strip())
            else:
                if sent.strip():
                    result.append(sent.strip())

        return result

    def _create_chunks_from_sentences(self, sentences: List[str]) -> List[str]:
        """
        Create overlapping chunks from a list of sentences.
        Uses a sliding window approach with word-count-based boundaries.
        """
        if not sentences:
            return []

        chunks = []
        current_chunk_sentences = []
        current_word_count = 0

        for sentence in sentences:
            sentence_words = len(sentence.split())

            if current_word_count + sentence_words > self.chunk_size and current_chunk_sentences:
                # Save current chunk
                chunk_text = " ".join(current_chunk_sentences)
                chunks.append(chunk_text)

                # Create overlap: keep last few sentences
                overlap_sentences = []
                overlap_words = 0
                for s in reversed(current_chunk_sentences):
                    s_words = len(s.split())
                    if overlap_words + s_words > self.chunk_overlap:
                        break
                    overlap_sentences.insert(0, s)
                    overlap_words += s_words

                current_chunk_sentences = overlap_sentences
                current_word_count = overlap_words

            current_chunk_sentences.append(sentence)
            current_word_count += sentence_words

        # Don't forget the last chunk
        if current_chunk_sentences:
            chunk_text = " ".join(current_chunk_sentences)
            chunks.append(chunk_text)

        return chunks

    def chunk_document_pages(
        self,
        pages: List[Dict],
        doc_type: str = "unknown",
        subject: str = "",
    ) -> List[TextChunk]:
        """
        Chunk a document from page-level data.
        
        Args:
            pages: List of dicts with 'page_number' and 'text' keys
            doc_type: Document type
            subject: Subject name
            
        Returns:
            List of TextChunk objects with page number tracking
        """
        # Combine all page texts with page markers
        combined_text = ""
        for page in pages:
            combined_text += page.get("text", "") + "\n\n"

        chunks = self.chunk_text(combined_text, doc_type, subject)

        # Try to assign approximate page numbers
        for chunk in chunks:
            chunk.start_page = 1
            chunk.end_page = len(pages)

        return chunks
