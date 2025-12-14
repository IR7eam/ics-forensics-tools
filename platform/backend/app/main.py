import argparse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    analysis,
    assets,
    baselines,
    events,
    observations,
    scan_jobs,
    auth,
    evidence,
    evidence_links,
    reports,
    audit,
    plugins,
    rules,
)
from pathlib import Path

from app.core.config import get_settings
from app.db.session import init_db

settings = get_settings()

Path(settings.report_dir).mkdir(parents=True, exist_ok=True)
Path(settings.evidence_dir).mkdir(parents=True, exist_ok=True)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(assets.router, prefix=settings.api_prefix)
app.include_router(scan_jobs.router, prefix=settings.api_prefix)
app.include_router(observations.router, prefix=settings.api_prefix)
app.include_router(evidence.router, prefix=settings.api_prefix)
app.include_router(evidence_links.router, prefix=settings.api_prefix)
app.include_router(events.router, prefix=settings.api_prefix)
app.include_router(baselines.router, prefix=settings.api_prefix)
app.include_router(analysis.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)
app.include_router(audit.router, prefix=settings.api_prefix)
app.include_router(plugins.router, prefix=settings.api_prefix)
app.include_router(rules.router, prefix=settings.api_prefix)


@app.get("/")
def healthcheck():
    return {"status": "ok", "app": settings.app_name}


def main():
    parser = argparse.ArgumentParser(description="ICS Forensics Platform backend")
    parser.add_argument("--init-db", action="store_true", help="Initialize database tables")
    parser.add_argument("--debug", action="store_true", help="Debug mode")
    args = parser.parse_args()

    if args.init_db:
        init_db()
        print("Database initialized")


if __name__ == "__main__":
    main()
