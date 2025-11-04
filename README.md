# GitHub Collaboration Backend

A FastAPI-based backend service that enhances GitHub repository collaboration through AI-powered code analysis and automated insights.

## Overview

The GitHub Collaboration Backend provides a comprehensive suite of tools for code analysis, review automation, and repository insights. It leverages modern AI technologies to assist developers in code review, documentation, and quality assurance processes.

## Features

- Secure authentication with JWT
- AI-powered code analysis using Google's Gemini
- Automated code review generation
- Repository metrics and insights
- Documentation automation
- Bug detection and analysis
- Natural language codebase querying
- GitHub integration and automation

## Technology Stack

### Core Technologies
- **Backend Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT + bcrypt

### AI/ML Components
- **Code Analysis**: Google Gemini API
- **Document Processing**: LangChain
- **Vector Storage**: FAISS

### Development Tools
- **Documentation**: OpenAPI/Swagger
- **Testing**: pytest
- **Container**: Docker & docker-compose
- **Database Migration**: Alembic

## Installation

### Prerequisites
```
Python 3.9 or higher
PostgreSQL
Docker & Docker Compose (optional)
```

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/negihimanshu015/github-collab-backend.git
cd github-collab-backend
```

2. Set up Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```
DATABASE_URL=postgresql://user:password@localhost:5432/ai_github_saas
SECRET_KEY=your-secure-secret-key
GEMINI_API_KEY=your-gemini-api-key
GITHUB_ACCESS_TOKEN=your-github-token
ASSEMBLYAI_API_KEY=your-assemblyai-key
```

## Usage

### Local Development
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment
```bash
docker-compose up -d
```

The API service will be available at:
- Base URL: `http://localhost:8000`
- API Documentation: `/api/docs`
- Alternative Documentation: `/api/redoc`

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User authentication

### Project Management
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects/{id}` - Project details
- `GET /api/v1/projects/{id}/analyses` - Project analyses

### Code Analysis
- `POST /api/v1/analyze/code-review` - Code review generation
- `POST /api/v1/analyze/documentation` - Documentation generation
- `POST /api/v1/analyze/bug-detection` - Bug detection
- `POST /api/v1/repo/analyze-complete` - Full repository analysis

## Project Structure
```
src/
├── api/           # API routes and controllers
├── core/          # Core application components
├── db/            # Database models and migrations
├── services/      # External service integrations
├── utils/         # Utility functions
├── main.py        # Application entry point
└── schemas.py     # Data models and validation
```

## Development

### Running Tests
```bash
pytest
```

### Database Migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Production Deployment

### Security Considerations
1. Configure HTTPS
2. Set up rate limiting
3. Implement proper logging
4. Use production-grade WSGI server
5. Set secure CORS policies

### Production Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Implement changes with tests
4. Update documentation
5. Submit a pull request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google Gemini API](https://cloud.google.com/vertex-ai)
- [LangChain Documentation](https://langchain.readthedocs.io/)