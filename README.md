# Project 2 - AI Business Process Automation Tool

## Goal
Build a free, self-hostable platform that converts natural language business instructions into reliable automated workflows.

Example input:
"When a new client signs up, create a CRM entry and send a welcome email."

The system parses intent, generates a validated workflow definition, and executes it with observability and retries.

## Current Status
- Planning complete.
- Phases 1-6 implemented in code (backend, runtime, connectors, frontend, security, CI).

## Quick Start
1. Copy environment file:
   - `cp .env.example .env` (Linux/macOS)
   - `Copy-Item .env.example .env` (PowerShell)
2. Start local stack:
   - `docker-compose up --build`
3. Check backend health:
   - `http://localhost:8000/health`
4. Open frontend:
   - `http://localhost:5173`
5. Use API key:
   - Header `X-API-Key: dev-api-key` (change in `.env` for production)

## Stack
- Backend: Python + FastAPI
- Runtime: Redis queue worker + PostgreSQL
- Frontend: React + TypeScript + Vite
- Local infra: Docker Compose
- AI planning: Ollama adapter + deterministic fallback

## Implemented Capabilities
- Prompt -> validated workflow JSON generation (`/api/v1/planner/generate`).
- Workflow CRUD, versioning, and activation.
- Trigger ingestion (`manual` and `webhook`) and run creation.
- Step runtime with dependency resolution, retries, and dead-letter status.
- Connectors: internal CRM, SMTP email, HTTP request action.
- Run history and step timeline APIs.
- Frontend workflow studio for generation/review/activation/runs/connectors.
- API key auth, encrypted connector config storage, and audit events.

## Project Docs
- [Product brief](docs/00-product-brief.md)
- [Architecture](docs/01-architecture.md)
- [Tech stack](docs/02-tech-stack.md)
- [Workflow spec](docs/03-workflow-spec.md)
- [Roadmap](docs/04-mvp-roadmap.md)
- [Repository structure](docs/05-repository-structure.md)
- [Risk and security](docs/06-risk-security.md)
- [Testing strategy](docs/07-testing-strategy.md)
- [Build checklist](docs/08-build-checklist.md)
- [Phase completion report](docs/09-phase-completion.md)
