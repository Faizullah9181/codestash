# Project Memory

Instructions here apply to this project and are shared with team members.

## Context

This is a generic full-stack starter workspace designed for reuse.

### Architecture Overview

| Area | Stack | Purpose |
|------|-------|---------|
| Backend | FastAPI + SQLAlchemy async | HTTP APIs and business logic |
| Frontend | React + TypeScript + Vite | Web application UI |
| Infra | Terraform | Cloud provisioning templates |
| CI/CD | GitHub Actions | Build, test, and validation pipelines |

### Key Patterns

1. API-first backend design
2. Type-safe frontend contracts
3. Environment-based configuration
4. Containerized local development
5. Infrastructure as code via modules

### Build Commands

- Backend install: `cd backend && uv sync`
- Backend run: `cd backend && make dev`
- Frontend install: `cd frontend && npm install`
- Frontend run: `cd frontend && npm run dev`
- Full stack: `docker compose up --build`

## Active Context

<!-- Current session context -->

## Recent Changes

<!-- Important project changes -->
