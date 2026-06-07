FROM python:3.10-slim

WORKDIR /app

# 安装基础依赖
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# 复制项目
COPY . .

# 安装 Python 依赖（去掉需要编译的库，减轻体积）
RUN pip install --no-cache-dir flask flask-socketio pyyaml requests beautifulsoup4 lxml eventlet

EXPOSE 5000

# 设置环境变量，确保 Python 找到模块
ENV PYTHONPATH=/app

# 启动矩阵生态
CMD ["python", "matrix/start_matrix.py"]
