FROM python:3.10-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir flask flask-socketio ddgs ollama pyyaml requests beautifulsoup4 lxml eventlet

EXPOSE 5000

CMD ["python", "main.py"]
