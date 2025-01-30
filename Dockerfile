# 使用 Python 3.12 作為基礎映像
FROM python:3.12-slim

# 設置工作目錄
WORKDIR /app

# 複製必要的檔案
COPY requirements.txt .
COPY analyzer.py .
#COPY .env.example .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 建立分析結果目錄
RUN mkdir -p analysis_results

# 設置 volume 以持久化分析結果和輸入的 PDF 文件
VOLUME ["/app/pdfs", "/app/analysis_results"]

# 設置環境變數
ENV PYTHONUNBUFFERED=1

# 執行命令
ENTRYPOINT ["python", "analyzer.py"]
