FROM python:3.10-slim

WORKDIR /app

# 安装基础依赖
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# 缓存破坏
ARG CACHE_BUST=unknown
RUN echo "Cache bust at $CACHE_BUST"

# 复制项目
COPY . .

# 安装 Python 依赖（不装 ollama）
RUN pip install --no-cache-dir flask flask-socketio ddgs pyyaml requests beautifulsoup4 lxml eventlet

EXPOSE 5000

CMD ["python", "main.py"]
