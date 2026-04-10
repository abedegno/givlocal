FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
COPY settings/ settings/
COPY config.example.yaml config.example.yaml
RUN pip install --no-cache-dir .

EXPOSE 8099
CMD ["uvicorn", "givlocal.main:app", "--host", "0.0.0.0", "--port", "8099"]
