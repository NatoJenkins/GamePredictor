FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml ./
COPY . .
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
