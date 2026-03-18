FROM ghcr.io/mlflow/mlflow:2.21.3
RUN pip install --no-cache-dir psycopg2-binary
