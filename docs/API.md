# 🔧 API Documentation

## Overview

ScholarGraph AI provides a comprehensive RESTful API for academic intelligence, document processing, and conversational AI capabilities.

## Base URL
- **Development**: `http://localhost:8000`
- **Production**: `https://api.scholargraph.ai`

## Authentication

### JWT Token Authentication
```bash
# Login to get token
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Use token in requests
curl -X GET "http://localhost:8000/api/dashboard/stats" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### API Key Authentication
```bash
# Use API key for service-to-service communication
curl -X GET "http://localhost:8000/api/dashboard/stats" \
  -H "X-API-Key: YOUR_API_KEY"
```

## Core Endpoints

### Chat System

#### Create Chat Session
```http
POST /api/chat/sessions
Content-Type: application/json

{
  "session_name": "Study Session - Machine Learning"
}
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "session_name": "Study Session - Machine Learning",
  "created_at": "2024-01-01T12:00:00Z",
  "message_count": 0
}
```

#### Stream Chat Response
```http
POST /api/chat/stream
Content-Type: multipart/form-data

message: "What is machine learning?"
session_id: "uuid-string"
subject: "Computer Science"
```

**Response (Server-Sent Events):**
```
data: {"type": "token", "token": "Machine"}
data: {"type": "token", "token": " learning"}
data: {"type": "complete", "agent_type": "general_qa", "processing_time_ms": 3000}
```

#### Get Chat Sessions
```http
GET /api/chat/sessions
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "uuid-string",
      "session_name": "Study Session",
      "created_at": "2024-01-01T12:00:00Z",
      "message_count": 15,
      "last_message_at": "2024-01-01T13:00:00Z"
    }
  ]
}
```

#### Get Session History
```http
GET /api/chat/sessions/{session_id}
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "messages": [
    {
      "message_id": "uuid-string",
      "role": "user",
      "content": "What is machine learning?",
      "created_at": "2024-01-01T12:00:00Z",
      "agent_type": null
    },
    {
      "message_id": "uuid-string",
      "role": "assistant",
      "content": "Machine learning is...",
      "created_at": "2024-01-01T12:00:05Z",
      "agent_type": "general_qa"
    }
  ]
}
```

#### Delete Chat Session
```http
DELETE /api/chat/sessions/{session_id}
Authorization: Bearer YOUR_JWT_TOKEN
```

### Document Processing

#### Upload Document
```http
POST /api/upload/
Content-Type: multipart/form-data

file: [PDF file]
subject: "Machine Learning"
doc_type: "syllabus"
semester: "Fall 2024"
year: 2024
```

**Response:**
```json
{
  "document_id": "uuid-string",
  "filename": "ml_syllabus.pdf",
  "subject": "Machine Learning",
  "doc_type": "syllabus",
  "processing_status": "completed",
  "extracted_topics": ["neural networks", "decision trees", "clustering"],
  "chunk_count": 25
}
```

#### Get Processing Status
```http
GET /api/upload/status/{document_id}
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "document_id": "uuid-string",
  "processing_status": "completed",
  "progress_percentage": 100,
  "extracted_topics": 15,
  "chunks_processed": 25,
  "error_message": null
}
```

### Topic Predictions

#### Get Probability Scores
```http
GET /api/predict/{subject}?user_id=uuid&limit=20
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "subject": "Machine Learning",
  "predictions": [
    {
      "topic_name": "Neural Networks",
      "probability_score": 85.5,
      "priority": "HIGH",
      "frequency_score": 90.0,
      "semantic_score": 82.0,
      "recency_score": 75.0,
      "exam_years_appeared": [2021, 2022, 2023]
    }
  ],
  "total_topics": 45,
  "generated_at": "2024-01-01T12:00:00Z"
}
```

#### Analyze Subject (Multi-Agent)
```http
POST /api/predict/analyze
Content-Type: application/json

{
  "subject": "Machine Learning",
  "analysis_type": "comprehensive",
  "include_recommendations": true
}
```

**Response:**
```json
{
  "subject": "Machine Learning",
  "analysis": {
    "topic_predictions": [...],
    "knowledge_graph": {...},
    "study_recommendations": [...],
    "difficulty_distribution": {...}
  },
  "processing_time_ms": 5000
}
```

### Quiz System

#### Generate Quiz
```http
POST /api/quiz/generate
Content-Type: application/json

{
  "subject": "Machine Learning",
  "difficulty": "medium",
  "count": 10,
  "topics": ["neural networks", "decision trees"],
  "question_types": ["multiple_choice", "true_false"]
}
```

**Response:**
```json
{
  "quiz_id": "uuid-string",
  "subject": "Machine Learning",
  "difficulty": "medium",
  "questions": [
    {
      "question_id": "uuid-string",
      "question_text": "What is backpropagation?",
      "options": [
        {"id": "a", "text": "Optimization algorithm"},
        {"id": "b", "text": "Data preprocessing"},
        {"id": "c", "text": "Feature selection"},
        {"id": "d", "text": "Model evaluation"}
      ],
      "correct_answer": "a",
      "explanation": "Backpropagation is...",
      "topic": "neural networks",
      "difficulty": "medium"
    }
  ],
  "estimated_time_minutes": 15
}
```

#### Submit Quiz Answers
```http
POST /api/quiz/submit
Content-Type: application/json

{
  "quiz_id": "uuid-string",
  "user_answers": [
    {"question_id": "uuid-string", "answer": "a"},
    {"question_id": "uuid-string", "answer": "c"}
  ]
}
```

**Response:**
```json
{
  "quiz_attempt_id": "uuid-string",
  "score": 80,
  "total_questions": 10,
  "correct_answers": 8,
  "performance_analysis": {
    "strengths": ["neural networks"],
    "weaknesses": ["decision trees"],
    "recommendations": ["Review decision tree algorithms"]
  },
  "time_taken_minutes": 12
}
```

### Knowledge Graph

#### Get Knowledge Graph Data
```http
GET /api/graph/{subject}?format=d3_json&include_weights=true
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "nodes": [
    {
      "id": "neural_networks",
      "label": "Neural Networks",
      "group": "core_concept",
      "size": 20,
      "probability_score": 85.5,
      "color": "#ff6b6b"
    }
  ],
  "links": [
    {
      "source": "neural_networks",
      "target": "backpropagation",
      "weight": 0.9,
      "type": "prerequisite"
    }
  ],
  "metadata": {
    "total_nodes": 45,
    "total_edges": 67,
    "generated_at": "2024-01-01T12:00:00Z"
  }
}
```

### Dashboard Analytics

#### Get Dashboard Statistics
```http
GET /api/dashboard/stats?user_id=uuid&subject=Machine%20Learning
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "overview": {
    "total_documents": 25,
    "total_topics": 45,
    "quiz_attempts": 12,
    "average_score": 78.5
  },
  "recent_activity": [
    {
      "type": "document_upload",
      "description": "Uploaded ML syllabus",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "performance_trends": {
    "quiz_scores": [75, 80, 78, 85, 82],
    "study_time_hours": [2, 3, 2.5, 4, 3.5]
  }
}
```

#### Get Study Plan
```http
GET /api/dashboard/study-plan/{subject}?duration_days=30
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "subject": "Machine Learning",
  "study_plan": {
    "duration_days": 30,
    "daily_sessions": [
      {
        "day": 1,
        "topics": ["neural networks basics"],
        "estimated_time_hours": 2,
        "priority": "HIGH",
        "resources": ["Chapter 1", "Video lecture"]
      }
    ],
    "milestones": [
      {
        "day": 7,
        "description": "Complete neural networks module",
        "quiz_recommended": true
      }
    ]
  }
}
```

#### Get Performance Analysis
```http
GET /api/dashboard/performance/{subject}?include_recommendations=true
Authorization: Bearer YOUR_JWT_TOKEN
```

**Response:**
```json
{
  "subject": "Machine Learning",
  "performance": {
    "overall_mastery": 75.5,
    "topic_mastery": {
      "neural_networks": 85.0,
      "decision_trees": 65.0
    },
    "knowledge_gaps": ["decision trees", "ensemble methods"],
    "improvement_trend": "positive"
  },
  "recommendations": [
    {
      "type": "study_focus",
      "description": "Focus on decision tree algorithms",
      "priority": "HIGH"
    }
  ]
}
```

## System Endpoints

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "database_status": "connected",
  "llm_status": {
    "ollama": "available",
    "openai": "available"
  }
}
```

### System Status
```http
GET /api/chat/status
```

**Response:**
```json
{
  "system_status": "operational",
  "llm_status": {
    "primary": "LLaMA 3.1",
    "fallback": "OpenAI GPT-4o",
    "ollama_available": true,
    "openai_available": true
  },
  "active_sessions": 15,
  "total_messages_today": 234
}
```

### Agent Capabilities
```http
GET /api/chat/agents/capabilities
```

**Response:**
```json
{
  "agents": [
    {
      "name": "document_classifier",
      "description": "Classifies uploaded documents",
      "capabilities": ["syllabus", "past_year_questions", "lecture_notes"]
    },
    {
      "name": "prediction_engine",
      "description": "Calculates exam topic probabilities",
      "capabilities": ["probability_scoring", "trend_analysis", "recommendations"]
    }
  ]
}
```

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "subject",
      "issue": "Subject is required"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "uuid-string"
}
```

### HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Rate Limiting
- **Standard Users**: 100 requests per hour
- **Premium Users**: 1000 requests per hour
- **API Keys**: 10,000 requests per hour

## SDK Examples

### Python SDK
```python
from scholargraph import ScholarGraphClient

client = ScholarGraphClient(api_key="your-api-key")

# Create chat session
session = client.chat.create_session("Study Session")

# Stream chat response
for token in client.chat.stream("What is ML?", session.id):
    print(token, end="")

# Upload document
doc = client.documents.upload("syllabus.pdf", "Machine Learning")
print(f"Extracted {len(doc.topics)} topics")
```

### JavaScript SDK
```javascript
import { ScholarGraphClient } from 'scholargraph-js';

const client = new ScholarGraphClient({ apiKey: 'your-api-key' });

// Create chat session
const session = await client.chat.createSession('Study Session');

// Stream chat response
const stream = await client.chat.stream('What is ML?', session.id);
for await (const token of stream) {
  process.stdout.write(token);
}
```

## WebSocket Events

### Real-time Notifications
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Notification:', data);
};

// Events:
// - document_processed
// - quiz_completed
// - study_plan_updated
// - performance_updated
```

This comprehensive API documentation provides developers with all the information needed to integrate with ScholarGraph AI's powerful academic intelligence features.
