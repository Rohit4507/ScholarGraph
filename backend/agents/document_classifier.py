"""
ScholarGraph AI — Agent 1: Document Classifier
Detects document type: syllabus, exam paper (PYQ), or lecture notes.
Uses LLM-based classification with confidence scoring.
"""

from typing import Dict, Optional
from config import get_settings

settings = get_settings()


CLASSIFICATION_PROMPT = """You are an academic document classifier. Analyze the following text excerpt and classify it into exactly ONE of these categories:

1. **syllabus** — Course outline with topics, learning objectives, module breakdowns, credit hours
2. **pyq** — Past Year Question paper with exam questions, marks distribution, question numbers
3. **lecture_notes** — Lecture slides, class notes, textbook excerpts, study material with explanations

Respond in JSON format:
{{
    "doc_type": "syllabus" | "pyq" | "lecture_notes",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}}

Document text (first 2000 characters):
{text}
"""


class DocumentClassifierAgent:
    """
    Agent 1: Classifies uploaded documents into syllabus, PYQ, or lecture notes.
    
    Uses a combination of:
    - LLM-based content analysis
    - Keyword heuristics for fast pre-classification
    - Confidence scoring for ambiguous documents
    """

    # Keyword indicators for each document type
    KEYWORDS = {
        "syllabus": [
            "course outline", "syllabus", "learning objectives",
            "module", "credit hours", "course code", "prerequisites",
            "curriculum", "course structure", "semester plan",
        ],
        "pyq": [
            "question paper", "exam", "marks", "attempt any",
            "answer all", "time allowed", "maximum marks",
            "q.", "q1", "q2", "question no", "examination",
            "total marks", "roll no", "seat no",
        ],
        "lecture_notes": [
            "definition", "theorem", "example", "solution",
            "proof", "concept", "introduction", "summary",
            "chapter", "topic", "explanation", "key points",
        ],
    }

    def classify(self, text: str, use_llm: bool = True) -> Dict:
        """
        Classify a document based on its text content.
        
        Args:
            text: Extracted document text
            use_llm: Whether to use LLM for classification (slower but more accurate)
            
        Returns:
            Dict with doc_type, confidence, and reasoning
        """
        # Step 1: Quick heuristic classification
        heuristic_result = self._heuristic_classify(text)

        # If heuristic is very confident, return immediately
        if heuristic_result["confidence"] >= 0.85:
            return heuristic_result

        # Step 2: LLM-based classification for ambiguous cases
        if use_llm:
            try:
                llm_result = self._llm_classify(text)
                if llm_result:
                    # Combine heuristic and LLM results
                    return self._merge_results(heuristic_result, llm_result)
            except Exception as e:
                print(f"LLM classification failed: {e}")

        return heuristic_result

    def _heuristic_classify(self, text: str) -> Dict:
        """Fast keyword-based classification."""
        text_lower = text.lower()
        scores = {}

        for doc_type, keywords in self.KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            scores[doc_type] = matches / len(keywords)

        # Get the best match
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        # Calculate confidence
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0.33

        return {
            "doc_type": best_type,
            "confidence": round(min(1.0, confidence), 3),
            "reasoning": (
                f"Heuristic classification based on keyword matching. "
                f"Scores: {', '.join(f'{k}={v:.2f}' for k, v in scores.items())}"
            ),
            "method": "heuristic",
        }

    def _llm_classify(self, text: str) -> Optional[Dict]:
        """LLM-based classification using OpenAI."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage
            import json

            llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0,
                api_key=settings.OPENAI_API_KEY,
            )

            prompt = CLASSIFICATION_PROMPT.format(text=text[:2000])
            response = llm.invoke([HumanMessage(content=prompt)])

            # Parse JSON response
            result = json.loads(response.content)
            result["method"] = "llm"
            return result

        except Exception as e:
            print(f"LLM classification error: {e}")
            return None

    def _merge_results(self, heuristic: Dict, llm: Dict) -> Dict:
        """Merge heuristic and LLM classification results."""
        if heuristic["doc_type"] == llm["doc_type"]:
            # Agreement — high confidence
            return {
                "doc_type": llm["doc_type"],
                "confidence": round(
                    max(heuristic["confidence"], llm.get("confidence", 0.8)), 3
                ),
                "reasoning": (
                    f"Both heuristic and LLM agree: {llm['doc_type']}. "
                    f"{llm.get('reasoning', '')}"
                ),
                "method": "combined",
            }
        else:
            # Disagreement — use LLM but lower confidence
            return {
                "doc_type": llm["doc_type"],
                "confidence": round(llm.get("confidence", 0.6) * 0.9, 3),
                "reasoning": (
                    f"LLM classified as {llm['doc_type']} "
                    f"(heuristic suggested {heuristic['doc_type']}). "
                    f"{llm.get('reasoning', '')}"
                ),
                "method": "llm_override",
            }
