# Tech Stack Decisions

## Decision Summary

| Layer | Choice | Why This Choice | Alternative Considered |
|---|---|---|---|
| Backend API | Python 3.12 + FastAPI | Fast iteration, typed models, strong ecosystem | Node + NestJS |
| Data models | Pydantic v2 + SQLModel/SQLAlchemy | Schema safety and serialization control | Django ORM |
| Database | PostgreSQL | Reliable relational model for workflows/runs | MySQL |
| Queue | Redis + RQ/Dramatiq worker | Simple, free, good enough for MVP | Celery |
| Frontend | React + TypeScript + Vite | Fast UI build and simple deployment | Next.js |
| AI provider | Ollama adapter (local) | Free local inference and privacy | Hosted API only |
| Auth (MVP) | Single admin or local auth | Reduce complexity in phase 1 | Full multi-tenant auth |
| Infra | Docker Compose | Easy local reproducibility | Kubernetes |

## Why Not Temporal Right Now
Temporal is powerful but adds operational complexity for first release. We start with a simpler event-driven engine, then migrate if workflow complexity exceeds current model.

## Free-First Principle
- All core runtime components are open-source.
- Paid providers are optional adapters, not hard dependencies.
