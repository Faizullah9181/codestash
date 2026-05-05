# Project Memory

Shared agent instructions for the codestash-starterpack workspace.

---

## Stack

| Layer | Tech | Version |
|-------|------|---------|
| Backend | FastAPI + SQLAlchemy (async) + asyncpg | Python ≥ 3.12 |
| Database | PostgreSQL 16 | via Docker |
| Frontend | React 19 + TypeScript 5.6 + Vite 6 | Node LTS |
| Infra | Terraform ≥ 1.6 + DigitalOcean provider ~> 2.68 | |
| Package mgr | `uv` (backend), `npm` (frontend) | |
| Linting | `ruff` (backend), `eslint` (frontend) | |

---

## Project Layout

```
backend/
  app/
    main.py          # FastAPI app, CORS, lifespan, /health
    config.py        # pydantic-settings — reads from .env
    api/routes.py    # APIRouter mounted at /api
    db/              # empty — add models + session here
  Makefile           # install | dev | test | lint
  pyproject.toml

frontend/
  src/
    lib/api.ts       # typed fetch helpers (apiGet<T>)
    App.tsx
    components/      # add shared UI here
  vite.config.ts

terraform/
  main.tf            # root — feature-flagged module calls + locals
  variables.tf       # create_* bools + resource config vars
  outputs.tf
  versions.tf        # required_version >= 1.6.0, DO ~> 2.68
  modules/
    droplet/         # digitalocean_droplet.this
    firewall/        # digitalocean_firewall.this
    project/         # digitalocean_project.this (groups URNs)

.agent/
  CLAUDE.md          # this file
  skills/
    tf-add/                  # generic Terraform skill v2.0.0
    skill-forge/
    bug-hunt/
    doc-drill/
    arch-review/
    agent-setup/
    test-cycle/
    feature-split/
    issue-triage/
    module-map/
    skill-scaffold/
    git-safety/
    precommit-setup/
    skill.update.py  # list | check | bump <skill> | sync
```

---

## Dev Commands

```bash
# Backend
cd backend && uv sync           # install deps
cd backend && make dev          # uvicorn on :8000 with --reload
cd backend && make test         # pytest -q
cd backend && make lint         # ruff check

# Frontend
cd frontend && npm install
cd frontend && npm run dev      # vite on :5173
cd frontend && npm run build    # tsc + vite build
cd frontend && npm run lint

# Full stack (Docker)
docker compose up --build       # db :5432, backend :8000, frontend :5173
```

---

## Key Conventions

**Backend**
- Settings live in `app/config.py` (`pydantic-settings`). All env vars go there — never read `os.environ` directly.
- Default DB URL: `postgresql+asyncpg://codestash:codestash@localhost:5432/codestash`
- CORS origins controlled by `CORS_ORIGINS` env var (comma-separated).
- All routes go under `/api` via `app/api/routes.py`. Register new routers with `router.include_router(...)`.
- DB session + models go in `app/db/` (currently empty — scaffold there).

**Frontend**
- API calls use `apiGet<T>(path)` from `src/lib/api.ts`. Add `apiPost`, `apiPut`, etc. in the same file.
- In dev, all `/api/*` requests proxy to `:8000` (configured in `vite.config.ts`). In prod, set `VITE_API_URL`.
- Components go in `src/components/`.

**Terraform**
- Every resource is feature-flagged: `create_<name>` bool in `variables.tf`, `count = var.create_<name> ? 1 : 0` in module call.
- Every module emits `id` + `urn` outputs minimum. URNs collected in `local.resources` for DO project assignment.
- Naming: module dirs `lowercase-hyphens`, resource label `this` for singletons.
- Use the `tf-add` skill when adding or wiring new resources.

**Skills**
- Run `python .agent/skills/skill.update.py check` to validate skill frontmatter.
- Run `python .agent/skills/skill.update.py list` to see all skills + versions.

---

## Agent skills

| Skill | What it does |
|---|---|
| `tf-add` | Add or wire Terraform resources (DigitalOcean, generic) |
| `skill-forge` | Create new agent skills with SKILL.md scaffolding |
| `bug-hunt` | Systematic bug diagnosis via HITL loop |
| `doc-drill` | Grill an agent on a codebase area using CONTEXT.md + ADRs |
| `arch-review` | Find shallow modules and propose deepening via parallel sub-agents |
| `agent-setup` | Scaffold `## Agent skills` block + `docs/agents/` config for this repo |
| `test-cycle` | TDD workflow: planning → tracer bullet → incremental RED→GREEN→REFACTOR |
| `feature-split` | Convert a feature/PRD into vertical-slice issues with dependency order |
| `issue-triage` | Triage an issue through state machine → label + AGENT-BRIEF rewrite |
| `module-map` | Map relevant modules and callers at a higher abstraction level |
| `skill-scaffold` | Create a new skill with correct frontmatter and reference files |
| `git-safety` | Install pre-tool-call hook blocking dangerous git commands |
| `precommit-setup` | Install husky + lint-staged + prettier pre-commit hook |
