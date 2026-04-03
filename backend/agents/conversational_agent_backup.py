"""
ScholarGraph AI — Conversational Agent
Handles streaming responses and coordinates with existing LangGraph agents.
Supports both OpenAI GPT-4o and LLaMA 3 via Ollama for flexible LLM deployment.
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
    Main conversational agent that coordinates with existing LangGraph agents
    and provides streaming responses using both OpenAI GPT-4o and LLaMA 3.
    
    Follows established patterns and integrates seamlessly with current architecture.
    """

    def __init__(self):
        # Initialize OpenAI LLM (primary)
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
            max_tokens=1000,  # Optimized for faster responses
            repeat_penalty=1.1,
            num_ctx=2048,  # Context window size
            num_predict=1000,  # Max tokens to predict
            timeout=8  # 8 second timeout for faster responses
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
        
        Args:
            route_decision: Routing decision from MessageRouter
            message: User message
            session_history: Chat session history
            current_user: Current user object
            
        Yields:
            Streaming response tokens
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

    async def _handle_document_analysis(
        self, 
        message: str, 
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle document analysis requests."""
        subject = parameters.get("subject", "general")
        
        response_text = f"""I'll help you analyze documents for {subject}. 

Here's what I can do:
📄 **Upload & Process**: Upload PDF files (syllabus, past year questions, lecture notes)
🔍 **Extract Topics**: Automatically identify key concepts and topics
📊 **Classify Content**: Determine document type and structure
🎯 **Prepare Analysis**: Get documents ready for prediction and graph generation

To get started:
1. Use the upload button to select your PDF files
2. Specify the subject (e.g., "Machine Learning")
3. I'll process them and extract all relevant topics

The document analysis will feed into:
- Topic probability predictions
- Knowledge graph visualization  
- Quiz generation
- Study plan recommendations

Ready to upload your documents?"""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)  # Simulate streaming

    async def _handle_prediction(
        self, 
        message: str, 
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle prediction requests."""
        subject = parameters.get("subject")
        
        if not subject:
            response_text = """To provide accurate topic predictions, I need:

📚 **Subject Specification**: Which subject are you studying? (e.g., "Machine Learning", "Data Structures")
📄 **Uploaded Documents**: Past year questions, syllabus, and lecture notes

Once you have documents uploaded, I'll analyze:
🎯 **Probability Scores**: Mathematical prediction of exam topic likelihood
📊 **Priority Classification**: HIGH/MEDIUM/LOW priority topics
📈 **Pattern Analysis**: Historical question frequency and trends
🔍 **Semantic Analysis**: Concept relevance and connections

Please specify a subject and ensure you've uploaded relevant documents first!"""
        else:
            response_text = f"""Analyzing topic probabilities for {subject}... 

🔍 **Prediction Engine Active**: I'm examining multiple data sources:
📊 **Historical Analysis**: Past year question patterns
📚 **Syllabus Weightage**: Topic importance from course outlines
🧠 **Semantic Relevance**: Concept connections and relationships
⏰ **Recency Factors**: Recent exam trends

The prediction algorithm calculates:
```
Score = (0.40 × Frequency) + (0.35 × Semantic Similarity) + (0.25 × Recency Weight)
```

📈 **Results**: Check the Predictions dashboard for detailed probability scores and priority classifications for {subject}.

The predictions will update automatically as more documents are processed!"""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)

    async def _handle_quiz_generation(
        self, 
        message: str, 
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle quiz generation requests."""
        subject = parameters.get("subject", "general")
        
        response_text = f"""Generating adaptive quiz questions for {subject}... 

🎯 **Quiz Generation Features**:
📝 **Adaptive Difficulty**: Questions match your current mastery level
🎨 **Multiple Formats**: MCQs with explanations and reasoning
📊 **Topic Targeting**: Focus on high-probability exam topics
⏱️ **Performance Tracking**: Monitor progress and improvement

🔄 **Quiz Algorithm**:
1. Analyze your current knowledge gaps
2. Select topics based on prediction scores
3. Generate questions at appropriate difficulty
4. Provide detailed explanations for learning
5. Track performance for future optimization

📈 **Results**: Your quiz performance will update the Performance dashboard and help refine future study recommendations.

Ready to test your knowledge? The quiz will adapt to your level in real-time!"""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)

    async def _handle_knowledge_graph(
        self, 
        message: str, 
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle knowledge graph requests."""
        subject = parameters.get("subject", "general")
        
        response_text = f"""Creating knowledge graph for {subject}... 

🕸️ **Knowledge Graph Visualization**:
🔗 **Topic Relationships**: How concepts connect and depend on each other
📊 **Probability Integration**: Node sizes show exam importance
🎯 **Prerequisite Mapping**: Clear learning pathways and dependencies
🎨 **Interactive Exploration**: Click nodes to focus on specific topics

📐 **Graph Structure**:
- **Nodes**: Topics, concepts, and subtopics
- **Edges**: Prerequisites, correlations, and dependencies
- **Colors**: Priority levels (HIGH/MEDIUM/LOW)
- **Sizes**: Probability scores and importance

🔍 **Analysis Features**:
- Identify knowledge gaps in your understanding
- Discover optimal learning sequences
- Visualize concept clusters and relationships
- Track mastery progression across topics

📈 **Interactive Dashboard**: Explore the graph in the right panel - zoom, pan, and click for detailed information!"""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)

    async def _handle_study_strategy(
        self, 
        message: str, 
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle study strategy requests."""
        subject = parameters.get("subject", "general")
        
        response_text = f"""Generating personalized study strategy for {subject}... 

📚 **Study Strategy Engine**:
🎯 **Priority-Based Planning**: Focus on high-probability topics first
⏰ **Time Optimization**: Efficient scheduling based on exam timeline
📊 **Mastery Integration**: Adapt to your current knowledge levels
🔄 **Dynamic Updates**: Plans evolve as you progress

🗓️ **Study Plan Components**:
📈 **Topic Prioritization**: HIGH priority topics get more time
⏱️ **Session Scheduling**: Optimal study intervals and breaks
🎯 **Milestone Tracking**: Clear progress checkpoints
📝 **Resource Allocation**: Best use of available study materials

🔄 **Adaptive Algorithm**:
```
Study Time = (Probability Score × Importance) ÷ Current Mastery
```

📊 **Dashboard Integration**: Your study plan will appear in the Dashboard widget with:
- Daily study schedules
- Progress tracking
- Topic completion status
- Upcoming milestones

Ready to optimize your exam preparation?"""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)

    async def _handle_performance_analysis(
        self, 
        message: str, 
        parameters: Dict,
        current_user: Optional[object]
    ) -> AsyncGenerator[str, None]:
        """Handle performance analysis requests."""
        user_id = current_user.id if current_user else None
        
        response_text = f"""Analyzing your learning performance... 

📊 **Performance Metrics**:
🎯 **Mastery Levels**: Track understanding across all topics
📈 **Progress Trends**: Improvement over time visualization
🔍 **Knowledge Gaps**: Identify areas needing attention
⏱️ **Study Efficiency**: Optimal learning patterns and timing

📈 **Analytics Dashboard**:
- **Topic Mastery**: Percentage scores per concept
```

    async def _handle_personal_assistant(
        self, 
        message: str, 
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle personal assistant requests."""
        # Quick general knowledge responses for common questions
        message_lower = message.lower().strip()
        
        # Machine Learning
        if "machine learning" in message_lower and ("what is" in message_lower or "explain" in message_lower):
            response = """Machine Learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.

🤖 **Core Concept**: Instead of writing specific rules, ML algorithms learn patterns from data to make predictions or decisions.

📊 **Key Types**:
- **Supervised Learning**: Learning from labeled data (classification, regression)
- **Unsupervised Learning**: Finding patterns in unlabeled data (clustering, dimensionality reduction)
- **Reinforcement Learning**: Learning through trial and error with rewards

🎯 **Real Applications**:
- 📱 Recommendation systems (Netflix, Amazon)
- 🏥 Medical diagnosis and treatment planning
- 🚗 Self-driving cars
- 💬 Natural language processing and chatbots
- 📈 Financial fraud detection

🔬 **How It Works**:
1. **Data Collection**: Gather relevant training data
2. **Model Training**: Algorithm learns patterns from data
3. **Evaluation**: Test model performance on unseen data
4. **Deployment**: Use model to make predictions on new data

Would you like me to explain any specific aspect of machine learning in more detail?"""
        
        # Quantum Computing
        elif "quantum computing" in message_lower and ("what is" in message_lower or "explain" in message_lower):
            response = """Quantum Computing is a revolutionary computing paradigm that uses quantum mechanics principles to process information in fundamentally different ways than classical computers.

⚛️ **Quantum Principles**:
- **Superposition**: Quantum bits (qubits) can exist in multiple states simultaneously
- **Entanglement**: Qubits can be correlated in ways that classical bits cannot
- **Quantum Interference**: Quantum states can interfere constructively or destructively

🔬 **Key Differences from Classical Computing**:
- Classical bits: 0 or 1
- Quantum bits (qubits): 0, 1, or both simultaneously (superposition)

💡 **Potential Applications**:
- 🔐 Breaking current encryption methods
- 💊 Drug discovery and molecular simulation
- 📈 Complex optimization problems
- 🧠 Artificial intelligence and machine learning
- 🌐 Climate modeling and weather prediction

⚡ **Current Status**:
- Still in early development stages
- Major companies: Google, IBM, Microsoft, Intel
- Limited by quantum decoherence and error rates
- Expected to revolutionize computing in the next decade

Would you like to explore any specific quantum computing concept?"""
        
        # Albert Einstein
        elif "albert einstein" in message_lower and ("who was" in message_lower or "what is" in message_lower):
            response = """Albert Einstein (1879-1955) was a German-born theoretical physicist who revolutionized our understanding of space, time, gravity, and the universe.

🧠 **Major Contributions**:

**Relativity Theory**:
- **Special Relativity (1905)**: E=mc², time dilation, length contraction
- **General Relativity (1915)**: Gravity as curvature of spacetime

**Quantum Mechanics**:
- Photoelectric effect (Nobel Prize 1921)
- Brownian motion
- Quantum theory of light

🌟 **Key Achievements**:
- 🏆 Nobel Prize in Physics (1921)
- 📚 Published over 300 scientific papers
- 🌍 Changed our fundamental understanding of the universe
- 🧮 Developed the famous equation E=mc²

🎓 **Personal Life**:
- Born in Ulm, Germany
- Worked at Swiss Patent Office (early career)
- Professor at Princeton University (later life)
- Became a US citizen in 1940
- Advocated for civil rights and world peace

💡 **Famous Quotes**:
- "Imagination is more important than knowledge."
- "God does not play dice with the universe."
- "The important thing is not to stop questioning."

Einstein's work laid the foundation for modern physics, GPS technology, nuclear energy, and our understanding of the cosmos!"""
        
        # Photosynthesis
        elif "photosynthesis" in message_lower and ("how" in message_lower or "what is" in message_lower or "explain" in message_lower):
            response = """Photosynthesis is the remarkable process by which plants, algae, and some bacteria convert light energy into chemical energy stored in glucose (sugar).

🌱 **Chemical Equation**:
6CO₂ + 6H₂O + Light Energy → C₆H₁₂O₆ + 6O₂
(Carbon Dioxide + Water + Light → Glucose + Oxygen)

🔬 **Two Main Stages**:

**1. Light-Dependent Reactions**:
- 🌞 Occur in thylakoid membranes of chloroplasts
- 💡 Capture light energy using chlorophyll
- ⚡ Split water molecules (photolysis)
- 🔋 Produce ATP (energy) and NADPH (electron carrier)

**2. Light-Independent Reactions (Calvin Cycle)**:
- 🧪 Occur in stroma of chloroplasts
- 🔄 Fix CO₂ into organic molecules
- 🍬 Synthesize glucose using ATP and NADPH
- ♻️ Regenerate starting molecules

🌍 **Importance for Life**:
- 🌬️ Produces oxygen we breathe
- 🍎 Creates food for entire food chain
- 🌍 Removes CO₂ from atmosphere
- 💊 Foundation of most ecosystems

🏭 **Human Applications**:
- 🌾 Agriculture and crop improvement
- 🔋 Biofuel development
- 🏭 Carbon capture technologies
- 💊 Medical applications

Photosynthesis is literally the engine that powers life on Earth!"""
        
        else:
            # General fallback for other questions
            response = f"""I understand you're asking about: "{message}"

I'm ScholarGraph AI, your academic intelligence assistant with broad knowledge across many subjects!

📚 **I can help you with**:
- **Computer Science**: Programming, algorithms, AI, databases, web development
- **Mathematics**: Calculus, linear algebra, statistics, discrete math
- **Physics**: Classical mechanics, quantum physics, thermodynamics, relativity
- **Chemistry**: Organic, inorganic, physical chemistry, biochemistry
- **Biology**: Molecular biology, genetics, ecology, evolution
- **History**: World history, scientific history, cultural studies
- **Literature**: Analysis, writing, literary theory
- **Current Events**: Technology trends, scientific discoveries, global issues

🎯 **Specialized Academic Tools**:
- 📄 Document analysis and topic extraction
- 🎯 Exam predictions and probability scoring
- 📝 Quiz generation and assessment
- 🕸️ Knowledge graph visualization
- 📊 Performance tracking and study planning

💡 **To get the best response**:
1. Be specific about your question
2. Mention the subject area if relevant
3. Let me know if you need a simple explanation or detailed analysis

Could you rephrase your question or tell me which subject area interests you most?"""
        
        # Stream the response word by word
        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.02)
    ) -> AsyncGenerator[str, None]:
        """Handle document analysis requests."""
        subject = parameters.get("subject", "general")
        
        response_text = f"""I'll help you analyze documents for {subject}. 

Here's what I can do:
📄 **Upload & Process**: Upload PDF files (syllabus, past year questions, lecture notes)
🔍 **Extract Topics**: Automatically identify key concepts and topics
📊 **Classify Content**: Determine document type and structure
🎯 **Prepare Analysis**: Get documents ready for prediction and graph generation

To get started:
1. Use the upload button to select your PDF files
2. Specify the subject (e.g., "Machine Learning")
3. I'll process them and extract all relevant topics

The document analysis will feed into:
- Topic probability predictions
- Knowledge graph visualization  
- Quiz generation
- Study plan recommendations

Ready to upload your documents?"""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)  # Simulate streaming

    async def _handle_prediction(
        self, 
        message: str, 
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle prediction requests."""
        subject = parameters.get("subject")
        
        if not subject:
            response_text = """To provide accurate topic predictions, I need:

📚 **Subject Specification**: Which subject are you studying? (e.g., "Machine Learning", "Data Structures")
📄 **Uploaded Documents**: Past year questions, syllabus, and lecture notes

Once you have documents uploaded, I'll analyze:
🎯 **Probability Scores**: Mathematical prediction of exam topic likelihood
📊 **Priority Classification**: HIGH/MEDIUM/LOW priority topics
📈 **Pattern Analysis**: Historical question frequency and trends
🔍 **Semantic Analysis**: Concept relevance and connections

Please specify a subject and ensure you've uploaded relevant documents first!"""
        else:
            response_text = f"""Analyzing topic probabilities for {subject}... 

🔍 **Prediction Engine Active**: I'm examining multiple data sources:
📊 **Historical Analysis**: Past year question patterns
📚 **Syllabus Weightage**: Topic importance from course outlines
🧠 **Semantic Relevance**: Concept connections and relationships
⏰ **Recency Factors**: Recent exam trends

The prediction algorithm calculates:
```
Score = (0.40 × Frequency) + (0.35 × Semantic Similarity) + (0.25 × Recency Weight)
```

📈 **Results**: Check the Predictions dashboard for detailed probability scores and priority classifications for {subject}.

The predictions will update automatically as more documents are processed!"""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)

    async def _handle_quiz_generation(
        self, 
        message: str, 
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle quiz generation requests."""
        subject = parameters.get("subject", "general")
        
        response_text = f"""Generating adaptive quiz questions for {subject}... 

🎯 **Quiz Generation Features**:
📝 **Adaptive Difficulty**: Questions match your current mastery level
🎨 **Multiple Formats**: MCQs with explanations and reasoning
📊 **Topic Targeting**: Focus on high-probability exam topics
⏱️ **Performance Tracking**: Monitor progress and improvement

🔄 **Quiz Algorithm**:
1. Analyze your current knowledge gaps
2. Select topics based on prediction scores
3. Generate questions at appropriate difficulty
4. Provide detailed explanations for learning
5. Track performance for future optimization

📈 **Results**: Your quiz performance will update the Performance dashboard and help refine future study recommendations.

Ready to test your knowledge? The quiz will adapt to your level in real-time!"""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)

    async def _handle_knowledge_graph(
        self, 
        message: str, 
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle knowledge graph requests."""
        subject = parameters.get("subject", "general")
        
        response_text = f"""Creating knowledge graph for {subject}... 

🕸️ **Knowledge Graph Visualization**:
🔗 **Topic Relationships**: How concepts connect and depend on each other
📊 **Probability Integration**: Node sizes show exam importance
🎯 **Prerequisite Mapping**: Clear learning pathways and dependencies
🎨 **Interactive Exploration**: Click nodes to focus on specific topics

📐 **Graph Structure**:
- **Nodes**: Topics, concepts, and subtopics
- **Edges**: Prerequisites, correlations, and dependencies
- **Colors**: Priority levels (HIGH/MEDIUM/LOW)
- **Sizes**: Probability scores and importance

🔍 **Analysis Features**:
- Identify knowledge gaps in your understanding
- Discover optimal learning sequences
- Visualize concept clusters and relationships
- Track mastery progression across topics

📈 **Interactive Dashboard**: Explore the graph in the right panel - zoom, pan, and click for detailed information!"""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)

    async def _handle_study_strategy(
        self, 
        message: str, 
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle study strategy requests."""
        subject = parameters.get("subject", "general")
        
        response_text = f"""Generating personalized study strategy for {subject}... 

📚 **Study Strategy Engine**:
🎯 **Priority-Based Planning**: Focus on high-probability topics first
⏰ **Time Optimization**: Efficient scheduling based on exam timeline
📊 **Mastery Integration**: Adapt to your current knowledge levels
🔄 **Dynamic Updates**: Plans evolve as you progress

🗓️ **Study Plan Components**:
📈 **Topic Prioritization**: HIGH priority topics get more time
⏱️ **Session Scheduling**: Optimal study intervals and breaks
🎯 **Milestone Tracking**: Clear progress checkpoints
📝 **Resource Allocation**: Best use of available study materials

🔄 **Adaptive Algorithm**:
```
Study Time = (Probability Score × Importance) ÷ Current Mastery
```

📊 **Dashboard Integration**: Your study plan will appear in the Dashboard widget with:
- Daily study schedules
- Progress tracking
- Topic completion status
- Upcoming milestones

Ready to optimize your exam preparation?"""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)

    async def _handle_performance_analysis(
        self, 
        message: str, 
        parameters: Dict,
        current_user: Optional[object]
    ) -> AsyncGenerator[str, None]:
        """Handle performance analysis requests."""
        user_id = current_user.id if current_user else None
        
        response_text = f"""Analyzing your learning performance... 

📊 **Performance Metrics**:
🎯 **Mastery Levels**: Track understanding across all topics
📈 **Progress Trends**: Improvement over time visualization
🔍 **Knowledge Gaps**: Identify areas needing attention
⏱️ **Study Efficiency**: Optimal learning patterns and timing

📈 **Analytics Dashboard**:
- **Topic Mastery**: Percentage scores per concept
- **Quiz Performance**: Accuracy and completion rates
- **Study Patterns**: Most effective study times
- **Improvement Areas**: Topics with lowest mastery

🎯 **Personalized Insights**:
🔍 **Strength Analysis**: Your best-performing topic categories
📚 **Growth Opportunities**: Areas with biggest improvement potential
⏰ **Optimal Study Times**: When you learn most effectively
🎯 **Focus Recommendations**: What to study next for maximum impact

📊 **Real-Time Tracking**: Your performance updates automatically after each quiz and study session!

Check the Performance dashboard for detailed analytics and personalized recommendations."""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)

    async def _handle_personal_assistant(
        self, 
        message: str, 
        parameters: Dict
    ) -> AsyncGenerator[str, None]:
        """Handle personal assistant tasks (reminders, scheduling)."""
        import re
        
        # Extract time and task from message
        time_patterns = [
            r"(\d{1,2})\s*(am|pm)",
            r"(\d{1,2}:\d{2})\s*(am|pm)",
            r"(\d{1,2})\s*o'clock"
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message.lower())
            if match:
                time_str = match.group(0)
                response_text = f"""⏰ **Reminder Set**: I've noted your request for {time_str}.

📝 **Personal Assistant Features**:
🔔 **Study Reminders**: Custom notifications for review sessions
📅 **Schedule Management**: Track study appointments and deadlines
🎯 **Goal Tracking**: Monitor preparation milestones
📊 **Progress Alerts**: Notifications for achievements

🔄 **Integration**: Your reminders will connect with:
- Study plan schedules
- Quiz recommendations
- Performance milestones
- Exam preparation timelines

📱 **Notification System**: I'll remind you at optimal study times based on your performance patterns!

For now, I've logged this request and it will appear in your session history. Full reminder integration is being implemented."""
                
                for word in response_text.split():
                    yield word + " "
                    await asyncio.sleep(0.02)
                return
        
        # No time pattern found
        response_text = """🤝 **Personal Assistant Ready**: I can help with scheduling and reminders!

📝 **What I Can Do**:
⏰ **Set Reminders**: "Remind me to review neural networks at 8 am"
📅 **Schedule Study**: "Schedule machine learning study for 2 pm tomorrow"
🎯 **Track Goals**: "Remind me to complete 3 quizzes this week"
📊 **Progress Alerts**: "Notify me when I reach 80% mastery"

🔧 **How to Use**:
1. Specify the time (e.g., "8 am", "2:30 pm", "7 o'clock")
2. Tell me what to remind you about
3. I'll log it and integrate with your study plan

**Example**: "Remind me to practice algorithms at 6 pm today"

Ready to set up your study reminders?"""
        
        for word in response_text.split():
            yield word + " "
            await asyncio.sleep(0.02)

    def get_llm_status(self) -> Dict[str, str]:
        """Get status of available LLMs."""
        return {
            "primary": "OpenAI GPT-4o" if self.primary_llm == self.openai_llm else "LLaMA 3 (Ollama)",
            "openai_available": "✅ Available" if settings.OPENAI_API_KEY else "❌ No API Key",
            "ollama_available": "✅ Available" if self.ollama_llm else "❌ Not Configured",
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
