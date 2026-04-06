import os

from fastapi import FastAPI

from app.routers import health, spaces, pages

app = FastAPI(
    title="Docmost Database API",
    description="REST API for live Docmost PostgreSQL data. Exposes spaces and pages with normalized text content.",
    version="1.0.0",
)

app.include_router(health.router)
app.include_router(spaces.router)
app.include_router(pages.router)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("LISTEN_HOST", "0.0.0.0")
    port = int(os.getenv("LISTEN_PORT", "8099"))
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
