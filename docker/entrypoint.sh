#!/bin/sh
# Seed models volume on first boot if volume is empty
MODEL_VOL="/app/models-vol"
if [ ! -f "$MODEL_VOL/best_model.json" ]; then
    echo "[entrypoint] Seeding classifier models volume from image..."
    cp /app/models/artifacts/best_model.json "$MODEL_VOL/"
    cp /app/models/experiments.jsonl "$MODEL_VOL/"
    echo "[entrypoint] Classifier seeding complete."
fi
# Seed spread artifacts separately (handles v1.0 -> v1.1 upgrade)
if [ ! -f "$MODEL_VOL/best_spread_model.json" ]; then
    echo "[entrypoint] Seeding spread model artifacts from image..."
    cp /app/models/artifacts/best_spread_model.json "$MODEL_VOL/"
    cp /app/models/spread_experiments.jsonl "$MODEL_VOL/"
    echo "[entrypoint] Spread seeding complete."
fi
exec "$@"
