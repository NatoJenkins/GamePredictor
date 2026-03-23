"""Dependency injection for FastAPI application."""

# Mutable app state dict -- loaded at startup, updated on reload
app_state: dict = {}


def get_app_state() -> dict:
    """FastAPI dependency that returns the shared app state.

    State keys (populated by lifespan):
    - "model": XGBClassifier instance (or None)
    - "model_info": dict from get_best_experiment() (or None)
    - "engine": SQLAlchemy engine
    - "spread_model": XGBRegressor instance (or None)
    - "spread_model_info": dict from get_best_spread_experiment() (or None)
    """
    return app_state
