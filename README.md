# Threat Intelligence PDF Analyzer

這是一個使用 LangChain 和 OpenAI 來分析資安威脅情報 PDF 文件的工具。它可以自動提取關鍵資訊，包括威脅行為者、惡意軟體、攻擊方式等重要情報。

## 功能特點

- 支援單一或批次 PDF 分析
- 自動提取威脅情報關鍵資訊
- 支援關鍵字搜尋和過濾
- 結構化分析結果輸出
- 直觀的網頁使用介面
- Docker 容器化部署
- 支援 ARM64 架構（M1/M2 Mac）

## 技術架構

- 前端：Next.js + TypeScript + Tailwind CSS
- 後端：Python FastAPI + LangChain
- 容器化：Docker + Docker Compose
- AI：OpenAI GPT API

## 快速開始

### 使用 Docker（推薦）

1. 克隆專案：
   ```bash
   git clone https://github.com/ericmao/threat_intel_analyzer.git
   cd threat_intel_analyzer
   ```

2. 設定環境變數：
   ```bash
   cp .env.example .env
   # 編輯 .env 文件，填入你的 OpenAI API 金鑰
   ```

3. 啟動服務：
   ```bash
   docker compose up --build
   ```

4. 開啟瀏覽器訪問：
   - 前端界面：http://localhost:3000
   - 後端 API：http://localhost:8080

### 本地開發

#### 後端開發

1. 進入後端目錄：
   ```bash
   cd backend
   ```

2. 建立虛擬環境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```

4. 運行服務：
   ```bash
   uvicorn main:app --reload --port 8080
   ```

#### 前端開發

1. 進入前端目錄：
   ```bash
   cd frontend
   ```

2. 安裝依賴：
   ```bash
   npm install
   ```

3. 運行開發服務器：
   ```bash
   npm run dev
   ```

## 使用方式

1. 設定 OpenAI API 金鑰：
   - 在網頁介面輸入你的 OpenAI API 金鑰
   - 點擊 "Save Key" 保存

2. 上傳 PDF：
   - 點擊上傳區域選擇 PDF 文件
   - 支援單一或多個 PDF 文件
   - 等待上傳完成

3. 分析威脅情報：
   - 從文件列表選擇要分析的文件
   - 輸入可選的查詢關鍵字（例如特定的惡意軟體名稱或攻擊手法）
   - 點擊 "Analyze" 開始分析
   - 查看結構化的分析結果

## 分析結果

工具會自動提取以下資訊：
- 威脅行為者/組織
- 惡意軟體名稱
- 攻擊方式和技術
- 入侵指標 (IOCs)
- 受影響產業
- 威脅等級
- 關鍵字相關性（當提供查詢關鍵字時）

## API 端點

- `POST /api/key` - 更新 OpenAI API 金鑰
- `POST /api/upload` - 上傳 PDF 文件
- `GET /api/files` - 獲取已上傳的文件列表
- `POST /api/analyze` - 分析 PDF 文件

## 開發注意事項

- 確保 PDF 文件是文字格式而非掃描圖片
- API 金鑰應妥善保管，不要提交到版本控制系統
- 大型 PDF 分析可能需要較長時間
- 注意 OpenAI API 的使用額度
- 批次分析多個 PDF 時，請注意總處理時間

## 貢獻指南

1. Fork 專案
2. 創建特性分支：`git checkout -b feature/AmazingFeature`
3. 提交更改：`git commit -m 'Add some AmazingFeature'`
4. 推送分支：`git push origin feature/AmazingFeature`
5. 開啟 Pull Request

## 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 文件
