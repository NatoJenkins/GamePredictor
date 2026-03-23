"""FastAPI application with lifespan model loading and CORS."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import settings
from api.deps import app_state
from api.routes import predictions, model, experiments, health, spreads
from models.predict import load_best_model, get_best_experiment, load_best_spread_model, get_best_spread_experiment
from data.db import get_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model and metadata at startup, cleanup on shutdown."""
    # Startup
    app_state["engine"] = get_engine()
    try:
        app_state["model"] = load_best_model(settings.MODEL_PATH)
    except FileNotFoundError:
        app_state["model"] = None
    try:
        app_state["model_info"] = get_best_experiment(settings.EXPERIMENTS_PATH)
    except FileNotFoundError:
        app_state["model_info"] = None
    # Spread model (graceful degradation -- API continues if missing)
    try:
        app_state["spread_model"] = load_best_spread_model(settings.SPREAD_MODEL_PATH)
    except FileNotFoundError:
        app_state["spread_model"] = None
    try:
        app_state["spread_model_info"] = get_best_spread_experiment(settings.SPREAD_EXPERIMENTS_PATH)
    except FileNotFoundError:
        app_state["spread_model_info"] = None
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
app.include_router(spreads.router)
