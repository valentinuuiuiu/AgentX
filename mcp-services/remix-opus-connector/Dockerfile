FROM python:3.11-slim

WORKDIR /app

# Copy service files
COPY . /app/

# Install dependencies (fall back to Flask if requirements fail)
RUN pip install --no-cache-dir -r /app/requirements.txt || pip install --no-cache-dir flask
RUN pip install --no-cache-dir playwright && playwright install chromium && playwright install-deps

EXPOSE 3010

CMD ["python", "server.py"]
