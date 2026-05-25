# AI Workspace OS

Production-grade multi-agent AI platform with RAG, real-time streaming, and workflow automation.

## Architecture

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 15, TypeScript, TailwindCSS |
| **Backend API** | FastAPI, Pydantic, SQLAlchemy 2.0, async |
| **LLM** | Groq API (Llama 3.3 70B, DeepSeek R1 70B) or OpenAI API (GPT-4o, GPT-4o-mini) |
| **Agents** | LangGraph orchestrator, Research/Code/Planning agents |
| **RAG** | ChromaDB, sentence-transformers, hybrid retrieval |
| **Task Queue** | Celery + Redis |
| **Database** | PostgreSQL 16, async via asyncpg |
| **Cache** | Redis 7 |

## Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/Ahmed-Rizk1/Full_rag-One.git
cd Full_rag-One
cp .env.example .env
# Edit .env → set SECRET_KEY. (Optional) set GROQ_API_KEY. Users can configure their own keys in settings.
```

### 2. Launch with Docker Compose

```bash
docker compose up -d --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### 3. Local Development (Backend)

```bash
cd backend
uv sync
# Start infrastructure
docker compose -f ../docker-compose.yml up db redis chroma -d
# Run API server
uv run uvicorn app.main:app --reload
# Run tests
uv run python -m pytest --tb=short -q
# Lint
uv run ruff check .
```

### 4. Local Development (Frontend)

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/signup` | Register |
| POST | `/api/v1/auth/login` | Login (JWT) |
| POST | `/api/v1/auth/refresh` | Refresh token |
| GET | `/api/v1/auth/me` | Current user |
| PUT | `/api/v1/auth/settings` | Update preferred provider (Groq or OpenAI) and validate API keys |
| POST | `/api/v1/documents/upload` | Upload document (PDF/DOCX/TXT) |
| GET | `/api/v1/documents/` | List documents |
| POST | `/api/v1/chat/{id}/message` | Send message (SSE stream) |
| POST | `/api/v1/workflows/` | Create workflow |
| POST | `/api/v1/workflows/{id}/execute` | Execute workflow (async) |
| POST | `/api/v1/repositories/analyze` | Trigger repo analysis |
| GET | `/api/v1/repositories/{id}` | Get analysis results |
| GET | `/api/v1/health` | Health check |

## Project Structure

```
backend/
├── app/
│   ├── agents/          # LangGraph multi-agent system
│   ├── api/v1/          # FastAPI route handlers
│   ├── core/            # Security, dependencies, exceptions
│   ├── db/              # Async SQLAlchemy session
│   ├── memory/          # Short-term (Redis) + Long-term memory
│   ├── models/          # SQLAlchemy ORM models
│   ├── rag/             # Ingestion, chunking, embedding, retrieval
│   ├── repositories/    # Generic CRUD repositories
│   ├── services/        # Business logic layer
│   └── workers/         # Celery background tasks
├── tests/
└── Dockerfile

frontend/
├── src/
│   ├── app/             # Next.js App Router pages
│   ├── components/      # Reusable UI components
│   ├── lib/             # API client, auth, hooks
│   └── types/           # TypeScript interfaces
└── Dockerfile
```

## SaaS API Key Configuration

This project supports dynamic, multi-tenant API key routing. Each user signs up and provides their own Groq or OpenAI API key.
- Navigate to `/settings` after logging in.
- Choose your preferred LLM provider (Groq or OpenAI).
- Enter your credentials, which are validated instantly against the provider API before saving.
- The multi-agent orchestrator dynamically routes completions and token streams using your credentials.

## License

MIT
