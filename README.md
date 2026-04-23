# CodeStash Starterpack

A reusable full-stack starter template written as a clean generic base for any domain.

## Stack

- Backend: FastAPI + SQLAlchemy (async) + PostgreSQL
- Frontend: React + TypeScript + Vite
- Infra: Terraform (DigitalOcean modules)
- CI/CD: GitHub Actions (backend, frontend, terraform checks)

## Project Layout

- `backend/` FastAPI API service
- `frontend/` React application
- `terraform/` IaC for droplet, firewall, and project setup
- `.github/workflows/` CI and Terraform workflows

## Quick Start

1. Copy env files:
   - `cp backend/.env.example backend/.env`
   - `cp frontend/.env.example frontend/.env`
2. Start local stack:
   - `docker compose up --build`
3. Open:
   - Frontend: `http://localhost:5173`
   - Backend docs: `http://localhost:8000/docs`

## Notes

- Replace all placeholder values before production use.
- Terraform is configured for DigitalOcean by default; adapt provider or modules as needed.
