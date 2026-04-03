"""
ScholarGraph AI — Database ORM Models
All SQLAlchemy models for the application: Users, Tenants, Documents,
Topics, Quizzes, StudyPlans, and Performance tracking.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


# ── Tenant (University / Institution) ───────────────────────────
class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, unique=True)
    domain = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant")
    documents = relationship("Document", back_populates="tenant")


# ── User ────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="student")  # student, professor, admin
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")
    documents = relationship("Document", back_populates="uploaded_by_user")
    quiz_attempts = relationship("QuizAttempt", back_populates="user")
    performance_records = relationship("PerformanceRecord", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")


# ── Document ────────────────────────────────────────────────────
class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String(500), nullable=False)
    original_name = Column(String(500), nullable=False)
    doc_type = Column(String(50), nullable=False)  # syllabus, pyq, lecture_notes
    subject = Column(String(255), nullable=True)
    semester = Column(String(50), nullable=True)
    year = Column(Integer, nullable=True)
    file_path = Column(String(1000), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    extracted_text = Column(Text, nullable=True)
    chunk_count = Column(Integer, default=0)
    tenant_id = Column(String, ForeignKey("tenants.id"), nullable=True)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="documents")
    uploaded_by_user = relationship("User", back_populates="documents")
    topics = relationship("TopicScore", back_populates="document")


# ── Topic Probability Score ─────────────────────────────────────
class TopicScore(Base):
    __tablename__ = "topic_scores"

    id = Column(String, primary_key=True, default=generate_uuid)
    topic_name = Column(String(500), nullable=False, index=True)
    subject = Column(String(255), nullable=False, index=True)
    probability_score = Column(Float, default=0.0)
    frequency_score = Column(Float, default=0.0)
    semantic_score = Column(Float, default=0.0)
    recency_score = Column(Float, default=0.0)
    priority = Column(String(20), default="LOW")  # HIGH, MEDIUM, LOW
    exam_years_appeared = Column(JSON, default=list)
    difficulty_level = Column(String(20), default="medium")  # easy, medium, hard
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    tenant_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    document = relationship("Document", back_populates="topics")


# ── Knowledge Graph Node ────────────────────────────────────────
class GraphNode(Base):
    __tablename__ = "graph_nodes"

    id = Column(String, primary_key=True, default=generate_uuid)
    topic_name = Column(String(500), nullable=False)
    subject = Column(String(255), nullable=False)
    node_type = Column(String(50), default="concept")  # topic, concept, subtopic
    probability_score = Column(Float, default=0.0)
    difficulty_level = Column(String(20), default="medium")
    mastery_score = Column(Float, default=0.0)
    node_metadata = Column("metadata", JSON, default=dict)  # "metadata" reserved by SQLAlchemy
    tenant_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Knowledge Graph Edge ────────────────────────────────────────
class GraphEdge(Base):
    __tablename__ = "graph_edges"

    id = Column(String, primary_key=True, default=generate_uuid)
    source_node_id = Column(String, ForeignKey("graph_nodes.id"), nullable=False)
    target_node_id = Column(String, ForeignKey("graph_nodes.id"), nullable=False)
    relationship_type = Column(String(50), default="correlation")  # prerequisite, correlation, dependency
    weight = Column(Float, default=1.0)
    subject = Column(String(255), nullable=True)
    tenant_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Quiz Question ───────────────────────────────────────────────
class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(String, primary_key=True, default=generate_uuid)
    topic = Column(String(500), nullable=False)
    subject = Column(String(255), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer = Column(String(10), nullable=False)
    explanation = Column(Text, nullable=True)
    difficulty = Column(String(20), default="medium")  # easy, medium, hard
    question_type = Column(String(50), default="mcq")  # mcq, true_false, short_answer
    tenant_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ── Quiz Attempt ────────────────────────────────────────────────
class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    score_percentage = Column(Float, default=0.0)
    time_taken_seconds = Column(Integer, default=0)
    answers = Column(JSON, default=dict)  # {question_id: selected_answer}
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="quiz_attempts")


# ── Performance Record ──────────────────────────────────────────
class PerformanceRecord(Base):
    __tablename__ = "performance_records"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    topic = Column(String(500), nullable=False)
    mastery_level = Column(Float, default=0.0)  # 0-100
    attempts_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    last_practiced = Column(DateTime, default=datetime.utcnow)
    strength = Column(String(20), default="weak")  # weak, developing, strong, mastered
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="performance_records")


# ── Study Plan ──────────────────────────────────────────────────
class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    plan_data = Column(JSON, nullable=False)  # Structured study plan
    total_hours = Column(Float, default=0.0)
    days_until_exam = Column(Integer, default=30)
    priority_topics = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ── Chat Session ───────────────────────────────────────────────────
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Optional for anonymous sessions
    session_name = Column(String(255), nullable=True)  # User-friendly name
    subject = Column(String(255), nullable=True)  # Current academic subject context
    is_active = Column(Boolean, default=True)
    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    tenant_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


# ── Chat Message ───────────────────────────────────────────────────
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    agent_type = Column(String(50), nullable=True)  # Which agent handled this: "general_qa", "prediction", etc.
    message_metadata = Column(JSON, default=dict)  # Additional data: dashboard_updates, routing_info, etc.
    token_count = Column(Integer, default=0)  # For usage tracking
    model_used = Column(String(50), nullable=True)  # "gpt-4o", "llama3", etc.
    processing_time_ms = Column(Integer, default=0)  # Performance tracking
    tenant_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
