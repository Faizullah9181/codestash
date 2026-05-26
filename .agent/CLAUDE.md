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
    api/
      health.py        # /api/status + /api/health
      items.py         # example controller (thin HTTP layer)
      crud.py          # (legacy) generic CRUD helper — prefer repository/service pattern
      schemas.py       # Pydantic base schemas + PaginatedResponse
    db/
      connection.py    # async engine, session maker, get_db dependency
      models.py        # SQLAlchemy Base + models (Item, etc.)
    repositories/
      base.py          # BaseRepository — paginated list, get, create, update, delete
      item_repository.py  # Item-specific data access (extends BaseRepository)
    services/
      item_service.py  # Item business logic (controller → service → repository → model)
  Makefile           # install | dev | test | lint
  pyproject.toml

frontend/
  src/
    lib/api.ts       # typed fetch helpers (apiGet/Post/Put/Patch/Delete)
    hooks/
      useApi.ts       # fetch-once hook with loading/error/refetch
      usePaginatedApi.ts  # auto-loading paginated list hook
    components/
      Layout.tsx      # sidebar + content shell
      StatusStates.tsx  # LoadingSpinner, ErrorBox, EmptyState, LoadMoreButton
      ErrorBoundary.tsx  # React error boundary with retry
      Form.tsx        # FormInput, FormSelect, FormTextarea, FormCheckbox
    pages/
      Home.tsx        # dashboard with system status
      Items.tsx       # full CRUD example with search + create/edit modals
    App.tsx           # BrowserRouter + routes
    main.tsx          # React root
    index.css         # design tokens + utility classes
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
- All routes go under `/api` via FastAPI routers. Register new ones in `app/main.py`.
- DB session via `get_db` dependency. Models inherit from `app.db.models.Base` (gives id + timestamps).
- **Architecture: Controller → Service → Repository → Model**
  - `app/api/*.py` — thin controllers: validate request, call service, return response
  - `app/services/*.py` — business logic: transforms, rules, orchestration
  - `app/repositories/*.py` — data access: all SQLAlchemy queries go here
  - `app/db/models.py` — SQLAlchemy models only
- Pydantic schemas in `app/api/schemas.py` — inherit `SchemaBase` for responses, `CreateBase`/`UpdateBase` for requests.
- Controllers use dependency injection (`Depends(get_db)`) and call service singletons.

**Frontend**
- API calls use typed helpers from `src/lib/api.ts`: `apiGet<T>`, `apiPost<T>`, `apiPut<T>`, `apiPatch<T>`, `apiDelete<T>`.
- Pagination hook: `usePaginatedApi<T>(fetcher, deps)`. Single-fetch hook: `useApi<T>(fetcher, deps)`.
- UI components: `Layout`, `LoadingSpinner`, `ErrorBox`, `EmptyState`, `LoadMoreButton`, `ErrorBoundary`.
- Form components: `FormInput`, `FormSelect`, `FormTextarea`, `FormCheckbox`.
- Design tokens defined in `index.css` under `:root` — use `var(--accent)`, `var(--card)`, etc.
- In dev, all `/api/*` requests proxy to `:8000` (configured in `vite.config.ts`). In prod, set `VITE_API_URL`.
- `@/` path alias is configured (e.g., `import { useApi } from "@/hooks"`)

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
| `skill-forge` | Create new agent skills with SKILL.md generation |
| `bug-hunt` | Systematic bug diagnosis via HITL loop |
| `doc-drill` | Grill an agent on a codebase area using CONTEXT.md + ADRs |
| `arch-review` | Find shallow modules and propose deepening via parallel sub-agents |
| `agent-setup` | Generate `## Agent skills` block + `docs/agents/` config for this repo |
| `test-cycle` | TDD workflow: planning → tracer bullet → incremental RED→GREEN→REFACTOR |
| `feature-split` | Convert a feature/PRD into vertical-slice issues with dependency order |
| `issue-triage` | Triage an issue through state machine → label + AGENT-BRIEF rewrite |
| `module-map` | Map relevant modules and callers at a higher abstraction level |
| `skill-scaffold` | Create a new skill with correct frontmatter and reference files |
| `git-safety` | Install pre-tool-call hook blocking dangerous git commands |
| `precommit-setup` | Install husky + lint-staged + prettier pre-commit hook |
