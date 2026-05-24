    # AI Workspace OS — System Architecture Blueprint

    ## 1. High-Level System Architecture

    ```mermaid
    graph TB
        subgraph "Client Layer"
            FE["Next.js 15 Frontend<br/>(TypeScript + shadcn/ui)"]
        end

        subgraph "Edge Layer"
            GW["API Gateway<br/>(FastAPI)"]
            RL["Rate Limiter<br/>(Redis)"]
            AUTH["JWT Auth<br/>Middleware"]
        end

        subgraph "Application Layer"
            CHAT["Chat Service"]
            DOC["Document Service"]
            WF["Workflow Service"]
            REPO["Repository Service"]
            USR["User Service"]
        end

        subgraph "Intelligence Layer"
            ORCH["Agent Orchestrator<br/>(LangGraph)"]
            RES["Research Agent"]
            CODE["Code Agent"]
            PLAN["Planning Agent"]
            MEM_A["Memory Agent"]
            AUTO["Automation Agent"]
        end

        subgraph "Knowledge Layer"
            RAG["RAG Engine"]
            CHUNK["Chunking Pipeline"]
            EMB["Embedding Service"]
            RET["Hybrid Retriever"]
        end

        subgraph "Memory Layer"
            STM["Short-Term Memory<br/>(Redis)"]
            LTM["Long-Term Memory<br/>(PostgreSQL + ChromaDB)"]
        end

        subgraph "Infrastructure Layer"
            PG[(PostgreSQL)]
            CHROMA[(ChromaDB)]
            REDIS[(Redis)]
            CELERY["Celery Workers"]
            GROQ["Groq API<br/>(llama-3.3-70b / deepseek-r1)"]
        end

        FE <-->|WebSocket + REST| GW
        GW --> RL
        GW --> AUTH
        GW --> CHAT & DOC & WF & REPO & USR
        CHAT --> ORCH
        ORCH --> RES & CODE & PLAN & MEM_A & AUTO
        RES --> RAG
        RAG --> CHUNK --> EMB --> RET
        RET --> CHROMA
        MEM_A --> STM & LTM
        DOC --> CELERY
        WF --> CELERY
        ORCH --> GROQ
        CHAT --> PG
        DOC --> PG
        USR --> PG
        CELERY --> REDIS
    ```

    ### Layered Architecture Summary

    | Layer | Responsibility | Technology |
    |---|---|---|
    | Client | UI, state, streaming | Next.js 15, shadcn/ui, TailwindCSS |
    | Edge | Auth, routing, rate limiting | FastAPI middleware, Redis |
    | Application | Business logic, CRUD | FastAPI services, Pydantic |
    | Intelligence | Agent orchestration, LLM calls | LangGraph, LangChain, Groq |
    | Knowledge | Document ingestion, retrieval | ChromaDB, sentence-transformers |
    | Memory | Session + persistent context | Redis (STM), PostgreSQL+ChromaDB (LTM) |
    | Infrastructure | Persistence, queues, LLM provider | PostgreSQL, Redis, Celery, Groq API |

    ---

    ## 2. Service Boundaries

    Each service is a self-contained module with its own router, schemas, repository, and business logic. Services communicate only via defined interfaces (dependency injection, event bus, or Celery tasks).

    ```mermaid
    graph LR
        subgraph "Auth Boundary"
            A1["AuthRouter"]
            A2["AuthService"]
            A3["UserRepository"]
        end

        subgraph "Chat Boundary"
            B1["ChatRouter"]
            B2["ChatService"]
            B3["ConversationRepository"]
            B4["AgentOrchestrator"]
        end

        subgraph "Document Boundary"
            C1["DocumentRouter"]
            C2["DocumentService"]
            C3["DocumentRepository"]
            C4["IngestionWorker"]
        end

        subgraph "RAG Boundary"
            D1["RAGService"]
            D2["ChunkingPipeline"]
            D3["EmbeddingService"]
            D4["HybridRetriever"]
        end

        subgraph "Workflow Boundary"
            E1["WorkflowRouter"]
            E2["WorkflowService"]
            E3["WorkflowRepository"]
            E4["WorkflowWorker"]
        end

        subgraph "Repository Analysis Boundary"
            F1["RepoRouter"]
            F2["RepoService"]
            F3["CodeAnalysisWorker"]
        end

        subgraph "Memory Boundary"
            G1["MemoryService"]
            G2["ShortTermStore"]
            G3["LongTermStore"]
        end
    ```

    ### Coupling Rules

    - Services depend on **abstractions** (protocols/ABCs), never concrete implementations
    - Cross-service calls go through **service interfaces** injected via FastAPI's `Depends()`
    - Async work crosses boundaries only via **Celery task dispatch** (fire-and-forget with callback)
    - Shared types live in `core/schemas/` — no service imports another service's models

    ---

    ## 3. Folder Structure

    ```
    ai-workspace-os/
    ├── backend/
    │   ├── app/
    │   │   ├── __init__.py
    │   │   ├── main.py                    # FastAPI app factory
    │   │   ├── config.py                  # Settings (pydantic-settings)
    │   │   │
    │   │   ├── core/                      # Shared kernel
    │   │   │   ├── __init__.py
    │   │   │   ├── security.py            # JWT encode/decode, password hashing
    │   │   │   ├── dependencies.py        # FastAPI dependency providers
    │   │   │   ├── exceptions.py          # Custom exception hierarchy
    │   │   │   ├── middleware.py          # Rate limiting, logging, CORS
    │   │   │   ├── events.py              # App lifecycle (startup/shutdown)
    │   │   │   └── schemas/               # Shared Pydantic models
    │   │   │       ├── __init__.py
    │   │   │       ├── common.py          # Pagination, APIResponse, ErrorDetail
    │   │   │       └── enums.py           # Shared enums (roles, status, agent types)
    │   │   │
    │   │   ├── api/                       # HTTP layer only — no business logic
    │   │   │   ├── __init__.py
    │   │   │   ├── router.py              # Root router aggregating all sub-routers
    │   │   │   └── v1/
    │   │   │       ├── __init__.py
    │   │   │       ├── auth.py
    │   │   │       ├── chat.py
    │   │   │       ├── documents.py
    │   │   │       ├── workflows.py
    │   │   │       ├── repositories.py
    │   │   │       └── health.py
    │   │   │
    │   │   ├── models/                    # SQLAlchemy ORM models
    │   │   │   ├── __init__.py
    │   │   │   ├── base.py               # DeclarativeBase, mixins (TimestampMixin, UUIDMixin)
    │   │   │   ├── user.py
    │   │   │   ├── conversation.py
    │   │   │   ├── message.py
    │   │   │   ├── document.py
    │   │   │   ├── workflow.py
    │   │   │   └── memory.py
    │   │   │
    │   │   ├── repositories/             # Data access layer (SQL queries)
    │   │   │   ├── __init__.py
    │   │   │   ├── base.py               # Generic CRUD repository
    │   │   │   ├── user_repo.py
    │   │   │   ├── conversation_repo.py
    │   │   │   ├── document_repo.py
    │   │   │   ├── workflow_repo.py
    │   │   │   └── memory_repo.py
    │   │   │
    │   │   ├── services/                  # Business logic layer
    │   │   │   ├── __init__.py
    │   │   │   ├── auth_service.py
    │   │   │   ├── chat_service.py
    │   │   │   ├── document_service.py
    │   │   │   ├── workflow_service.py
    │   │   │   ├── repo_service.py
    │   │   │   └── user_service.py
    │   │   │
    │   │   ├── agents/                    # Intelligence layer
    │   │   │   ├── __init__.py
    │   │   │   ├── orchestrator.py        # LangGraph state machine — routes to agents
    │   │   │   ├── base_agent.py          # Abstract agent interface
    │   │   │   ├── research_agent.py
    │   │   │   ├── code_agent.py
    │   │   │   ├── planning_agent.py
    │   │   │   ├── memory_agent.py
    │   │   │   ├── automation_agent.py
    │   │   │   ├── tools/                 # LangChain tool definitions
    │   │   │   │   ├── __init__.py
    │   │   │   │   ├── search_tools.py
    │   │   │   │   ├── code_tools.py
    │   │   │   │   ├── file_tools.py
    │   │   │   │   └── workflow_tools.py
    │   │   │   └── prompts/               # System prompts (jinja2 or plain text)
    │   │   │       ├── research.txt
    │   │   │       ├── code_review.txt
    │   │   │       ├── planning.txt
    │   │   │       └── automation.txt
    │   │   │
    │   │   ├── rag/                       # Knowledge / RAG engine
    │   │   │   ├── __init__.py
    │   │   │   ├── ingestion.py           # File parsing (PDF, DOCX, TXT)
    │   │   │   ├── chunking.py            # Text splitting strategies
    │   │   │   ├── embeddings.py          # Embedding model wrapper
    │   │   │   ├── retriever.py           # Hybrid retrieval (dense + keyword)
    │   │   │   ├── vector_store.py        # ChromaDB adapter
    │   │   │   └── cache.py               # Semantic cache (Redis)
    │   │   │
    │   │   ├── memory/                    # Memory subsystem
    │   │   │   ├── __init__.py
    │   │   │   ├── short_term.py          # Redis-backed session memory
    │   │   │   ├── long_term.py           # PostgreSQL + ChromaDB persistent memory
    │   │   │   └── manager.py             # Unified memory interface
    │   │   │
    │   │   ├── workers/                   # Celery async tasks
    │   │   │   ├── __init__.py
    │   │   │   ├── celery_app.py          # Celery configuration
    │   │   │   ├── ingestion_tasks.py     # Document processing
    │   │   │   ├── workflow_tasks.py      # Workflow execution
    │   │   │   └── repo_tasks.py          # Repository analysis
    │   │   │
    │   │   └── db/                        # Database setup
    │   │       ├── __init__.py
    │   │       ├── session.py             # AsyncSession factory
    │   │       └── migrations/            # Alembic migrations
    │   │           ├── env.py
    │   │           └── versions/
    │   │
    │   ├── tests/
    │   │   ├── conftest.py
    │   │   ├── unit/
    │   │   ├── integration/
    │   │   └── e2e/
    │   │
    │   ├── pyproject.toml                 # uv project config
    │   ├── alembic.ini
    │   └── Dockerfile
    │
    ├── frontend/
    │   ├── src/
    │   │   ├── app/                       # Next.js 15 App Router
    │   │   │   ├── layout.tsx
    │   │   │   ├── page.tsx               # Landing
    │   │   │   ├── (auth)/
    │   │   │   │   ├── login/page.tsx
    │   │   │   │   └── signup/page.tsx
    │   │   │   ├── dashboard/page.tsx
    │   │   │   ├── workspace/page.tsx     # AI Chat
    │   │   │   ├── documents/page.tsx
    │   │   │   ├── workflows/page.tsx
    │   │   │   ├── repositories/page.tsx
    │   │   │   └── settings/page.tsx
    │   │   │
    │   │   ├── components/
    │   │   │   ├── ui/                    # shadcn/ui primitives
    │   │   │   ├── chat/
    │   │   │   ├── documents/
    │   │   │   ├── workflows/
    │   │   │   └── layout/
    │   │   │
    │   │   ├── lib/
    │   │   │   ├── api.ts                 # API client (fetch wrapper)
    │   │   │   ├── auth.ts                # Token management
    │   │   │   ├── hooks/                 # Custom React hooks
    │   │   │   └── utils.ts
    │   │   │
    │   │   └── types/                     # TypeScript interfaces
    │   │       └── index.ts
    │   │
    │   ├── package.json
    │   ├── tailwind.config.ts
    │   ├── tsconfig.json
    │   └── Dockerfile
    │
    ├── docker-compose.yml
    ├── docker-compose.dev.yml
    ├── .env.example
    ├── .github/
    │   └── workflows/
    │       ├── ci.yml
    │       └── deploy.yml
    ├── README.md
    └── docs/
        ├── architecture.md
        └── api.md
    ```

    ---

    ## 4. Database Schema

    ```mermaid
    erDiagram
        users {
            uuid id PK
            varchar email UK
            varchar hashed_password
            varchar full_name
            varchar role "admin | user | viewer"
            jsonb preferences
            timestamp created_at
            timestamp updated_at
        }

        conversations {
            uuid id PK
            uuid user_id FK
            varchar title
            varchar agent_type "research | code | planning | general"
            jsonb metadata
            timestamp created_at
            timestamp updated_at
        }

        messages {
            uuid id PK
            uuid conversation_id FK
            varchar role "user | assistant | system | tool"
            text content
            jsonb tool_calls
            jsonb citations
            integer token_count
            timestamp created_at
        }

        documents {
            uuid id PK
            uuid user_id FK
            varchar filename
            varchar content_type
            varchar storage_path
            varchar status "pending | processing | ready | failed"
            integer chunk_count
            jsonb metadata
            timestamp created_at
        }

        document_chunks {
            uuid id PK
            uuid document_id FK
            integer chunk_index
            text content
            varchar embedding_id "ChromaDB reference"
            jsonb metadata
            timestamp created_at
        }

        workflows {
            uuid id PK
            uuid user_id FK
            varchar name
            varchar status "draft | running | completed | failed | paused"
            jsonb definition "DAG of steps"
            jsonb execution_log
            varchar schedule "cron expression, nullable"
            timestamp started_at
            timestamp completed_at
            timestamp created_at
        }

        workflow_steps {
            uuid id PK
            uuid workflow_id FK
            integer step_order
            varchar agent_type
            varchar status "pending | running | completed | failed"
            jsonb input_data
            jsonb output_data
            timestamp started_at
            timestamp completed_at
        }

        memories {
            uuid id PK
            uuid user_id FK
            varchar memory_type "fact | preference | insight | workflow_result"
            text content
            varchar embedding_id "ChromaDB reference"
            float importance_score
            jsonb metadata
            timestamp last_accessed
            timestamp created_at
        }

        repo_analyses {
            uuid id PK
            uuid user_id FK
            varchar repo_url
            varchar status "pending | analyzing | completed | failed"
            jsonb summary
            jsonb dependencies
            jsonb architecture
            jsonb pr_reviews
            timestamp created_at
        }

        users ||--o{ conversations : "has"
        users ||--o{ documents : "uploads"
        users ||--o{ workflows : "creates"
        users ||--o{ memories : "accumulates"
        users ||--o{ repo_analyses : "requests"
        conversations ||--o{ messages : "contains"
        documents ||--o{ document_chunks : "split_into"
        workflows ||--o{ workflow_steps : "composed_of"
    ```

    ### ChromaDB Collections

    | Collection | Purpose | Metadata Fields |
    |---|---|---|
    | `document_chunks` | RAG retrieval | `document_id`, `user_id`, `chunk_index`, `filename` |
    | `user_memories` | Long-term memory retrieval | `user_id`, `memory_type`, `importance_score` |
    | `semantic_cache` | LLM response caching | `query_hash`, `ttl`, `model` |

    ### Redis Key Patterns

    | Pattern | Purpose | TTL |
    |---|---|---|
    | `session:{user_id}:{conv_id}` | Short-term conversation memory | 2h |
    | `rate:{user_id}` | Rate limiting counter | 60s |
    | `cache:semantic:{hash}` | Semantic query cache | 1h |
    | `task:{task_id}` | Celery task status | 24h |
    | `stream:{conv_id}` | SSE streaming channel | 5min |

    ---

    ## 5. Agent Orchestration Flow

    ```mermaid
    stateDiagram-v2
        [*] --> Classify
        Classify --> ResearchAgent: knowledge_query
        Classify --> CodeAgent: code_analysis | pr_review
        Classify --> PlanningAgent: task_breakdown
        Classify --> AutomationAgent: workflow_exec
        Classify --> DirectLLM: general_chat

        ResearchAgent --> MemoryAgent: store_findings
        CodeAgent --> MemoryAgent: store_analysis
        PlanningAgent --> AutomationAgent: execute_plan
        AutomationAgent --> MemoryAgent: store_results

        MemoryAgent --> Synthesize
        DirectLLM --> Synthesize
        ResearchAgent --> Synthesize
        CodeAgent --> Synthesize
        PlanningAgent --> Synthesize

        Synthesize --> [*]
    ```

    ### LangGraph State Machine

    ```python
    # Conceptual graph definition (not implementation code)
    class AgentState(TypedDict):
        messages: list[BaseMessage]
        user_id: str
        conversation_id: str
        agent_type: str | None        # Resolved by classifier
        context: list[Document]       # RAG-retrieved context
        memory: list[str]             # Relevant memories
        tool_results: list[dict]      # Tool call outputs
        citations: list[dict]         # Source references
        should_continue: bool

    # Graph nodes:
    # 1. classify_intent    → determines agent_type
    # 2. retrieve_memory    → fetches relevant STM + LTM
    # 3. retrieve_context   → RAG retrieval if knowledge query
    # 4. route_to_agent     → conditional edge to specialist agent
    # 5. execute_agent      → runs agent with tools
    # 6. store_memory       → persists important findings
    # 7. synthesize         → formats final response with citations
    ```

    ### Agent-Tool Mapping

    | Agent | Tools Available |
    |---|---|
    | Research | `semantic_search`, `keyword_search`, `summarize_document`, `cite_source` |
    | Code | `analyze_diff`, `explain_code`, `detect_issues`, `suggest_refactor` |
    | Planning | `create_subtasks`, `estimate_effort`, `generate_plan` |
    | Memory | `store_memory`, `recall_memory`, `forget_memory` |
    | Automation | `execute_workflow_step`, `chain_tools`, `schedule_task` |

    ---

    ## 6. API Design

    ### Base URL: `/api/v1`

    ### Auth Endpoints

    | Method | Path | Description |
    |---|---|---|
    | `POST` | `/auth/signup` | Register new user |
    | `POST` | `/auth/login` | Get access + refresh tokens |
    | `POST` | `/auth/refresh` | Refresh access token |
    | `GET` | `/auth/me` | Get current user profile |

    ### Chat Endpoints

    | Method | Path | Description |
    |---|---|---|
    | `POST` | `/chat/conversations` | Create conversation |
    | `GET` | `/chat/conversations` | List user conversations |
    | `GET` | `/chat/conversations/{id}` | Get conversation with messages |
    | `DELETE` | `/chat/conversations/{id}` | Delete conversation |
    | `POST` | `/chat/conversations/{id}/messages` | Send message (returns SSE stream) |

    ### Document Endpoints

    | Method | Path | Description |
    |---|---|---|
    | `POST` | `/documents/upload` | Upload file(s) — triggers async ingestion |
    | `GET` | `/documents` | List user documents |
    | `GET` | `/documents/{id}` | Get document metadata + status |
    | `DELETE` | `/documents/{id}` | Delete document + chunks |
    | `POST` | `/documents/{id}/query` | RAG query against specific document |

    ### Workflow Endpoints

    | Method | Path | Description |
    |---|---|---|
    | `POST` | `/workflows` | Create workflow definition |
    | `GET` | `/workflows` | List workflows |
    | `GET` | `/workflows/{id}` | Get workflow + steps + status |
    | `POST` | `/workflows/{id}/execute` | Trigger async execution |
    | `POST` | `/workflows/{id}/pause` | Pause running workflow |
    | `DELETE` | `/workflows/{id}` | Delete workflow |

    ### Repository Endpoints

    | Method | Path | Description |
    |---|---|---|
    | `POST` | `/repositories/analyze` | Submit repo URL for analysis |
    | `GET` | `/repositories/{id}` | Get analysis results |
    | `POST` | `/repositories/review-pr` | Submit PR diff for review |

    ### System Endpoints

    | Method | Path | Description |
    |---|---|---|
    | `GET` | `/health` | Health check (DB, Redis, ChromaDB) |
    | `GET` | `/health/ready` | Readiness probe |

    ### Streaming Protocol

    Chat messages use **Server-Sent Events (SSE)** via `text/event-stream`:

    ```
    event: token
    data: {"content": "Hello", "type": "token"}

    event: citation
    data: {"source": "doc.pdf", "chunk_id": "abc", "page": 3}

    event: tool_call
    data: {"tool": "semantic_search", "status": "started"}

    event: done
    data: {"message_id": "uuid", "token_count": 142}
    ```

    ---

    ## 7. Event / Data Flow

    ### Chat Message Flow

    ```mermaid
    sequenceDiagram
        participant U as User (Browser)
        participant GW as API Gateway
        participant CS as ChatService
        participant ORCH as Orchestrator
        participant RAG as RAG Engine
        participant MEM as Memory
        participant LLM as Groq API
        participant DB as PostgreSQL

        U->>GW: POST /chat/{conv_id}/messages
        GW->>GW: Validate JWT, rate limit
        GW->>CS: Forward request
        CS->>DB: Persist user message
        CS->>ORCH: Invoke agent graph

        ORCH->>ORCH: Classify intent
        ORCH->>MEM: Retrieve memories
        ORCH->>RAG: Retrieve context (if needed)
        RAG-->>ORCH: Relevant chunks + citations

        ORCH->>LLM: Stream completion
        loop Token Streaming
            LLM-->>ORCH: Token
            ORCH-->>CS: Token
            CS-->>U: SSE event: token
        end

        ORCH->>MEM: Store new memories
        ORCH->>DB: Persist assistant message
        CS-->>U: SSE event: done
    ```

    ### Document Ingestion Flow

    ```mermaid
    sequenceDiagram
        participant U as User
        participant API as DocumentRouter
        participant SVC as DocumentService
        participant DB as PostgreSQL
        participant Q as Redis/Celery
        participant W as IngestionWorker
        participant RAG as RAG Engine
        participant VEC as ChromaDB

        U->>API: POST /documents/upload (file)
        API->>SVC: Handle upload
        SVC->>DB: Create document record (status=pending)
        SVC->>Q: Dispatch ingestion task
        SVC-->>U: 202 Accepted {document_id, status: pending}

        Q->>W: Pick up task
        W->>W: Parse file (PDF/DOCX/TXT)
        W->>RAG: Chunk text
        RAG->>RAG: Generate embeddings
        RAG->>VEC: Store vectors
        RAG->>DB: Store chunk records
        W->>DB: Update document (status=ready, chunk_count=N)
    ```

    ### Workflow Execution Flow

    ```mermaid
    sequenceDiagram
        participant U as User
        participant API as WorkflowRouter
        participant Q as Celery
        participant W as WorkflowWorker
        participant ORCH as Orchestrator
        participant DB as PostgreSQL

        U->>API: POST /workflows/{id}/execute
        API->>DB: Update status=running
        API->>Q: Dispatch workflow task
        API-->>U: 202 Accepted

        loop For each step in DAG
            Q->>W: Execute step
            W->>ORCH: Run agent for step
            ORCH-->>W: Step result
            W->>DB: Update step status + output
        end

        W->>DB: Update workflow status=completed
    ```

    ---

    ## 8. Recommended Development Order

    > [!IMPORTANT]
    > Each phase is independently deployable and testable. Complete one before starting the next.

    ### Phase 1 — Foundation (Week 1)
    1. Project scaffolding (`pyproject.toml`, `uv` venv, Dockerfile, docker-compose)
    2. `core/` — config, exceptions, schemas, enums
    3. `db/` — AsyncSession, Alembic setup, base models
    4. `models/` — User model
    5. `repositories/` — Base CRUD + UserRepository
    6. `services/` — AuthService (JWT issue/verify, signup/login)
    7. `api/v1/auth.py` + `health.py`
    8. Tests for auth flow

    ### Phase 2 — Chat & LLM Integration (Week 2)
    1. Groq LLM client wrapper (with retry, rate limiting)
    2. `models/` — Conversation, Message
    3. `services/` — ChatService (basic, no agents yet)
    4. `api/v1/chat.py` — SSE streaming endpoint
    5. `memory/short_term.py` — Redis session context
    6. Tests for chat + streaming

    ### Phase 3 — RAG Engine (Week 3)
    1. `rag/ingestion.py` — PDF, DOCX, TXT parsers
    2. `rag/chunking.py` — Recursive text splitter
    3. `rag/embeddings.py` — Sentence-transformers wrapper
    4. `rag/vector_store.py` — ChromaDB adapter
    5. `rag/retriever.py` — Hybrid retrieval
    6. `models/` — Document, DocumentChunk
    7. `workers/ingestion_tasks.py` — Celery background ingestion
    8. `api/v1/documents.py`
    9. Tests for ingestion + retrieval

    ### Phase 4 — Agent System (Week 4)
    1. `agents/base_agent.py` — Abstract agent protocol
    2. `agents/orchestrator.py` — LangGraph state machine
    3. `agents/research_agent.py` — RAG-powered Q&A
    4. `agents/tools/` — Search + file tools
    5. Wire orchestrator into ChatService
    6. `agents/code_agent.py` — Diff analysis + code review
    7. `agents/planning_agent.py` — Task decomposition
    8. Tests for agent routing + execution

    ### Phase 5 — Memory & Workflows (Week 5)
    1. `memory/long_term.py` — PostgreSQL + ChromaDB persistence
    2. `memory/manager.py` — Unified memory interface
    3. `agents/memory_agent.py` — Memory storage/retrieval agent
    4. `models/` — Workflow, WorkflowStep
    5. `services/workflow_service.py`
    6. `workers/workflow_tasks.py`
    7. `agents/automation_agent.py`
    8. `api/v1/workflows.py`

    ### Phase 6 — Repository Intelligence (Week 6)
    1. `services/repo_service.py` — Git clone, diff parsing
    2. `workers/repo_tasks.py` — Background analysis
    3. `agents/tools/code_tools.py` — PR review tools
    4. `api/v1/repositories.py`
    5. Semantic caching (`rag/cache.py`)

    ### Phase 7 — Frontend (Weeks 7-8)
    1. Next.js 15 scaffolding + shadcn/ui + TailwindCSS
    2. Auth pages (login/signup)
    3. Dashboard
    4. AI Workspace (chat with SSE streaming)
    5. Document management
    6. Workflow builder
    7. Repository analyzer
    8. Settings
    9. Landing page

    ### Phase 8 — Production Hardening (Week 9)
    1. Docker Compose production config
    2. GitHub Actions CI/CD
    3. Observability hooks (structured logging, metrics)
    4. Rate limiting fine-tuning
    5. Error handling audit
    6. README + API docs
    7. `.env.example`

    ---

    ## 9. Scalability Considerations

    ### Horizontal Scaling

    | Component | Scaling Strategy |
    |---|---|
    | FastAPI | Stateless — scale behind load balancer (Uvicorn workers) |
    | Celery Workers | Add workers per queue (ingestion, workflow, repo) |
    | Redis | Redis Sentinel or Redis Cluster for HA |
    | PostgreSQL | Read replicas for query-heavy paths |
    | ChromaDB | Consider migrating to Qdrant/Weaviate at scale |

    ### Performance Optimizations

    - **Semantic Cache**: Cache LLM responses by query embedding similarity (Redis). Avoids redundant Groq API calls and saves tokens.
    - **Async Everywhere**: All I/O-bound operations (DB, HTTP, file parsing) use `async`/`await`.
    - **Connection Pooling**: SQLAlchemy async pool for PostgreSQL; `httpx.AsyncClient` pool for Groq.
    - **Chunked Streaming**: SSE responses stream tokens as they arrive — no buffering.
    - **Background Processing**: All heavy operations (ingestion, workflow execution, repo analysis) run in Celery workers, not request threads.
    - **Separated Celery Queues**: `ingestion`, `workflow`, `analysis` queues allow independent scaling.

    ### Token Efficiency

    - **Context Window Management**: Trim conversation history to fit model context; prioritize recent + high-importance messages.
    - **RAG Top-K Tuning**: Default `k=5` with reranking to minimize irrelevant context.
    - **Prompt Templates**: Lean system prompts; inject only relevant context per agent.
    - **Memory Summarization**: Periodically compress long-term memories into condensed summaries.

    ---

    ## 10. Security Considerations

    ### Authentication & Authorization

    - **JWT** with short-lived access tokens (15min) + long-lived refresh tokens (7d)
    - **Refresh token rotation**: Each refresh invalidates the previous token
    - **RBAC**: `admin`, `user`, `viewer` roles enforced at middleware level
    - **Password hashing**: `bcrypt` via `passlib`

    ### API Security

    - **Rate limiting**: Per-user, per-endpoint (Redis sliding window)
    - **Input validation**: All inputs validated via Pydantic models — no raw request data passes through
    - **CORS**: Strict origin whitelist
    - **Request size limits**: Max upload size enforced (50MB default)

    ### Data Security

    - **File storage**: Files stored server-side with UUID paths — no user-controlled filenames on disk
    - **SQL injection**: Prevented by SQLAlchemy ORM (parameterized queries)
    - **XSS**: Next.js auto-escapes; API returns JSON only
    - **Secrets management**: All secrets via environment variables, never committed

    ### LLM Security

    - **Prompt injection defense**: System prompts separated from user input; agent tools have restricted scopes
    - **Output sanitization**: LLM outputs sanitized before rendering (strip executable content)
    - **API key protection**: Groq API key server-side only, never exposed to client

    ### Infrastructure Security

    - **Docker**: Non-root containers, read-only filesystem where possible
    - **Network**: Internal services (Redis, PostgreSQL, ChromaDB) not exposed to host
    - **Health checks**: Unauthenticated health endpoints expose no sensitive data

    ---

    ## Open Questions

    > [!IMPORTANT]
    > **Embedding model choice**: The BRD doesn't specify an embedding model. Recommend `all-MiniLM-L6-v2` (fast, 384d) for dev, upgradable to `nomic-embed-text` via Groq if supported. Confirm?

    > [!IMPORTANT]
    > **File storage backend**: Store uploaded files on local disk (Docker volume) or object storage (S3/MinIO)? Local disk is simpler for dev; MinIO can be added to docker-compose for production parity.

    > [!WARNING]
    > **ChromaDB persistence**: ChromaDB's built-in persistence is adequate for moderate scale, but may become a bottleneck at high document counts (>100K chunks). Plan migration path to Qdrant if needed?

    > [!NOTE]
    > **Frontend SSR vs CSP**: Next.js 15 App Router defaults to Server Components. The AI workspace (chat) page should be a Client Component for real-time SSE. Dashboard can leverage SSR for initial load performance.
