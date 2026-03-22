#!/bin/sh
# Seed models volume on first boot if volume is empty
MODEL_VOL="/app/models-vol"
if [ ! -f "$MODEL_VOL/best_model.json" ]; then
    echo "[entrypoint] Seeding models volume from image..."
    cp /app/models/artifacts/best_model.json "$MODEL_VOL/"
    cp /app/models/experiments.jsonl "$MODEL_VOL/"
    echo "[entrypoint] Seeding complete."
fi
exec "$@"
