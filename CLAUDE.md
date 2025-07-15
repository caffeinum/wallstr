# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WallStr is a full-stack AI chat application with document processing capabilities. It's a monorepo containing:
- **Backend**: FastAPI + PostgreSQL + Redis + RabbitMQ + MinIO + Weaviate
- **Frontend**: Next.js with TypeScript
- **Infrastructure**: Docker Compose for local development

## Critical Setup Requirements

### Both Workers MUST Be Running
The system requires TWO separate worker processes:
1. **Main Worker** (`poetry run task worker`) - Processes chat messages (default queue)
2. **Heavy Worker** (`poetry run task worker:heavy`) - Processes document uploads (parse queue)

**Without both workers, the system will not function properly!**

### Database Migrations
Always run BOTH migrations after infrastructure setup:
```bash
poetry run task migrate          # PostgreSQL database schema
poetry run task migrate_weaviate # Vector database collections
```

Without Weaviate migration, document processing will fail with "class not found" errors.

## Essential Development Commands

### Backend (from `packages/backend/`)
```bash
# Setup
poetry install
docker-compose -f docker-compose-minimal.yaml up -d  # Start infrastructure

# Development
poetry run task dev              # API server (port 8000)
poetry run task worker           # Main worker (chat processing)
poetry run task worker:heavy     # Document processing worker

# IMPORTANT: Both workers must be running for full functionality!
# - worker: processes chat messages (default queue)
# - worker:heavy: processes document uploads (parse queue)

# Running workers manually (if needed):
poetry run dramatiq wallstr.worker.main -p 1 -t 2 -Q default
poetry run dramatiq wallstr.worker.heavy -p 1 -t 1 -Q parse

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
- Check RabbitMQ management UI: http://localhost:15672 (user/password123)
- Monitor Redis: http://localhost:8001
- Worker logs show task execution details
- Document processing uses `parse` queue, chat uses `default` queue

### Troubleshooting Document Uploads
1. Check both workers are running: `ps aux | grep dramatiq`
2. Verify document status in DB - stuck in `UPLOADED` means worker issue
3. Check for Weaviate errors - "class not found" means run migrations
4. Monitor MinIO for uploaded files: http://localhost:9001 (user/password123)

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
- File uploads failing with 429 error: Fixed by applying MinIO bucket policy for presigned URLs
- Made `OLLAMA_URL` optional in settings (was required, blocking production deployments)
- Document processing failing: Fixed by running Weaviate migrations

### MinIO/Storage Setup
File uploads use MinIO with presigned URLs. If uploads fail:
1. Ensure MinIO container is running: `docker ps | grep minio`
2. Apply bucket policy to allow browser uploads:
```python
# Apply public read/write policy for presigned URL uploads
s3_client.put_bucket_policy(Bucket='wallstr', Policy=json.dumps({
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"AWS": "*"},
        "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
        "Resource": "arn:aws:s3:::wallstr/*"
    }]
}))
```
3. Restart MinIO: `docker restart wallstr_minio`

### Railway Deployment
Environment variables for Railway:
- `ENV` must be `prod` (not "production" or "development")
- `DATABASE_URL` and `REDIS_URL` are auto-provided when you add those services
- For RabbitMQ: Use internal URL `amqp://user:password@rabbitmq.railway.internal:5672/`
- Update `CORS_ALLOW_ORIGINS` with your Railway frontend URL

Workers need to be deployed as separate services with start commands:
- Main worker: `poetry run task worker`
- Heavy worker: `poetry run task worker:heavy`

### Deployment Notes
- Backend uses custom PostgreSQL port 5441 to avoid conflicts
- Frontend can be deployed to Vercel/Railway  
- Use ngrok for exposing local backend during development
- For CORS with ngrok: Add ngrok URL to `CORS_ALLOW_ORIGINS` in .env

## Code Style

- Python: Ruff for formatting and linting
- Type hints required for all functions
- Async-first design
- Pydantic for data validation
- Clear separation between API routes and business logic