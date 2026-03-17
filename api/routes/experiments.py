"""Experiments endpoint -- reads experiments.jsonl directly."""

import json

from fastapi import APIRouter, HTTPException

from api.config import settings
from api.schemas import ExperimentResponse

router = APIRouter()


@router.get("/api/experiments", response_model=list[ExperimentResponse])
async def list_experiments():
    """Return all experiments from experiments.jsonl.

    File is the single source of truth (CONTEXT.md).
    Parsed on every request -- at 20-30 experiments this is negligible.
    """
    try:
        experiments = []
        with open(settings.EXPERIMENTS_PATH) as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    experiments.append(ExperimentResponse(**entry))
        return experiments
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="experiments.jsonl not found")
