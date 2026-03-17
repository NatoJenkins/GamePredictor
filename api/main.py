"""FastAPI application with lifespan model loading and CORS."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.deps import app_state
from api.routes import predictions, model, experiments, health
from models.predict import load_best_model, get_best_experiment
from data.db import get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model and metadata at startup, cleanup on shutdown."""
    # Startup
    app_state["engine"] = get_engine()
    app_state["model"] = load_best_model(settings.MODEL_PATH)
    app_state["model_info"] = get_best_experiment(settings.EXPERIMENTS_PATH)
    yield
    # Shutdown
    app_state.clear()


app = FastAPI(
    title="NFL Game Predictor API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(predictions.router)
app.include_router(model.router)
app.include_router(experiments.router)
app.include_router(health.router)
