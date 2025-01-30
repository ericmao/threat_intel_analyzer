from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain
import shutil

app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局變數
UPLOAD_DIR = "pdfs"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# 確保上傳目錄存在
os.makedirs(UPLOAD_DIR, exist_ok=True)

class APIKeyUpdate(BaseModel):
    key: str

class AnalysisRequest(BaseModel):
    filename: str
    query: Optional[str] = None

def analyze_threat_intel_pdf(pdf_path: str, query: Optional[str] = None):
    """分析威脅情報PDF文件"""
    try:
        # 載入PDF
        loader = PyPDFLoader(pdf_path)
        pages = loader.load_and_split()
        
        # 分割文本
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        texts = text_splitter.split_documents(pages)
        
        # 定義提取模式
        schema = {
            "properties": {
                "threat_actor": {"type": "string", "description": "Name of the threat actor or group"},
                "malware_name": {"type": "string", "description": "Names of any malware mentioned"},
                "attack_vector": {"type": "string", "description": "Methods used to carry out the attack"},
                "indicators": {"type": "string", "description": "IOCs like IP addresses, domains, or file hashes"},
                "targeted_sectors": {"type": "string", "description": "Industries or sectors targeted"},
                "severity": {"type": "string", "description": "Severity level of the threat"},
            },
            "required": ["threat_actor", "malware_name", "attack_vector"],
        }
        
        # 初始化LLM
        llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        chain = create_extraction_chain(schema, llm)
        
        # 處理每個文本塊
        all_results = []
        for text in texts:
            try:
                if query:
                    # 如果有特定查詢，先檢查相關性
                    relevance_prompt = f"""
                    Analyze if the following text is relevant to the query: '{query}'
                    
                    Text: {text.page_content}
                    
                    If relevant, explain why. If not relevant, just say 'Not relevant'.
                    """
                    relevance_response = llm.predict(relevance_prompt)
                    if "not relevant" in relevance_response.lower():
                        continue
                
                result = chain.run(text.page_content)
                if result:
                    if query:
                        for item in result:
                            item["relevance"] = relevance_response
                    all_results.extend(result)
                    
            except Exception as e:
                print(f"Error processing chunk: {e}")
        
        return all_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/key")
async def update_api_key(key_update: APIKeyUpdate):
    """更新OpenAI API金鑰"""
    global OPENAI_API_KEY
    OPENAI_API_KEY = key_update.key
    os.environ["OPENAI_API_KEY"] = key_update.key
    return {"message": "API key updated successfully"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上傳PDF文件"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def list_files():
    """列出已上傳的PDF文件"""
    try:
        files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith('.pdf')]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_file(request: AnalysisRequest):
    """分析PDF文件"""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="OpenAI API key not set")
    
    file_path = os.path.join(UPLOAD_DIR, request.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        results = analyze_threat_intel_pdf(file_path, request.query)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
