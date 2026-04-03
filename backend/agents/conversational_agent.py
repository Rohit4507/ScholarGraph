"""
ScholarGraph AI — Optimized Conversational Agent
Hybrid LLaMA + OpenAI system for fast ChatGPT-like responses.
"""

import asyncio
import time
from typing import AsyncGenerator, Dict, List, Optional, Union
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from agents.message_router import RouteDecision, AgentType
from agents.document_classifier import DocumentClassifierAgent
from agents.concept_extractor import ConceptExtractionAgent
from agents.prediction_engine import PredictionEngineAgent
from agents.quiz_generator import QuizGeneratorAgent
from agents.study_strategist import StudyStrategyAgent
from agents.performance_analyzer import PerformanceAnalyzerAgent
from config import get_settings
from database.session import get_db
from database.models import Document, TopicScore, QuizAttempt, User

settings = get_settings()


class ConversationalAgent:
    """
    Optimized conversational agent that prefers LLaMA for fast responses
    with OpenAI fallback for complex reasoning tasks.
    """

    def __init__(self):
        # Initialize OpenAI LLM (fallback)
        self.openai_llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.7,
            streaming=True,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize LLaMA 3 via Ollama (optimized for performance)
        self.ollama_llm = ChatOllama(
            model="llama3.1:8b",  # Use your specific LLaMA model
            base_url="http://localhost:11434",
            temperature=0.7,
            streaming=True,
            top_p=0.9,
            max_tokens=800,  # Optimized for faster responses
            repeat_penalty=1.1,
            num_ctx=2048,  # Context window size
            num_predict=800,  # Max tokens to predict
            timeout=6  # 6 second timeout for faster responses
        )
        
        # Initialize existing agents (reuse current architecture)
        self.document_agent = DocumentClassifierAgent()
        self.prediction_agent = PredictionEngineAgent()
        self.quiz_agent = QuizGeneratorAgent()
        self.concept_agent = ConceptExtractionAgent()
        self.study_agent = StudyStrategyAgent()
        self.performance_agent = PerformanceAnalyzerAgent()
        
        # Choose primary LLM based on availability
        self.primary_llm = self._choose_primary_llm()

    def _choose_primary_llm(self):
        """Choose primary LLM based on configuration and performance optimization."""
        # Prefer LLaMA for fast responses, OpenAI as fallback
        try:
            # Test Ollama connection and available models
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get('models', [])
                llama_models = [m for m in models if 'llama' in m.get('name', '').lower()]
                if llama_models:
                    print(f"✅ Using LLaMA models: {[m['name'] for m in llama_models]}")
                    return self.ollama_llm
        except Exception as e:
            print(f"Ollama check failed: {e}")
        
        # Fallback to OpenAI if LLaMA not available
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.startswith("sk-"):
            print("🔄 LLaMA not available, using OpenAI fallback")
            return self.openai_llm
        
        # Last resort
        return self.ollama_llm

    async def get_streaming_response(
        self,
        route_decision: RouteDecision,
        message: str,
        session_history: List[Dict],
        current_user: Optional[object] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response based on route decision.
        Routes to appropriate agent or handles general conversation.
        """
        start_time = time.time()
        agent_type = route_decision.agent_type
        
        try:
            if agent_type == AgentType.DOCUMENT_ANALYSIS:
                async for token in self._handle_document_analysis(
                    message, route_decision.parameters
                ):
                    yield token
                    
            elif agent_type == AgentType.PREDICTION:
                async for token in self._handle_prediction(
                    message, route_decision.parameters
                ):
                    yield token
                    
            elif agent_type == AgentType.QUIZ_GENERATION:
                async for token in self._handle_quiz_generation(
                    message, route_decision.parameters
                ):
                    yield token
                    
            elif agent_type == AgentType.KNOWLEDGE_GRAPH:
                async for token in self._handle_knowledge_graph(
                    message, route_decision.parameters
                ):
                    yield token
                    
            elif agent_type == AgentType.STUDY_STRATEGY:
                async for token in self._handle_study_strategy(
                    message, route_decision.parameters
                ):
                    yield token
                    
            elif agent_type == AgentType.PERFORMANCE_ANALYSIS:
                async for token in self._handle_performance_analysis(
                    message, route_decision.parameters, current_user
                ):
                    yield token
                    
            elif agent_type == AgentType.PERSONAL_ASSISTANT:
                async for token in self._handle_personal_assistant(
                    message, route_decision.parameters
                ):
                    yield token
                    
            else:  # GENERAL_QA
                async for token in self._handle_general_qa(
                    message, session_history, route_decision.parameters
                ):
                    yield token
                    
        except Exception as e:
            yield f"Error: {str(e)}"

    async def _handle_general_qa(
        self, 
        message: str, 
        session_history: List[Dict],
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle general Q&A with optimized LLaMA responses."""
        
        # Stream response from primary LLM (now LLaMA-optimized)
        try:
            # Build conversation context for LLaMA
            context_messages = []
            
            # Add system prompt optimized for LLaMA
            system_prompt = """You are ScholarGraph AI, a helpful academic assistant. Answer clearly and concisely.

You can help with:
- Science: Physics, Chemistry, Biology, Computer Science
- Math: Algebra, Calculus, Statistics
- Humanities: History, Literature, Philosophy
- Current events and general knowledge

Be direct, accurate, and helpful. Keep responses under 200 words when possible."""
            
            context_messages.append(SystemMessage(content=system_prompt))
            
            # Add recent history (last 3 messages for LLaMA efficiency)
            for msg in session_history[-3:]:
                if msg["role"] == "user":
                    context_messages.append(HumanMessage(content=msg["content"]))
                else:
                    context_messages.append(AIMessage(content=msg["content"]))
            
            # Add current message
            context_messages.append(HumanMessage(content=message))
            
            # Stream from LLaMA with optimized settings
            async for chunk in self.primary_llm.astream(context_messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                elif isinstance(chunk, str):
                    yield chunk
                    
        except Exception as e:
            print(f"LLaMA error: {e}")
            # Fallback to OpenAI if LLaMA fails
            try:
                async for chunk in self.openai_llm.astream(context_messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        yield chunk.content
                    elif isinstance(chunk, str):
                        yield chunk
            except Exception as openai_error:
                print(f"OpenAI fallback error: {openai_error}")
                # Simple fallback response
                yield f"I'm having trouble connecting right now. Please try again or rephrase your question."

    def get_llm_status(self) -> Dict[str, str]:
        """Get status of available LLMs."""
        primary = "LLaMA 3.1" if self.primary_llm == self.ollama_llm else "OpenAI GPT-4o"
        return {
            "primary": primary,
            "openai_available": "✅ Available" if settings.OPENAI_API_KEY else "❌ No API Key",
            "ollama_available": "✅ Available" if self.primary_llm == self.ollama_llm else "❌ Not Active",
            "fallback_enabled": "✅ Yes"
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
            "Mobile Development"
        ]
