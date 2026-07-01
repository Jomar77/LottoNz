"""FastAPI app entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import CORS_ORIGINS
from api.deps import get_data
from api.routers import strategies, strategies_weighted, weighted


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_data()  # warm cache at startup
    yield


_DESCRIPTION = """
Generate NZ Lotto number sets using two distinct engines.

> **Entertainment only.** NZ Lotto draws are independent, uniform-random events.
> Nothing here carries predictive edge over a random quick-pick.

## Endpoints

| Endpoint | What it does |
|---|---|
| `GET /predict/weighted` | Frequency-weighted tickets with lean / spread / consecutive constraints |
| `GET /predict/strategies` | Five algorithm-distinct strategy sets, optionally filtered by date window (constraints advisory only) |
| `GET /predict/strategies/weighted` | Same five strategy sets, with lean / spread / consecutive constraints enforced via minimal-swap repair |
| `GET /health` | Sanity check — confirms data is loaded |

## Interactive docs
Use the **Try it out** button on any endpoint below to call the live API.
"""

_TAGS: list[dict] = [
    {
        "name": "predict",
        "description": "Number generation endpoints.",
    },
    {
        "name": "system",
        "description": "Health and diagnostics.",
    },
]

app = FastAPI(
    title="LottoNZ Prediction API",
    description=_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
    allow_credentials=False,
)

app.include_router(weighted.router)
app.include_router(strategies.router)
app.include_router(strategies_weighted.router)


@app.get("/health", tags=["system"], summary="Health check")
def health() -> dict:
    """Returns `ok` and the number of historical draws currently loaded in memory."""
    df, _ = get_data()
    return {"status": "ok", "draws_loaded": len(df)}
