"""Tests for /api/model/* endpoints."""

import pytest


def test_model_info(client):
    """GET /api/model/info returns 200 with experiment metadata."""
    response = client.get("/api/model/info")
    assert response.status_code == 200
    data = response.json()
    assert data["experiment_id"] == 1
    assert "training_date" in data
    assert "val_accuracy_2023" in data


def test_model_info_baselines(client):
    """Response includes both baseline accuracy fields."""
    response = client.get("/api/model/info")
    data = response.json()
    assert "baseline_always_home" in data
    assert "baseline_better_record" in data
    assert data["baseline_always_home"] == 0.5551
    assert data["baseline_better_record"] == 0.5820


def test_reload(client):
    """POST /api/model/reload with valid token returns 200 with reloaded status."""
    response = client.post(
        "/api/model/reload",
        headers={"X-Reload-Token": "test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reloaded"
    assert "experiment_id" in data
    assert "val_accuracy_2023" in data
    assert "predictions_generated" in data


def test_reload_auth(client):
    """POST /api/model/reload without token returns 422 (missing required header)."""
    response = client.post("/api/model/reload")
    assert response.status_code == 422


def test_reload_bad_token(client):
    """POST /api/model/reload with wrong token returns 403."""
    response = client.post(
        "/api/model/reload",
        headers={"X-Reload-Token": "wrong-token"},
    )
    assert response.status_code == 403


def test_model_info_spread_model(client):
    """GET /api/model/info includes spread_model metadata when loaded."""
    response = client.get("/api/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "spread_model" in data
    assert data["spread_model"] is not None
    assert data["spread_model"]["mae"] == pytest.approx(10.6826)
    assert data["spread_model"]["rmse"] == pytest.approx(13.8711)
    assert data["spread_model"]["derived_win_accuracy"] == pytest.approx(0.6016)
    assert "training_date" in data["spread_model"]
    assert data["spread_model"]["experiment_id"] == 1


def test_model_info_spread_model_null(no_spread_client):
    """GET /api/model/info returns spread_model: null when not loaded."""
    response = no_spread_client.get("/api/model/info")
    assert response.status_code == 200
    data = response.json()
    assert data["spread_model"] is None


def test_reload_includes_spread_fields(client):
    """POST /api/model/reload response includes spread fields."""
    response = client.post(
        "/api/model/reload",
        headers={"X-Reload-Token": "test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "spread_experiment_id" in data
    assert "spread_mae" in data
    assert "spread_predictions_generated" in data
