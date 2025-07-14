# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WallStr is a full-stack AI chat application with document processing capabilities. It's a monorepo containing:
- **Backend**: FastAPI + PostgreSQL + Redis + RabbitMQ + Weaviate
- **Frontend**: Next.js with TypeScript
- **Infrastructure**: Docker Compose for local development

## Essential Development Commands

### Backend (from `packages/backend/`)
```bash
# Setup
poetry install
docker-compose -f docker-compose-minimal.yaml up -d  # Start infrastructure

# Development
poetry run task dev              # API server (port 8000)
poetry run task worker -p 1      # Main worker
poetry run task worker:heavy -p 1 # Document processing worker

# Database
poetry run task migrate          # Apply migrations
poetry run task makemigrations   # Create migration

# Testing & Quality
poetry run task test             # Run tests with coverage
poetry run task lint             # Check formatting
poetry run task format           # Auto-format code
poetry run task mypy             # Type checking
```

### Frontend (from `packages/frontend/`)
```bash
pnpm install
pnpm dev                         # Development server (port 3000)
pnpm build                       # Production build
```

## Architecture Patterns

### Service Layer Pattern
Each module implements a service class inheriting from `BaseService`:
```python
class ChatService(BaseService):
    async def get_chat(self, chat_id: UUID, user_id: UUID) -> ChatModel | None:
        async with self.tx():  # Automatic transaction handling
            # Business logic here
```

### Authentication Flow
- JWT-based with access/refresh tokens
- Use dependency injection: `auth: Auth = Depends()` for protected routes
- `AuthOrAnonym` for optional auth, `AuthExp` for non-expired tokens only

### LLM Integration
- Configured in `wallstr/core/llm.py`
- Supports OpenAI, Google Gemini, Azure, DeepSeek, Replicate
- Rate limiting and token counting built-in
- Streaming responses via Server-Sent Events (SSE)

### Document Processing Pipeline
1. Upload → `DocumentStatus.UPLOADING`
2. Process in background → `DocumentStatus.PROCESSING`
3. Vector embeddings stored in Weaviate
4. Ready for RAG → `DocumentStatus.READY`

### Database Models
- All models inherit from `RecordModel` (includes id, created_at, updated_at, deleted_at)
- Soft deletes enabled by default
- Relationships: Users → Chats → Messages, Documents linked via many-to-many

## Common Tasks

### Adding a New LLM Provider
1. Update `wallstr/conf/models.py` with new provider enum
2. Add configuration in `wallstr/conf/__init__.py`
3. Implement provider logic in `wallstr/core/llm.py`
4. Add environment variables to `.env`

### Creating New API Endpoints
1. Add route in appropriate module's `api.py`
2. Implement business logic in `services.py`
3. Use proper dependencies (`Auth`, database session)
4. Update OpenAPI schema: `poetry run task generate_openapi`

### Running Specific Tests
```bash
poetry run pytest tests/chat/test_service.py::test_specific_function -v
```

### Debugging Worker Tasks
- Check RabbitMQ management UI: http://localhost:15672
- Monitor Redis: http://localhost:8001
- Worker logs show task execution details

## Key Configuration

### Required Environment Variables
- `SECRET_KEY` - JWT signing
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `RABBITMQ_URL` - Message queue
- `STORAGE_URL`, `STORAGE_ACCESS_KEY`, `STORAGE_SECRET_KEY` - MinIO
- LLM API keys: `OPENAI_API_KEY`, `GOOGLE_API_KEY`, etc.

### CORS Configuration
Update `CORS_ALLOW_ORIGINS` in `.env` when deploying to new domains.

## Recent Fixes & Known Issues

### Fixed Issues
- Replaced `logger.trace()` with `logger.debug()` (trace not available in structlog)
- Updated Gemini model to `gemini-2.5-flash-preview-04-17`

### Deployment Notes
- Backend uses custom PostgreSQL port 5441 to avoid conflicts
- Frontend can be deployed to Vercel/Railway
- Use ngrok for exposing local backend during development

## Code Style

- Python: Ruff for formatting and linting
- Type hints required for all functions
- Async-first design
- Pydantic for data validation
- Clear separation between API routes and business logic