FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖 (用于 llama-cpp-python 编译)
RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 安装 Python 依赖，现在包含 llama-cpp-python
RUN pip install --no-cache-dir flask flask-socketio pyyaml requests beautifulsoup4 lxml eventlet python-dotenv llama-cpp-python

EXPOSE 5000

# 启动矩阵生态，而非旧单体应用
CMD ["python", "matrix/start_matrix.py"]
