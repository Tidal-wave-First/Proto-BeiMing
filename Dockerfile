FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖和 Ollama
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://ollama.com/install.sh | sh

# 复制项目文件
COPY . .

# 安装 Python 依赖
RUN pip install --no-cache-dir flask flask-socketio ddgs ollama pyyaml requests beautifulsoup4 lxml eventlet

# 启动 Ollama 服务并拉取模型（在构建时预拉取）
RUN ollama serve & \
    sleep 5 && \
    ollama pull qwen2.5:7b

EXPOSE 5000
EXPOSE 11434

# 启动脚本：先启动 Ollama 服务，再启动鲲
CMD ollama serve & sleep 5 && python main.py
