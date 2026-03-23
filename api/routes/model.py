"""Model info and reload endpoints."""

from fastapi import APIRouter, Depends, Header, HTTPException

from api.config import settings, get_confidence_tier
from api.deps import get_app_state
from api.schemas import ModelInfoResponse, ReloadResponse, SpreadModelInfo
from models.predict import (
    load_best_model,
    get_best_experiment,
    detect_current_week,
    generate_predictions,
    load_best_spread_model,
    get_best_spread_experiment,
    generate_spread_predictions,
)

router = APIRouter()


@router.get("/api/model/info", response_model=ModelInfoResponse)
async def model_info(state: dict = Depends(get_app_state)):
    """Return current model metadata.

    API-03: GET /model/info returns current model version, training date,
    and 2023 validation accuracy. Also includes feature count, hypothesis,
    and both baseline accuracies per CONTEXT.md.
    """
    info = state.get("model_info")
    if info is None:
        raise HTTPException(status_code=503, detail="No model loaded")

    # Build spread model info if available
    spread_info = state.get("spread_model_info")
    spread_model_data = None
    if spread_info is not None:
        spread_model_data = SpreadModelInfo(
            mae=spread_info["mae_2023"],
            rmse=spread_info["rmse_2023"],
            derived_win_accuracy=spread_info["derived_win_accuracy_2023"],
            training_date=spread_info["timestamp"],
            experiment_id=spread_info["experiment_id"],
        )

    return ModelInfoResponse(
        experiment_id=info["experiment_id"],
        training_date=info["timestamp"],
        val_accuracy_2023=info["val_accuracy_2023"],
        feature_count=len(info["features"]),
        hypothesis=info["hypothesis"],
        baseline_always_home=info["baseline_always_home"],
        baseline_better_record=info["baseline_better_record"],
        spread_model=spread_model_data,
    )


@router.post("/api/model/reload", response_model=ReloadResponse)
async def reload_model(
    state: dict = Depends(get_app_state),
    x_reload_token: str = Header(
        ..., description="Reload authorization token"
    ),
):
    """Hot-swap the serving model and regenerate current week predictions.

    API-04: POST /model/reload hot-swaps the serving model after manual approval.
    Requires X-Reload-Token header matching RELOAD_TOKEN env var.

    Steps:
    1. Validate token
    2. Load new model from artifact path
    3. Re-parse experiments.jsonl for updated metadata
    4. Detect current week
    5. Regenerate predictions for current week
    6. Update app state
    """
    # Step 1: Validate token
    if not settings.RELOAD_TOKEN or x_reload_token != settings.RELOAD_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid reload token")

    # Step 2: Load new model
    try:
        new_model = load_best_model(settings.MODEL_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Model artifact not found")

    # Step 3: Re-parse experiment metadata
    new_info = get_best_experiment(settings.EXPERIMENTS_PATH)
    if new_info is None:
        raise HTTPException(status_code=500, detail="No kept experiments found")

    # Step 4: Detect current week
    engine = state["engine"]
    current = detect_current_week(engine)

    # Step 5: Regenerate predictions if there's a current week
    predictions_count = 0
    if current is not None:
        current_season, current_week = current
        preds = generate_predictions(
            new_model,
            current_season,
            current_week,
            engine,
            get_confidence_tier,
            model_id=new_info["experiment_id"],
        )
        predictions_count = len(preds)

    # Step 6: Update app state
    state["model"] = new_model
    state["model_info"] = new_info

    # Reload spread model (graceful -- continues if missing)
    spread_experiment_id = None
    spread_mae = None
    spread_preds_count = 0
    try:
        new_spread_model = load_best_spread_model(settings.SPREAD_MODEL_PATH)
        new_spread_info = get_best_spread_experiment(settings.SPREAD_EXPERIMENTS_PATH)
        state["spread_model"] = new_spread_model
        state["spread_model_info"] = new_spread_info

        # Generate spread predictions for current week if available
        if current is not None and new_spread_info is not None:
            spread_preds = generate_spread_predictions(
                new_spread_model,
                current_season,
                current_week,
                engine,
                model_id=new_spread_info["experiment_id"],
            )
            spread_preds_count = len(spread_preds)

        if new_spread_info is not None:
            spread_experiment_id = new_spread_info["experiment_id"]
            spread_mae = new_spread_info["mae_2023"]
    except FileNotFoundError:
        state["spread_model"] = None
        state["spread_model_info"] = None

    return ReloadResponse(
        status="reloaded",
        experiment_id=new_info["experiment_id"],
        val_accuracy_2023=new_info["val_accuracy_2023"],
        predictions_generated=predictions_count,
        spread_experiment_id=spread_experiment_id,
        spread_mae=spread_mae,
        spread_predictions_generated=spread_preds_count,
    )
