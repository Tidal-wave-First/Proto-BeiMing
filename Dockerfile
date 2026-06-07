FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir flask flask-socketio pyyaml requests beautifulsoup4 lxml eventlet

EXPOSE 5000

CMD ["python", "main.py"]
