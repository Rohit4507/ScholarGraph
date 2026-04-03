"""
ScholarGraph AI — Agent 7: Quiz Generator Agent
Creates adaptive MCQs with difficulty levels (easy/medium/hard)
using LLM-based question generation.
"""

from typing import List, Dict, Optional
from config import get_settings

settings = get_settings()


QUIZ_GENERATION_PROMPT = """You are an expert exam question generator. Create {count} multiple-choice questions on the topic "{topic}" for subject "{subject}".

Difficulty level: {difficulty}
Context from study material:
{context}

Generate questions in JSON format:
{{
    "questions": [
        {{
            "question": "Question text here?",
            "options": {{
                "A": "Option A text",
                "B": "Option B text",
                "C": "Option C text",
                "D": "Option D text"
            }},
            "correct_answer": "A",
            "explanation": "Brief explanation of why this is correct",
            "difficulty": "{difficulty}",
            "topic": "{topic}"
        }}
    ]
}}

Rules:
- Questions should test conceptual understanding, not just memorization
- All four options should be plausible
- Explanations should be educational
- For "hard" difficulty, include application-based or analytical questions
- For "easy" difficulty, focus on definitions and basic concepts
"""


class QuizGeneratorAgent:
    """
    Agent 7: Generates adaptive MCQ quizzes using LLM.
    
    Features:
    - Difficulty-level classification (easy/medium/hard)
    - Context-aware question generation using RAG results
    - Adaptive difficulty based on student performance
    - Detailed explanations for learning
    """

    def generate_quiz(
        self,
        topic: str,
        subject: str,
        difficulty: str = "medium",
        count: int = 5,
        context: str = "",
    ) -> Dict:
        """
        Generate MCQ quiz questions for a topic.
        
        Args:
            topic: Topic to generate questions about
            subject: Subject/course name
            difficulty: Difficulty level (easy/medium/hard)
            count: Number of questions to generate
            context: Additional context from study materials
            
        Returns:
            Dict with generated quiz questions
        """
        # Try LLM generation
        try:
            result = self._llm_generate(topic, subject, difficulty, count, context)
            if result:
                return result
        except Exception as e:
            print(f"LLM quiz generation failed: {e}")

        # Fallback sample questions
        return self._generate_sample_quiz(topic, subject, difficulty, count)

    def _llm_generate(
        self,
        topic: str,
        subject: str,
        difficulty: str,
        count: int,
        context: str,
    ) -> Optional[Dict]:
        """Generate quiz using LLM."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage
            import json

            llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=0.7,
                api_key=settings.OPENAI_API_KEY,
            )

            prompt = QUIZ_GENERATION_PROMPT.format(
                topic=topic,
                subject=subject,
                difficulty=difficulty,
                count=count,
                context=context[:3000] if context else "No additional context provided.",
            )

            response = llm.invoke([HumanMessage(content=prompt)])
            result = json.loads(response.content)

            return {
                "topic": topic,
                "subject": subject,
                "difficulty": difficulty,
                "total_questions": len(result.get("questions", [])),
                "questions": result.get("questions", []),
                "generated_by": "llm",
            }

        except Exception:
            return None

    def _generate_sample_quiz(
        self,
        topic: str,
        subject: str,
        difficulty: str,
        count: int,
    ) -> Dict:
        """Generate sample quiz questions as fallback."""
        questions = []

        template_questions = {
            "easy": [
                {
                    "question": f"What is the basic definition of {topic}?",
                    "options": {
                        "A": f"A fundamental concept in {subject} that deals with {topic}",
                        "B": f"An advanced technique unrelated to {subject}",
                        "C": f"A deprecated method no longer used",
                        "D": f"A proprietary algorithm with limited applications",
                    },
                    "correct_answer": "A",
                    "explanation": f"{topic} is a core concept in {subject}.",
                },
                {
                    "question": f"Which of the following best describes {topic}?",
                    "options": {
                        "A": "None of the listed options",
                        "B": f"A key concept studied in {subject}",
                        "C": "An obsolete theory",
                        "D": "A hardware component",
                    },
                    "correct_answer": "B",
                    "explanation": f"{topic} is an important topic in {subject}.",
                },
            ],
            "medium": [
                {
                    "question": f"What is a practical application of {topic} in {subject}?",
                    "options": {
                        "A": "It has no practical applications",
                        "B": f"It is used to solve complex problems in {subject}",
                        "C": "It is only theoretical",
                        "D": "It is used exclusively in unrelated fields",
                    },
                    "correct_answer": "B",
                    "explanation": f"{topic} has numerous practical applications in {subject}.",
                },
            ],
            "hard": [
                {
                    "question": f"Analyze the trade-offs involved in applying {topic} to real-world {subject} problems.",
                    "options": {
                        "A": "There are no trade-offs",
                        "B": "Complexity vs. accuracy, scalability vs. performance",
                        "C": "Only financial considerations matter",
                        "D": "The topic has been fully optimized with no trade-offs",
                    },
                    "correct_answer": "B",
                    "explanation": f"Applying {topic} involves balancing multiple factors.",
                },
            ],
        }

        available = template_questions.get(difficulty, template_questions["medium"])
        for i in range(min(count, len(available))):
            q = available[i % len(available)].copy()
            q["difficulty"] = difficulty
            q["topic"] = topic
            questions.append(q)

        return {
            "topic": topic,
            "subject": subject,
            "difficulty": difficulty,
            "total_questions": len(questions),
            "questions": questions,
            "generated_by": "template",
        }

    def generate_adaptive_quiz(
        self,
        topics: List[Dict],
        subject: str,
        performance_data: Optional[Dict] = None,
        total_questions: int = 10,
    ) -> Dict:
        """
        Generate an adaptive quiz that adjusts difficulty based on performance.
        
        Args:
            topics: List of topics with priority info
            subject: Subject name
            performance_data: Previous quiz performance by topic
            total_questions: Total questions to generate
            
        Returns:
            Adaptive quiz with mixed difficulty levels
        """
        all_questions = []
        perf = performance_data or {}

        for topic_data in topics[:5]:
            topic = topic_data.get("topic", topic_data.get("name", ""))

            # Determine difficulty based on past performance
            mastery = perf.get(topic, {}).get("mastery_level", 50)
            if mastery < 30:
                difficulty = "easy"
            elif mastery < 70:
                difficulty = "medium"
            else:
                difficulty = "hard"

            questions_for_topic = max(1, total_questions // min(5, len(topics)))
            result = self.generate_quiz(topic, subject, difficulty, questions_for_topic)
            all_questions.extend(result.get("questions", []))

        return {
            "subject": subject,
            "quiz_type": "adaptive",
            "total_questions": len(all_questions),
            "questions": all_questions[:total_questions],
            "difficulty_distribution": {
                "easy": sum(1 for q in all_questions if q.get("difficulty") == "easy"),
                "medium": sum(1 for q in all_questions if q.get("difficulty") == "medium"),
                "hard": sum(1 for q in all_questions if q.get("difficulty") == "hard"),
            },
        }
