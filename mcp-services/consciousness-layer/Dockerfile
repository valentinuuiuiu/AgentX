FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic

COPY server.py /app/

EXPOSE 3000

CMD ["python", "server.py"]