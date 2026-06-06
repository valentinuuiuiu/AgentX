FROM python:3.11-slim

WORKDIR /app

# Install system deps + git for pip install
RUN apt-get update && apt-get install -y curl git && rm -rf /var/lib/apt/lists/*

# Install service deps first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Install TradingAgents at runtime from mounted volume or pip
ENV PYTHONPATH=/app:/app/tradingagents_lib
ENV PYTHONUNBUFFERED=1
ENV MCP_SERVER_NAME=trading-agents

# Install TradingAgents if the volume is available at startup
CMD ["sh", "-c", "if [ -d /app/tradingagents_lib ] && [ -f /app/tradingagents_lib/pyproject.toml ]; then pip install --no-cache-dir -e /app/tradingagents_lib 2>/dev/null || true; fi && python server.py"]

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=30s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1