"""
ScholarGraph AI — Text Cleaning Pipeline
Normalizes and cleans extracted text for downstream NLP processing.
"""

import re
import unicodedata
from typing import List


class TextCleaner:
    """
    Production-grade text cleaning pipeline for academic documents.
    
    Handles:
    - Unicode normalization
    - Header/footer removal
    - Noise character cleanup
    - Whitespace normalization
    - Page number removal
    - Encoding fix
    """

    # Common header/footer patterns in academic documents
    HEADER_FOOTER_PATTERNS = [
        r"^Page\s+\d+\s*(of\s+\d+)?$",
        r"^\d+\s*$",  # Standalone page numbers
        r"^(CONFIDENTIAL|DRAFT|DO NOT DISTRIBUTE).*$",
        r"^(University|Department|Faculty|School)\s+of\s+.*$",
        r"^(Semester|Term|Session)\s+\d+.*$",
        r"^\s*(©|Copyright).*$",
    ]

    # Noise patterns to remove
    NOISE_PATTERNS = [
        r"\x0c",  # Form feed characters
        r"\x00",  # Null bytes
        r"[\u200b\u200c\u200d\ufeff]",  # Zero-width characters
    ]

    def clean(self, text: str) -> str:
        """
        Apply full cleaning pipeline to extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""

        # Step 1: Unicode normalization
        text = unicodedata.normalize("NFKD", text)

        # Step 2: Remove noise characters
        for pattern in self.NOISE_PATTERNS:
            text = re.sub(pattern, "", text)

        # Step 3: Fix common encoding artifacts
        text = self._fix_encoding(text)

        # Step 4: Remove headers/footers
        text = self._remove_headers_footers(text)

        # Step 5: Normalize whitespace
        text = self._normalize_whitespace(text)

        # Step 6: Fix hyphenated line breaks
        text = self._fix_hyphenation(text)

        # Step 7: Clean up multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def _fix_encoding(self, text: str) -> str:
        """Fix common encoding artifacts."""
        replacements = {
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2014": "-",
            "\u2013": "-",
            "\u2022": "*",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    def _remove_headers_footers(self, text: str) -> str:
        """Remove common header/footer patterns from text."""
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()
            is_header_footer = False

            for pattern in self.HEADER_FOOTER_PATTERNS:
                if re.match(pattern, stripped, re.IGNORECASE):
                    is_header_footer = True
                    break

            if not is_header_footer:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize various types of whitespace."""
        # Replace tabs with spaces
        text = text.replace("\t", " ")
        # Replace multiple spaces with single space (preserve newlines)
        text = re.sub(r"[^\S\n]+", " ", text)
        # Remove trailing whitespace from each line
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        return text

    def _fix_hyphenation(self, text: str) -> str:
        """Rejoin words split across lines with hyphens."""
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
        return text

    def clean_batch(self, texts: List[str]) -> List[str]:
        """Clean a batch of text strings."""
        return [self.clean(t) for t in texts]

    @staticmethod
    def remove_references(text: str) -> str:
        """Remove reference sections from academic text."""
        # Find common reference section headers
        patterns = [
            r"\n(References|Bibliography|Works Cited)\s*\n.*",
            r"\n(REFERENCES|BIBLIOGRAPHY)\s*\n.*",
        ]
        for pattern in patterns:
            text = re.sub(pattern, "", text, flags=re.DOTALL | re.IGNORECASE)
        return text

    @staticmethod
    def extract_sections(text: str) -> List[dict]:
        """
        Extract sections from academic text based on heading patterns.
        
        Returns:
            List of dicts with 'heading' and 'content' keys
        """
        # Match numbered sections (1. Section, 1.1 Subsection, etc.)
        section_pattern = r"(?:^|\n)\s*(\d+(?:\.\d+)*\.?\s+[A-Z][^\n]+)\n"
        parts = re.split(section_pattern, text)

        sections = []
        for i in range(1, len(parts), 2):
            heading = parts[i].strip() if i < len(parts) else ""
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            if heading:
                sections.append({"heading": heading, "content": content})

        # If no sections found, return the whole text as one section
        if not sections:
            sections.append({"heading": "Full Document", "content": text})

        return sections
