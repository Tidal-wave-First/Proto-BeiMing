FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖和 Ollama（可选）
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://ollama.com/install.sh | sh

# 缓存破坏：每次构建时生成不同的时间戳
ARG CACHE_BUST=unknown
RUN echo "Cache bust at $CACHE_BUST"

# 复制项目文件
COPY . .

# 安装 Python 依赖
RUN pip install --no-cache-dir flask flask-socketio ddgs ollama pyyaml requests beautifulsoup4 lxml eventlet

EXPOSE 5000
EXPOSE 11434

CMD ollama serve & sleep 5 && python main.py
