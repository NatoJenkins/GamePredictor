"""Prediction endpoints: week, current, history."""

import pandas as pd
from fastapi import APIRouter, Depends, Query

from api.deps import get_app_state
from api.schemas import (
    PredictionResponse,
    WeekPredictionsResponse,
    PredictionHistoryResponse,
    HistorySummary,
)
from models.predict import detect_current_week

router = APIRouter()


@router.get("/api/predictions/week/{week}", response_model=WeekPredictionsResponse)
async def get_week_predictions(
    week: int,
    season: int | None = Query(
        default=None, description="Season year. Defaults to current season."
    ),
    state: dict = Depends(get_app_state),
):
    """Return predictions for a specific week.

    API-01: GET /predictions/week/{week} returns predicted winner
    and confidence score per game for the specified week.
    """
    engine = state["engine"]

    # Default season = current season (max season in schedules)
    if season is None:
        result = pd.read_sql(
            "SELECT MAX(season) as max_season FROM schedules WHERE game_type = 'REG'",
            engine,
        )
        season = int(result["max_season"].iloc[0])

    # Query predictions for this week
    query = """
        SELECT game_id, season, week, game_date, home_team, away_team,
               predicted_winner, confidence, confidence_tier,
               actual_winner, correct
        FROM predictions
        WHERE season = %(season)s AND week = %(week)s
        ORDER BY game_date, game_id
    """
    df = pd.read_sql(query, engine, params={"season": season, "week": week})

    predictions = []
    for _, row in df.iterrows():
        predictions.append(
            PredictionResponse(
                game_id=row["game_id"],
                season=int(row["season"]),
                week=int(row["week"]),
                game_date=(
                    str(row["game_date"]) if pd.notna(row["game_date"]) else None
                ),
                home_team=row["home_team"],
                away_team=row["away_team"],
                predicted_winner=row["predicted_winner"],
                confidence=float(row["confidence"]),
                confidence_tier=row["confidence_tier"],
                actual_winner=(
                    row["actual_winner"]
                    if pd.notna(row.get("actual_winner"))
                    else None
                ),
                correct=(
                    bool(row["correct"]) if pd.notna(row.get("correct")) else None
                ),
            )
        )

    return WeekPredictionsResponse(
        season=season,
        week=week,
        status="ok",
        predictions=predictions,
    )


@router.get("/api/predictions/current", response_model=WeekPredictionsResponse)
async def get_current_predictions(state: dict = Depends(get_app_state)):
    """Convenience endpoint that auto-resolves to the current unplayed week.

    Returns offseason status when no unplayed games exist.
    """
    engine = state["engine"]
    current = detect_current_week(engine)

    if current is None:
        return WeekPredictionsResponse(
            season=0,
            week=0,
            status="offseason",
            predictions=[],
        )

    current_season, current_week = current
    return await get_week_predictions(
        week=current_week,
        season=current_season,
        state=state,
    )


@router.get("/api/predictions/history", response_model=PredictionHistoryResponse)
async def get_prediction_history(
    season: int | None = Query(
        default=None, description="Filter by season. Defaults to current season."
    ),
    team: str | None = Query(
        default=None,
        description="Filter by team abbreviation (e.g., KC, BUF).",
    ),
    state: dict = Depends(get_app_state),
):
    """Return past predictions with actual outcomes and summary stats.

    API-02: GET /predictions/history returns all past predictions
    with actual outcomes. Includes summary object with correct/total/accuracy.
    """
    engine = state["engine"]

    # Default season = current season
    if season is None:
        result = pd.read_sql(
            "SELECT MAX(season) as max_season FROM schedules WHERE game_type = 'REG'",
            engine,
        )
        season = int(result["max_season"].iloc[0])

    # Build query with optional team filter
    query = """
        SELECT game_id, season, week, game_date, home_team, away_team,
               predicted_winner, confidence, confidence_tier,
               actual_winner, correct
        FROM predictions
        WHERE season = %(season)s AND actual_winner IS NOT NULL
    """
    params: dict = {"season": season}

    if team:
        query += " AND (home_team = %(team)s OR away_team = %(team)s)"
        params["team"] = team.upper()

    query += " ORDER BY week, game_date, game_id"
    df = pd.read_sql(query, engine, params=params)

    predictions = []
    for _, row in df.iterrows():
        predictions.append(
            PredictionResponse(
                game_id=row["game_id"],
                season=int(row["season"]),
                week=int(row["week"]),
                game_date=(
                    str(row["game_date"]) if pd.notna(row["game_date"]) else None
                ),
                home_team=row["home_team"],
                away_team=row["away_team"],
                predicted_winner=row["predicted_winner"],
                confidence=float(row["confidence"]),
                confidence_tier=row["confidence_tier"],
                actual_winner=row["actual_winner"],
                correct=bool(row["correct"]),
            )
        )

    # Summary stats
    total = len(predictions)
    correct_count = sum(1 for p in predictions if p.correct)
    accuracy = correct_count / total if total > 0 else None

    return PredictionHistoryResponse(
        predictions=predictions,
        summary=HistorySummary(
            correct=correct_count, total=total, accuracy=accuracy
        ),
    )
