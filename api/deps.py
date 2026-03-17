"""Dependency injection for FastAPI application."""

# Mutable app state dict -- loaded at startup, updated on reload
app_state: dict = {}


def get_app_state() -> dict:
    """FastAPI dependency that returns the shared app state.

    State keys (populated by lifespan):
    - "model": XGBClassifier instance
    - "model_info": dict from get_best_experiment()
    - "engine": SQLAlchemy engine
    """
    return app_state
