# Build stage
FROM python:3.12-slim

# 設置工作目錄
WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製源代碼
COPY . .

# 建立上傳目錄
RUN mkdir -p pdfs

# 暴露端口
EXPOSE 8080

# 啟動命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
