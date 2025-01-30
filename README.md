# Threat Intelligence PDF Analyzer

這是一個使用 LangChain 和 OpenAI 來分析資安威脅情報 PDF 文件的工具。它可以自動提取關鍵資訊,包括威脅行為者、惡意軟體、攻擊方式等重要情報。

[![Test](https://github.com/ericmao/threat_intel_analyzer/actions/workflows/test.yml/badge.svg)](https://github.com/ericmao/threat_intel_analyzer/actions/workflows/test.yml)
[![Deploy](https://github.com/ericmao/threat_intel_analyzer/actions/workflows/deploy.yml/badge.svg)](https://github.com/ericmao/threat_intel_analyzer/actions/workflows/deploy.yml)
[![codecov](https://codecov.io/gh/ericmao/threat_intel_analyzer/branch/main/graph/badge.svg)](https://codecov.io/gh/ericmao/threat_intel_analyzer)

## 功能特點

- 支援單一或批次 PDF 分析
- 自動提取威脅情報關鍵資訊
- 支援關鍵字搜尋和過濾
- 結構化分析結果輸出
- 直觀的網頁使用介面
- 多種 LLM 模型支援
- API 金鑰管理
- Elasticsearch 全文搜索
- Docker 容器化部署
- 支援 ARM64 架構(M1/M2 Mac)

## 技術架構

- 前端:Next.js + TypeScript + Tailwind CSS
- 後端:Python FastAPI + LangChain
- 數據庫:
  - PostgreSQL (API 金鑰和模型管理)
  - Elasticsearch (文檔存儲和搜索)
- 容器化:Docker + Docker Compose
- AI:OpenAI GPT API (可擴展支援其他 LLM)

## 快速開始

### 使用 Docker(推薦)

1. 克隆專案:
   ```bash
   git clone https://github.com/ericmao/threat_intel_analyzer.git
   cd threat_intel_analyzer
   ```

2. 設定環境變數:
   ```bash
   cp env.example .env
   # 編輯 .env 文件,填入必要的設定
   ```

3. 啟動服務:
   ```bash
   docker compose up --build
   ```

4. 開啟瀏覽器訪問:
   - 前端界面:http://localhost:3000
   - 後端 API:http://localhost:8080
   - API 文檔:http://localhost:8080/docs

### 本地開發

#### 後端開發

1. 進入後端目錄:
   ```bash
   cd backend
   ```

2. 建立虛擬環境:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. 安裝依賴:
   ```bash
   pip install -r requirements.txt
   ```

4. 運行測試:
   ```bash
   pytest --cov=.
   ```

5. 運行服務:
   ```bash
   uvicorn main:app --reload --port 8080
   ```

#### 前端開發

1. 進入前端目錄:
   ```bash
   cd frontend
   ```

2. 安裝依賴:
   ```bash
   npm install
   ```

3. 運行測試:
   ```bash
   npm test
   ```

4. 運行開發服務器:
   ```bash
   npm run dev
   ```

## CI/CD 流程

本專案使用 GitHub Actions 進行持續整合和部署:

### 測試工作流程 (test.yml)

- 單元測試 (Python/JavaScript)
- 代碼覆蓋率報告
- 代碼風格檢查 (flake8, black, isort)
- TypeScript 類型檢查
- 安全性掃描 (Snyk)

### 部署工作流程 (deploy.yml)

- Docker 映像構建
- 容器映像推送到 GitHub Container Registry
- 自動部署到生產環境
- Slack 通知

## API 端點

### 文件分析
- `POST /api/upload` - 上傳 PDF 文件
- `GET /api/documents` - 獲取已上傳的文件列表
- `GET /api/documents/{id}` - 獲取特定文件的分析結果
- `DELETE /api/documents/{id}` - 刪除文件

### API 金鑰管理
- `POST /api/api-keys` - 創建新的 API 金鑰
- `GET /api/api-keys` - 列出所有 API 金鑰
- `PUT /api/api-keys/{id}` - 更新 API 金鑰
- `DELETE /api/api-keys/{id}` - 刪除 API 金鑰

### LLM 模型管理
- `POST /api/llm-models` - 添加新的模型配置
- `GET /api/llm-models` - 列出所有可用模型
- `PUT /api/llm-models/{id}` - 更新模型配置
- `DELETE /api/llm-models/{id}` - 刪除模型配置

## 開發注意事項

- 確保 PDF 文件是文字格式而非掃描圖片
- API 金鑰應妥善保管,不要提交到版本控制系統
- 大型 PDF 分析可能需要較長時間
- 注意 OpenAI API 的使用額度
- 批次分析多個 PDF 時,請注意總處理時間

## 測試

運行所有測試:
```bash
# 後端測試
cd backend
pytest --cov=.

# 前端測試
cd frontend
npm test
```

## 貢獻指南

1. Fork 專案
2. 創建特性分支:`git checkout -b feature/AmazingFeature`
3. 提交更改:`git commit -m 'Add some AmazingFeature'`
4. 推送分支:`git push origin feature/AmazingFeature`
5. 開啟 Pull Request

確保:
- 所有測試通過
- 代碼符合風格指南
- 更新相關文檔
- 添加必要的測試用例

## 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 文件
