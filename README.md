# WallStr.chat

## Installation

1. Install [pnpm](https://pnpm.io/installation#using-npm)
2. Install [poetry](https://python-poetry.org/docs/#installation)
3. Install dependencies
   ```bash
   pnpm install
   poetry install -C packages/backend
   ```

## Running locally

1. Frontend
   ```bash
   pnpm frontend:dev
   ```
2. Backend, check [backend/README.md](packages/backend/README.md) for more information

   ```bash
   pnpm docker-compose
   # once (optional)
   docker exec -it wallstr_ollama /bin/ollama pull llama3.2
   docker exec -it wallstr_ollama /bin/ollama pull nomic-embed-text

   pnpm backend:dev
   pnpm backend:worker
   ```

3. Open http://localhost:3000
