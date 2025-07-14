# Local Setup Guide 🚀

A quick guide to get the wallstr AI chat system running locally.

## Prerequisites

- Docker & Docker Compose
- Python 3.12
- Node.js & pnpm
- API Keys:
  - OpenAI API key
  - Google API key (for Gemini)

## Quick Start

### 1. Start Infrastructure Services

First, get the database, redis, and other services running:

```bash
cd packages/backend
docker-compose -f docker-compose-minimal.yaml up -d
```

This starts:
- PostgreSQL (port 5441)
- Redis (port 6379)
- RabbitMQ (port 5672)
- MinIO (port 9000)

### 2. Set Up Environment

Create `.env` file in `packages/backend/`:

```bash
cp packages/backend/.env.example packages/backend/.env
```

Update these keys in the `.env`:
```
OPENAI_API_KEY="your-openai-key-here"
GOOGLE_API_KEY="your-google-api-key-here"
```

### 3. Install Backend Dependencies

```bash
cd packages/backend
poetry install
```

### 4. Run Database Migrations

```bash
cd packages/backend
poetry run alembic upgrade head
```

### 5. Start Backend Services

In separate terminals:

**Backend API:**
```bash
cd packages/backend
poetry run uvicorn wallstr.asgi:app --reload --port 8000
```

**Worker (for processing messages):**
```bash
cd packages/backend
poetry run dramatiq wallstr.chat.tasks wallstr.upload.tasks -p 10 -t 10
```

### 6. Start Frontend

```bash
cd packages/frontend
pnpm install
pnpm dev
```

Frontend will be available at http://localhost:3000

## Verify Setup

1. Open http://localhost:3000
2. Navigate to the chat interface
3. Send a message - the AI should respond
4. Check logs to ensure both OpenAI and Gemini are configured

## Common Issues

### Worker Error: "AttributeError: 'BoundLoggerFilteringAtNotset' object has no attribute 'trace'"

This has been fixed in the code, but if you see it:
- Replace `logger.trace()` with `logger.debug()` in affected files
- Restart the worker

### Backend Won't Start

Check that all Docker services are running:
```bash
docker ps
```

### Can't Connect to Database

Ensure PostgreSQL is running on port 5441 (not the default 5432)

## Available LLM Models

The system supports:
- OpenAI: gpt-4o, gpt-4o-mini
- Google: gemini-2.5-flash (via gemini-2.5-flash-preview-04-17)

Models can be toggled in the chat interface.

---

That's it! You should now have a working AI chat system that can process documents and answer questions using either OpenAI or Google Gemini. 🎉