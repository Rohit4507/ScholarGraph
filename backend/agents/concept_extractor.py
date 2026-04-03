"""
ScholarGraph AI — Agent 2: Concept Extraction Agent
Extracts topics, key terms, and concepts using NER and topic modeling.
"""

from typing import List, Dict, Optional
from config import get_settings

settings = get_settings()


CONCEPT_EXTRACTION_PROMPT = """You are an expert academic concept extractor. Analyze the following text and extract:

1. **Main Topics** — High-level topics (e.g., "Neural Networks", "Data Structures")
2. **Key Concepts** — Specific concepts within topics (e.g., "Backpropagation", "Binary Search Tree")
3. **Key Terms** — Important technical terms and definitions
4. **Learning Objectives** — What a student should know

Respond in JSON format:
{{
    "topics": [
        {{
            "name": "topic name",
            "subtopics": ["subtopic1", "subtopic2"],
            "importance": "high" | "medium" | "low"
        }}
    ],
    "key_concepts": ["concept1", "concept2"],
    "key_terms": [
        {{
            "term": "term name",
            "definition": "brief definition"
        }}
    ],
    "learning_objectives": ["objective1", "objective2"]
}}

Text to analyze:
{text}
"""


class ConceptExtractionAgent:
    """
    Agent 2: Extracts academic concepts, topics, and key terms.
    
    Uses:
    - LLM-based concept extraction for nuanced understanding
    - Keyword frequency analysis for term identification
    - Section heading parsing for topic structure
    """

    def extract(self, text: str, subject: str = "") -> Dict:
        """
        Extract concepts from document text.
        
        Args:
            text: Document text to analyze
            subject: Subject/course context
            
        Returns:
            Dict with topics, key_concepts, key_terms, learning_objectives
        """
        # Try LLM extraction first
        try:
            result = self._llm_extract(text, subject)
            if result:
                return result
        except Exception as e:
            print(f"LLM concept extraction failed: {e}")

        # Fallback to heuristic extraction
        return self._heuristic_extract(text)

    def _llm_extract(self, text: str, subject: str) -> Optional[Dict]:
        """Extract concepts using LLM."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage
            import json

            llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0,
                api_key=settings.OPENAI_API_KEY,
            )

            context = f"Subject: {subject}\n\n" if subject else ""
            prompt = CONCEPT_EXTRACTION_PROMPT.format(text=context + text[:4000])
            response = llm.invoke([HumanMessage(content=prompt)])

            return json.loads(response.content)

        except Exception as e:
            print(f"LLM extraction error: {e}")
            return None

    def _heuristic_extract(self, text: str) -> Dict:
        """Fallback heuristic-based concept extraction."""
        import re

        # Extract potential topics from headings
        heading_pattern = r"(?:^|\n)\s*(\d+\.?\s+[A-Z][^\n]+)"
        headings = re.findall(heading_pattern, text)

        topics = []
        for heading in headings[:20]:
            clean = re.sub(r"^\d+\.?\s+", "", heading).strip()
            if len(clean) > 3 and len(clean) < 100:
                topics.append({
                    "name": clean,
                    "subtopics": [],
                    "importance": "medium",
                })

        # Extract capitalized key terms
        term_pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b"
        terms = list(set(re.findall(term_pattern, text)))[:30]

        key_concepts = [t for t in terms if len(t.split()) <= 4]

        return {
            "topics": topics,
            "key_concepts": key_concepts[:15],
            "key_terms": [{"term": t, "definition": ""} for t in terms[:10]],
            "learning_objectives": [],
        }
