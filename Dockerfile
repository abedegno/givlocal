FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
COPY givenergy_modbus_async/ givenergy_modbus_async/
COPY settings/ settings/
COPY config.example.yaml config.example.yaml
RUN pip install --no-cache-dir .
EXPOSE 8099
CMD ["uvicorn", "givenergy_local.main:app", "--host", "0.0.0.0", "--port", "8099"]
