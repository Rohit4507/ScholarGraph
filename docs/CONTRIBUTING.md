# 🤝 Contributing Guidelines

## Welcome to ScholarGraph AI!

We're excited that you're interested in contributing to ScholarGraph AI! This guide will help you get started and ensure your contributions are successful.

## 🎯 Our Mission

ScholarGraph AI aims to transform information overload into exam intelligence by providing students with advanced AI-powered tools for academic success. We believe in:
- **Accessibility**: Making advanced AI available to all students
- **Quality**: Building reliable, accurate, and helpful tools
- **Innovation**: Pushing the boundaries of educational technology
- **Community**: Fostering collaboration and knowledge sharing

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Git
- Basic knowledge of Python, JavaScript/React, and AI/ML concepts

### Development Setup
```bash
# 1. Fork the repository
# Click "Fork" on GitHub, then clone your fork

git clone https://github.com/YOUR_USERNAME/ScholarGraph.git
cd ScholarGraph

# 2. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/ScholarGraph.git

# 3. Set up development environment
make dev-setup  # or follow manual setup below

# 4. Start development servers
make dev
```

### Manual Development Setup
```bash
# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env
# Edit .env with your API keys
python -c "from database.session import init_db; init_db()"
uvicorn main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev

# LLaMA setup (optional)
ollama pull llama3.1:8b
```

## 📋 How to Contribute

### 1. Find an Issue
- Check [Issues](https://github.com/ORIGINAL_OWNER/ScholarGraph/issues) for open issues
- Look for issues labeled `good first issue` for beginners
- Comment on the issue to claim it (avoid duplicate work)

### 2. Create a Branch
```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Changes
- Follow the coding standards below
- Write tests for your changes
- Update documentation if needed
- Keep commits focused and atomic

### 4. Test Your Changes
```bash
# Run backend tests
cd backend
pytest tests/ -v --cov=.

# Run frontend tests
cd frontend
npm run test

# Run integration tests
python -m pytest tests/integration/ -v

# Check code quality
flake8 backend/
prettier --check frontend/src/
```

### 5. Submit Pull Request
```bash
# Commit your changes
git add .
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

## 🏗️ Project Structure

```
ScholarGraph/
├── backend/                    # Python FastAPI backend
│   ├── main.py                # Application entry point
│   ├── config.py              # Configuration management
│   ├── agents/                # AI agents (LangGraph)
│   ├── api/                   # API routes
│   ├── database/              # Database models and migrations
│   ├── tests/                 # Backend tests
│   └── requirements.txt       # Python dependencies
├── frontend/                   # Next.js frontend
│   ├── src/app/               # Next.js pages
│   ├── src/components/        # React components
│   ├── src/lib/               # Utilities and helpers
│   ├── tests/                 # Frontend tests
│   └── package.json           # Node.js dependencies
├── docs/                       # Documentation
├── docker/                     # Docker configuration
├── k8s/                        # Kubernetes manifests
└── .github/                    # GitHub workflows
```

## 🎨 Contribution Areas

### 🤖 AI/ML Improvements
- **New Agents**: Create specialized academic agents
- **Model Optimization**: Improve LLaMA/OpenAI integration
- **Algorithm Enhancement**: Better probability scoring
- **RAG Improvements**: Enhanced retrieval and generation

### 📊 Backend Development
- **API Features**: New endpoints and functionality
- **Database Optimization**: Performance improvements
- **Security**: Authentication and authorization enhancements
- **Performance**: Caching, optimization, scaling

### 🎨 Frontend Development
- **UI Components**: New React components
- **Visualizations**: D3.js charts and graphs
- **User Experience**: Interface improvements
- **Mobile Support**: Responsive design enhancements

### 📚 Documentation
- **API Docs**: Comprehensive API documentation
- **Tutorials**: Step-by-step guides
- **Architecture**: System design documentation
- **Examples**: Code examples and use cases

### 🧪 Testing
- **Unit Tests**: Backend and frontend test coverage
- **Integration Tests**: End-to-end testing
- **Performance Tests**: Load and stress testing
- **UI Tests**: Automated UI testing

## 📝 Coding Standards

### Python (Backend)
```python
# Use type hints
from typing import List, Optional, Dict

def process_documents(
    documents: List[str],
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process documents and extract topics.
    
    Args:
        documents: List of document content
        user_id: Optional user identifier
        
    Returns:
        Dictionary containing extracted topics and metadata
    """
    # Implementation here
    pass

# Follow PEP 8 style
# Use meaningful variable names
# Add docstrings to all functions
# Keep functions focused and small
```

### JavaScript/TypeScript (Frontend)
```typescript
// Use TypeScript for type safety
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  agentType?: string;
}

// Use functional components with hooks
const ChatInterface: React.FC<ChatProps> = ({ sessionId }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  
  const sendMessage = useCallback(async (content: string) => {
    // Implementation
  }, [sessionId]);
  
  return (
    <div className="chat-interface">
      {/* JSX content */}
    </div>
  );
};

// Follow React best practices
// Use meaningful component names
// Add JSDoc comments for complex functions
```

### Git Commit Messages
```
type(scope): brief description

Detailed explanation of the change and its impact.
Include technical details and reasoning.

Closes #issue-number

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Code style (formatting, etc.)
- refactor: Code refactoring
- test: Adding or updating tests
- chore: Maintenance tasks
```

## 🧪 Testing Guidelines

### Backend Testing
```python
# Use pytest for backend tests
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_chat_session_creation():
    """Test creating a new chat session."""
    response = client.post("/api/chat/sessions", json={
        "session_name": "Test Session"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["session_name"] == "Test Session"

def test_probability_scoring():
    """Test topic probability scoring."""
    # Test implementation
    pass
```

### Frontend Testing
```typescript
// Use Jest and React Testing Library
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInterface } from './ChatInterface';

describe('ChatInterface', () => {
  test('renders chat input', () => {
    render(<ChatInterface sessionId="test-id" />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    expect(input).toBeInTheDocument();
  });
  
  test('sends message on submit', async () => {
    const mockSendMessage = jest.fn();
    render(<ChatInterface sessionId="test-id" onSendMessage={mockSendMessage} />);
    
    const input = screen.getByPlaceholderText('Type your message...');
    const submitButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Hello' } });
    fireEvent.click(submitButton);
    
    expect(mockSendMessage).toHaveBeenCalledWith('Hello');
  });
});
```

## 🔍 Code Review Process

### Before Submitting PR
1. **Self-Review**: Review your own code first
2. **Testing**: Ensure all tests pass
3. **Documentation**: Update relevant documentation
4. **Formatting**: Run code formatting tools
5. **Performance**: Consider performance implications

### Review Guidelines
- **Be Constructive**: Provide helpful, specific feedback
- **Be Respectful**: Maintain professional and positive tone
- **Be Thorough**: Check for bugs, security issues, and performance
- **Be Patient**: Allow time for discussion and changes

### PR Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of the code
- [ ] Code builds successfully without errors
- [ ] All tests pass (100% coverage for new code)
- [ ] Documentation is updated
- [ ] No breaking changes (or clearly documented)
- [ ] Security considerations addressed
- [ ] Performance implications considered

## 🐛 Bug Reports

### Bug Report Template
```markdown
**Bug Description**
Brief description of the bug

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen

**Actual Behavior**
What actually happened

**Screenshots**
Add screenshots if applicable

**Environment**
- OS: [e.g. Windows 10, macOS 12.0]
- Browser: [e.g. Chrome 96, Firefox 95]
- Version: [e.g. v1.0.0]

**Additional Context**
Add any other context about the problem
```

## 💡 Feature Requests

### Feature Request Template
```markdown
**Feature Description**
Brief description of the feature

**Problem Statement**
What problem does this feature solve?

**Proposed Solution**
How do you envision this feature working?

**Alternatives Considered**
What other approaches did you consider?

**Additional Context**
Add any other context or screenshots
```

## 🏷️ Issue Labels

- `bug`: Bug reports and fixes
- `enhancement`: Feature requests and improvements
- `good first issue`: Good for newcomers
- `help wanted`: Community help needed
- `documentation`: Documentation improvements
- `performance`: Performance optimizations
- `security`: Security-related issues
- `breaking change**: Changes that break compatibility
- `wontfix`: Issues that won't be fixed
- `duplicate`: Duplicate issues

## 🎯 Development Priorities

### High Priority
- Bug fixes affecting core functionality
- Security vulnerabilities
- Performance bottlenecks
- Documentation gaps

### Medium Priority
- New features for core functionality
- Code refactoring and cleanup
- Test coverage improvements
- UI/UX enhancements

### Low Priority
- Nice-to-have features
- Experimental features
- Minor optimizations
- Documentation improvements

## 🏆 Recognition

### Contributors
We recognize and appreciate all contributions:
- **Code Contributors**: Developers who write code
- **Documentation Writers**: Those who improve documentation
- **Bug Reporters**: Users who report issues
- **Feature Suggesters**: Those who propose improvements
- **Community Supporters**: Users who help others

### Hall of Fame
Top contributors will be featured in:
- README.md contributors section
- Annual contributor highlights
- Special recognition in releases
- Invitation to core team (for consistent contributors)

## 📞 Getting Help

### Communication Channels
- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and discussions
- **Discord Community**: [Invite link] (if available)
- **Email**: rohitrajput33220@gmail.com

### Resources
- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)

## 📜 Code of Conduct

### Our Pledge
We are committed to providing a welcoming and inclusive environment for all contributors, regardless of:
- Experience level
- Gender identity and expression
- Sexual orientation
- Disability
- Personal appearance
- Body size
- Race
- Ethnicity
- Age
- Religion
- Nationality

### Expected Behavior
- Use welcoming and inclusive language
- Be respectful of different viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy toward other community members

### Unacceptable Behavior
- Harassment, trolling, or discriminatory language
- Personal attacks or political discussions
- Public or private harassment
- Publishing others' private information
- Any other conduct which could reasonably be considered inappropriate

## 🎉 Celebrating Contributions

We celebrate every contribution, no matter how small:
- **First PR**: Special recognition and welcome
- **Significant Features**: Highlighted in release notes
- **Bug Fixes**: Appreciated in acknowledgments
- **Documentation**: Recognized for improving accessibility
- **Community Help**: Valued for supporting others

---

## 🚀 Ready to Contribute?

Thank you for your interest in contributing to ScholarGraph AI! Every contribution helps make educational AI more accessible and effective for students worldwide.

**Next Steps:**
1. 🍴 Fork the repository
2. 🔍 Find an issue or create one
3. 🌿 Create a feature branch
4. 💻 Make your changes
5. 🧪 Test thoroughly
6. 📤 Submit a Pull Request

We look forward to your contributions! 🎓

---

*For questions, reach out to us at [rohitrajput33220@gmail.com](mailto:rohitrajput33220@gmail.com)*
