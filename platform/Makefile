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

.PHONY: seed-assets
seed-assets:
@echo "Seeding sample assets into running backend..."
@TOKEN=$$(curl -s -X POST -d "username=analyst&password=analyst" http://localhost:8000/api/auth/token | jq -r .access_token);
@if [ "$$TOKEN" = "null" ] || [ -z "$$TOKEN" ]; then echo "Failed to obtain analyst token"; exit 1; fi
@curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Authorization: Bearer $$TOKEN" \
  -F "file=@docs/sample_assets.csv" \
  http://localhost:8000/api/assets/import || true

.PHONY: compose-up compose-down

compose-up:
docker compose -f docker-compose.yml up --build

compose-down:
docker compose -f docker-compose.yml down
