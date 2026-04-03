"""
ScholarGraph AI — LangGraph Multi-Agent Workflow Orchestrator
Connects all 8 specialized agents in a DAG workflow using LangGraph's StateGraph.

Workflow:
  Document Upload → [Agent 1: Classify] → [Agent 2: Extract Concepts]
  → [Agent 3: Semantic Map] → [Agent 4: Pattern Analysis]
  → [Agent 5: Prediction] → [Agent 6: Study Plan]
  → [Agent 7: Quiz Generation] → [Agent 8: Performance Analysis]
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime


# ── State Schema ─────────────────────────────────────────────────
class ScholarGraphState(TypedDict):
    """Shared state flowing through the agent graph."""
    # Input
    document_text: str
    doc_type: str
    subject: str
    tenant_id: str
    user_id: str
    
    # Agent 1 output
    classification: Dict
    
    # Agent 2 output
    concepts: Dict
    topics: List[str]
    
    # Agent 3 output
    semantic_mappings: List[Dict]
    
    # Agent 4 output
    patterns: Dict
    exam_data: List[Dict]
    
    # Agent 5 output
    predictions: List[Dict]
    
    # Agent 6 output
    study_plan: Dict
    
    # Agent 7 output
    quiz: Dict
    
    # Agent 8 output
    performance: Dict
    
    # Metadata
    errors: List[str]
    timestamp: str


class AgentGraph:
    """
    LangGraph-based workflow orchestrator for ScholarGraph AI.
    
    Implements a directed acyclic graph (DAG) connecting 8 specialized agents.
    Each agent processes its slice of the state and passes results downstream.
    """

    def __init__(self):
        """Initialize all agents."""
        from agents.document_classifier import DocumentClassifierAgent
        from agents.concept_extractor import ConceptExtractionAgent
        from agents.semantic_mapper import SemanticMapperAgent
        from agents.pattern_analyzer import PatternAnalyzerAgent
        from agents.prediction_engine import PredictionEngineAgent
        from agents.study_strategist import StudyStrategyAgent
        from agents.quiz_generator import QuizGeneratorAgent
        from agents.performance_analyzer import PerformanceAnalyzerAgent

        self.classifier = DocumentClassifierAgent()
        self.extractor = ConceptExtractionAgent()
        self.mapper = SemanticMapperAgent()
        self.pattern_analyzer = PatternAnalyzerAgent()
        self.predictor = PredictionEngineAgent()
        self.strategist = StudyStrategyAgent()
        self.quiz_gen = QuizGeneratorAgent()
        self.perf_analyzer = PerformanceAnalyzerAgent()

    def build_graph(self):
        """
        Build the LangGraph StateGraph.
        
        Returns a compiled graph ready for execution.
        """
        try:
            from langgraph.graph import StateGraph, END

            workflow = StateGraph(ScholarGraphState)

            # Add agent nodes
            workflow.add_node("classify", self._classify_node)
            workflow.add_node("extract_concepts", self._extract_concepts_node)
            workflow.add_node("semantic_map", self._semantic_map_node)
            workflow.add_node("analyze_patterns", self._analyze_patterns_node)
            workflow.add_node("predict", self._predict_node)
            workflow.add_node("study_plan", self._study_plan_node)
            workflow.add_node("generate_quiz", self._generate_quiz_node)
            workflow.add_node("analyze_performance", self._analyze_performance_node)

            # Define edges (DAG flow)
            workflow.set_entry_point("classify")
            workflow.add_edge("classify", "extract_concepts")
            workflow.add_edge("extract_concepts", "semantic_map")
            workflow.add_edge("semantic_map", "analyze_patterns")
            workflow.add_edge("analyze_patterns", "predict")
            workflow.add_edge("predict", "study_plan")
            workflow.add_edge("study_plan", "generate_quiz")
            workflow.add_edge("generate_quiz", "analyze_performance")
            workflow.add_edge("analyze_performance", END)

            return workflow.compile()

        except ImportError:
            print("⚠️ LangGraph not installed. Using sequential fallback.")
            return None

    def run(
        self,
        document_text: str,
        subject: str = "",
        doc_type: str = "",
        tenant_id: str = "",
        user_id: str = "",
        exam_data: Optional[List[Dict]] = None,
        quiz_results: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Execute the full agent pipeline.
        
        Args:
            document_text: Extracted document text
            subject: Subject/course name
            doc_type: Pre-classified document type (optional)
            tenant_id: Tenant ID for multi-tenancy
            user_id: User ID
            exam_data: Historical exam data (optional)
            quiz_results: Previous quiz results for performance analysis
            
        Returns:
            Complete analysis results from all agents
        """
        initial_state = {
            "document_text": document_text,
            "doc_type": doc_type,
            "subject": subject,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "classification": {},
            "concepts": {},
            "topics": [],
            "semantic_mappings": [],
            "patterns": {},
            "exam_data": exam_data or [],
            "predictions": [],
            "study_plan": {},
            "quiz": {},
            "performance": {},
            "errors": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Try LangGraph execution
        graph = self.build_graph()
        if graph:
            try:
                result = graph.invoke(initial_state)
                return result
            except Exception as e:
                print(f"LangGraph execution failed: {e}")
                initial_state["errors"].append(f"LangGraph error: {str(e)}")

        # Fallback: sequential execution
        return self._sequential_run(initial_state, quiz_results)

    def _sequential_run(
        self, state: Dict, quiz_results: Optional[List[Dict]] = None
    ) -> Dict:
        """Fallback sequential execution without LangGraph."""
        state = self._classify_node(state)
        state = self._extract_concepts_node(state)
        state = self._semantic_map_node(state)
        state = self._analyze_patterns_node(state)
        state = self._predict_node(state)
        state = self._study_plan_node(state)
        state = self._generate_quiz_node(state)
        
        if quiz_results:
            state["_quiz_results"] = quiz_results
        state = self._analyze_performance_node(state)
        
        return state

    # ── Agent Node Functions ────────────────────────────────────
    def _classify_node(self, state: Dict) -> Dict:
        """Agent 1: Document Classification."""
        try:
            if not state.get("doc_type"):
                result = self.classifier.classify(state["document_text"])
                state["classification"] = result
                state["doc_type"] = result.get("doc_type", "unknown")
            else:
                state["classification"] = {
                    "doc_type": state["doc_type"],
                    "confidence": 1.0,
                    "reasoning": "Pre-classified by user",
                    "method": "user_provided",
                }
        except Exception as e:
            state["errors"].append(f"Classification error: {str(e)}")
        return state

    def _extract_concepts_node(self, state: Dict) -> Dict:
        """Agent 2: Concept Extraction."""
        try:
            result = self.extractor.extract(
                state["document_text"], state.get("subject", "")
            )
            state["concepts"] = result
            state["topics"] = [
                t["name"] for t in result.get("topics", [])
            ]
        except Exception as e:
            state["errors"].append(f"Concept extraction error: {str(e)}")
        return state

    def _semantic_map_node(self, state: Dict) -> Dict:
        """Agent 3: Semantic Mapping."""
        try:
            if state.get("topics"):
                # Map topics to document chunks
                chunks = [
                    state["document_text"][i:i+500]
                    for i in range(0, min(len(state["document_text"]), 5000), 500)
                ]
                mappings = self.mapper.map_topics_to_notes(
                    state["topics"][:10], chunks
                )
                state["semantic_mappings"] = mappings
        except Exception as e:
            state["errors"].append(f"Semantic mapping error: {str(e)}")
        return state

    def _analyze_patterns_node(self, state: Dict) -> Dict:
        """Agent 4: Pattern Analysis."""
        try:
            if state.get("exam_data"):
                result = self.pattern_analyzer.analyze_patterns(
                    state["exam_data"], state.get("topics", [])
                )
                state["patterns"] = result
        except Exception as e:
            state["errors"].append(f"Pattern analysis error: {str(e)}")
        return state

    def _predict_node(self, state: Dict) -> Dict:
        """Agent 5: Probability Prediction."""
        try:
            if state.get("topics"):
                result = self.predictor.predict_with_context(
                    state["topics"],
                    state.get("subject", ""),
                    state.get("exam_data", []),
                    state.get("tenant_id", ""),
                )
                state["predictions"] = result.get("predictions", [])
        except Exception as e:
            state["errors"].append(f"Prediction error: {str(e)}")
        return state

    def _study_plan_node(self, state: Dict) -> Dict:
        """Agent 6: Study Plan Generation."""
        try:
            if state.get("predictions"):
                plan = self.strategist.generate_plan(
                    state["predictions"],
                    state.get("subject", ""),
                    days_until_exam=30,
                )
                state["study_plan"] = plan
        except Exception as e:
            state["errors"].append(f"Study plan error: {str(e)}")
        return state

    def _generate_quiz_node(self, state: Dict) -> Dict:
        """Agent 7: Quiz Generation."""
        try:
            if state.get("predictions"):
                quiz = self.quiz_gen.generate_adaptive_quiz(
                    state["predictions"][:5],
                    state.get("subject", ""),
                    total_questions=10,
                )
                state["quiz"] = quiz
        except Exception as e:
            state["errors"].append(f"Quiz generation error: {str(e)}")
        return state

    def _analyze_performance_node(self, state: Dict) -> Dict:
        """Agent 8: Performance Analysis."""
        try:
            quiz_results = state.get("_quiz_results", [])
            if state.get("predictions"):
                result = self.perf_analyzer.analyze_performance(
                    quiz_results, state["predictions"]
                )
                state["performance"] = result
        except Exception as e:
            state["errors"].append(f"Performance analysis error: {str(e)}")
        return state
