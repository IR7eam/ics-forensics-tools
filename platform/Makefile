.PHONY: backend backend-dev init-db test-backend frontend frontend-build

BACKEND_DIR=backend

backend:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir $(BACKEND_DIR)

backend-dev:
python -m app.main --debug

init-db:
python -m app.main --init-db

test-backend:
cd backend && pytest -q

frontend:
cd frontend && npm run dev -- --host

frontend-build:
cd frontend && npm run build
