"""Tests for /api/predictions/spreads/* endpoints."""


def test_get_spread_week(client):
    """GET /api/predictions/spreads/week/{season}/{week} returns 200 with predictions."""
    response = client.get("/api/predictions/spreads/week/2024/1")
    assert response.status_code == 200
    data = response.json()
    assert data["season"] == 2024
    assert data["week"] == 1
    assert data["status"] == "ok"
    assert isinstance(data["predictions"], list)
    assert len(data["predictions"]) == 2


def test_get_spread_week_prediction_fields(client):
    """Spread prediction contains all required fields."""
    response = client.get("/api/predictions/spreads/week/2024/1")
    pred = response.json()["predictions"][0]
    assert "game_id" in pred
    assert "predicted_spread" in pred
    assert "predicted_winner" in pred
    assert isinstance(pred["predicted_spread"], float)
    assert pred["actual_spread"] is None
    assert pred["actual_winner"] is None
    assert pred["correct"] is None


def test_spread_503_no_model(no_spread_client):
    """Spread endpoint returns 503 when spread model is not loaded."""
    response = no_spread_client.get("/api/predictions/spreads/week/2024/1")
    assert response.status_code == 503
    assert "Spread model not loaded" in response.json()["detail"]


def test_startup_without_spread_model(no_spread_client):
    """API starts and serves classifier endpoints when spread model is missing."""
    # Classifier endpoint should still work
    response = no_spread_client.get("/api/predictions/week/1?season=2024")
    assert response.status_code == 200
