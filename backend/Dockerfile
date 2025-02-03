# Build stage
FROM python:3.12-slim

# 設置工作目錄
WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝依賴和系統工具
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# 複製源代碼和配置文件
COPY . .

# 建立必要的目錄
RUN mkdir -p pdfs migrations/versions

# 設置環境變數
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 創建啟動腳本
RUN echo '#!/bin/sh' > /app/start.sh && \
    echo 'alembic upgrade head' >> /app/start.sh && \
    echo 'exec python main.py' >> /app/start.sh && \
    chmod +x /app/start.sh

# 暴露端口
EXPOSE 8080

# 啟動命令
CMD ["/app/start.sh"]
