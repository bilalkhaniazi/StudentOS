FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 libgomp1 libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

COPY api /app/api
COPY pipeline /app/pipeline
COPY data /app/data

ENV PYTHONPATH=/app
ENV API_HOST=0.0.0.0
ENV API_PORT=43124

EXPOSE 43124

CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "43124"]
