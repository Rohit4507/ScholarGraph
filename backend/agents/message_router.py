"""
ScholarGraph AI — Message Router Agent
Intelligently routes user messages to appropriate existing LangGraph agents.
Follows established agent patterns and integrates with current architecture.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from agents.document_classifier import DocumentClassifierAgent
from agents.concept_extractor import ConceptExtractionAgent
from agents.prediction_engine import PredictionEngineAgent
from agents.quiz_generator import QuizGeneratorAgent
from agents.study_strategist import StudyStrategyAgent
from agents.performance_analyzer import PerformanceAnalyzerAgent
from database.models import Document, TopicScore, QuizAttempt


class AgentType(Enum):
    """Enumeration of available agent types for routing."""
    DOCUMENT_ANALYSIS = "document_analysis"
    CONCEPT_EXTRACTION = "concept_extraction"
    PREDICTION = "prediction"
    QUIZ_GENERATION = "quiz_generation"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    STUDY_STRATEGY = "study_strategy"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    GENERAL_QA = "general_qa"
    PERSONAL_ASSISTANT = "personal_assistant"


@dataclass
class RouteDecision:
    """Decision data structure for message routing."""
    agent_type: AgentType
    confidence: float
    parameters: Dict
    dashboard_updates: Optional[Dict] = None
    reasoning: str = ""


class MessageRouter:
    """
    Intelligent message router that classifies user queries and routes them
    to the appropriate specialized agent in the existing LangGraph system.
    
    Integrates with all 8 existing agents without modifying their core logic.
    """

    def __init__(self):
        # Pattern matching for each agent type
        self.patterns = {
            AgentType.DOCUMENT_ANALYSIS: [
                r"analyze.*document",
                r"process.*pdf",
                r"extract.*topics",
                r"summarize.*syllabus",
                r"upload.*file",
                r"classify.*document",
                r"document.*type"
            ],
            AgentType.PREDICTION: [
                r"predict.*topic",
                r"probability.*exam",
                r"likely.*question",
                r"important.*topic",
                r"exam.*prediction",
                r"topic.*probability",
                r"chance.*appears"
            ],
            AgentType.QUIZ_GENERATION: [
                r"generate.*quiz",
                r"create.*question",
                r"test.*me",
                r"practice.*question",
                r"quiz.*topic",
                r"assessment",
                r"evaluate.*me"
            ],
            AgentType.KNOWLEDGE_GRAPH: [
                r"show.*graph",
                r"knowledge.*map",
                r"topic.*relationship",
                r"visualize.*connection",
                r"concept.*map",
                r"graph.*visualization"
            ],
            AgentType.STUDY_STRATEGY: [
                r"study.*plan",
                r"how.*study",
                r"study.*strategy",
                r"prepare.*exam",
                r"revision.*plan",
                r"study.*schedule"
            ],
            AgentType.PERFORMANCE_ANALYSIS: [
                r"my.*progress",
                r"performance.*stats",
                r"track.*mastery",
                r"my.*scores",
                r"how.*well.*doing",
                r"improvement.*areas"
            ],
            AgentType.PERSONAL_ASSISTANT: [
                r"remind.*me",
                r"schedule.*meeting",
                r"set.*reminder",
                r"calendar",
                r"appointment",
                r"meeting.*time"
            ],
            AgentType.GENERAL_QA: [
                r"what.*is",
                r"explain.*concept",
                r"help.*understand",
                r"define.*term",
                r"how.*does",
                r"why.*is",
                r"tell.*me.*about",
                r"describe.*",
                r"who.*is",
                r"when.*was",
                r"where.*is",
                r"can.*you.*explain",
                r"could.*you.*tell.*me",
                r"i.*want.*to.*know",
                r"what.*do.*you.*think",
                r"what.*are.*your.*thoughts"
            ]
        }

    async def route_message(
        self, 
        message: str, 
        context: List[Dict], 
        subject: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> RouteDecision:
        """
        Route a message to the appropriate agent based on content analysis.
        
        Args:
            message: User message to route
            context: Recent chat history for context
            subject: Current academic subject (if any)
            user_id: User ID for personalization
            
        Returns:
            RouteDecision with agent type and parameters
        """
        message_lower = message.lower()
        
        # Check each agent pattern with confidence scoring
        best_match = None
        best_confidence = 0.0
        
        for agent_type, patterns in self.patterns.items():
            confidence = self._calculate_pattern_confidence(message_lower, patterns)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = agent_type
        
        # Use best match or default to general QA
        selected_agent = best_match if best_confidence > 0.3 else AgentType.GENERAL_QA
        
        return self._create_route_decision(
            selected_agent, message, context, subject, user_id, best_confidence
        )

    def _calculate_pattern_confidence(self, message: str, patterns: List[str]) -> float:
        """Calculate confidence score for pattern matching."""
        confidence = 0.0
        total_patterns = len(patterns)
        
        for pattern in patterns:
            if re.search(pattern, message):
                confidence += 1.0 / total_patterns
        
        # Boost confidence for exact matches
        if confidence > 0:
            confidence *= 1.2  # 20% boost for any match
        
        return min(confidence, 1.0)

    def _create_route_decision(
        self, 
        agent_type: AgentType, 
        message: str, 
        context: List[Dict], 
        subject: Optional[str],
        user_id: Optional[str],
        confidence: float
    ) -> RouteDecision:
        """Create a route decision with parameters and dashboard updates."""
        
        parameters = {
            "message": message,
            "context": context,
            "subject": subject,
            "user_id": user_id,
            "timestamp": context[-1]["timestamp"] if context else None
        }
        
        dashboard_updates = self._determine_dashboard_updates(agent_type, subject)
        reasoning = self._generate_reasoning(agent_type, message, confidence)
        
        return RouteDecision(
            agent_type=agent_type,
            confidence=confidence,
            parameters=parameters,
            dashboard_updates=dashboard_updates,
            reasoning=reasoning
        )

    def _determine_dashboard_updates(self, agent_type: AgentType, subject: Optional[str]) -> Optional[Dict]:
        """Determine what dashboard widgets should be updated."""
        updates = {
            AgentType.PREDICTION: {
                "widget": "predictions",
                "action": "refresh",
                "subject": subject
            },
            AgentType.QUIZ_GENERATION: {
                "widget": "quiz_stats",
                "action": "update",
                "recent_quiz": True
            },
            AgentType.KNOWLEDGE_GRAPH: {
                "widget": "knowledge_graph",
                "action": "highlight_topics",
                "topics": self._extract_topics_from_context(subject)
            },
            AgentType.DOCUMENT_ANALYSIS: {
                "widget": "document_stats",
                "action": "increment",
                "document_processed": True
            },
            AgentType.PERFORMANCE_ANALYSIS: {
                "widget": "performance_metrics",
                "action": "refresh",
                "user_specific": True
            },
            AgentType.STUDY_STRATEGY: {
                "widget": "study_plan",
                "action": "update",
                "subject": subject
            }
        }
        
        return updates.get(agent_type)

    def _generate_reasoning(self, agent_type: AgentType, message: str, confidence: float) -> str:
        """Generate human-readable reasoning for the routing decision."""
        reasoning_map = {
            AgentType.DOCUMENT_ANALYSIS: "Document processing request detected",
            AgentType.PREDICTION: "Topic probability prediction requested",
            AgentType.QUIZ_GENERATION: "Quiz/assessment generation requested",
            AgentType.KNOWLEDGE_GRAPH: "Knowledge graph visualization requested",
            AgentType.STUDY_STRATEGY: "Study planning/strategy requested",
            AgentType.PERFORMANCE_ANALYSIS: "Performance tracking requested",
            AgentType.PERSONAL_ASSISTANT: "Personal assistant task detected",
            AgentType.GENERAL_QA: "General question/answer request"
        }
        
        base_reasoning = reasoning_map.get(agent_type, "General query")
        confidence_desc = "high" if confidence > 0.7 else "medium" if confidence > 0.4 else "low"
        
        return f"{base_reasoning} (confidence: {confidence_desc})"

    def _extract_topics_from_context(self, subject: Optional[str]) -> List[str]:
        """Extract relevant topics for dashboard highlighting."""
        if not subject:
            return []
        
        # Common academic topics by subject
        topic_map = {
            "machine learning": ["neural networks", "deep learning", "algorithms", "optimization"],
            "data structures": ["arrays", "trees", "graphs", "algorithms", "complexity"],
            "algorithms": ["sorting", "searching", "dynamic programming", "greedy"],
            "computer networks": ["tcp/ip", "routing", "protocols", "security"],
            "database systems": ["sql", "normalization", "indexing", "transactions"]
        }
        
        return topic_map.get(subject.lower(), [])

    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Return capabilities of each agent for UI display."""
        return {
            "document_analysis": [
                "Upload and process PDF documents",
                "Extract topics and concepts", 
                "Classify document types",
                "Generate summaries"
            ],
            "prediction": [
                "Predict exam topic probabilities",
                "Analyze question patterns",
                "Calculate importance scores",
                "Generate study priorities"
            ],
            "quiz_generation": [
                "Create adaptive quizzes",
                "Generate MCQ questions",
                "Adjust difficulty levels",
                "Provide explanations"
            ],
            "knowledge_graph": [
                "Visualize topic relationships",
                "Show concept dependencies",
                "Map knowledge connections",
                "Interactive exploration"
            ],
            "study_strategy": [
                "Generate personalized study plans",
                "Optimize study schedules",
                "Prioritize topics",
                "Track preparation progress"
            ],
            "performance_analysis": [
                "Track learning progress",
                "Analyze quiz performance",
                "Identify knowledge gaps",
                "Monitor mastery levels"
            ],
            "general_qa": [
                "Answer conceptual questions",
                "Explain academic topics",
                "Provide study guidance",
                "Clarify concepts"
            ],
            "personal_assistant": [
                "Set study reminders",
                "Schedule review sessions",
                "Manage study calendar",
                "Send notifications"
            ]
        }

    def get_supported_subjects(self) -> List[str]:
        """Return list of supported academic subjects."""
        return [
            "Machine Learning",
            "Data Structures",
            "Algorithms",
            "Computer Networks",
            "Database Systems",
            "Operating Systems",
            "Software Engineering",
            "Artificial Intelligence",
            "Web Development",
            "Mobile Development",
            "Computer Science Fundamentals",
            "Mathematics for CS"
        ]
