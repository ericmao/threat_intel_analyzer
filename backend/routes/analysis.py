from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
from datetime import datetime
import hashlib
from ..database import get_db, get_es
from ..models import LLMModel
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain

router = APIRouter()

def get_document_hash(content: bytes) -> str:
    """Generate a unique hash for the document."""
    return hashlib.sha256(content).hexdigest()

async def process_pdf(file: UploadFile, model_id: int, db: Session):
    """Process PDF file and store in Elasticsearch."""
    # Read file content
    content = await file.read()
    document_id = get_document_hash(content)
    
    # Save file temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        f.write(content)
    
    try:
        # Get model configuration
        model = db.query(LLMModel).filter(LLMModel.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Load and process PDF
        loader = PyPDFLoader(temp_path)
        pages = loader.load_and_split()
        
        # Get file metadata
        file_stats = os.stat(temp_path)
        
        # Prepare document metadata
        metadata = {
            "file_size": file_stats.st_size,
            "page_count": len(pages),
            "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat()
        }
        
        # Process content
        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        texts = text_splitter.split_documents(pages)
        
        # Initialize LLM with model configuration
        llm = ChatOpenAI(
            model=model.model_name,
            temperature=model.configuration.get("temperature", 0),
            api_key=model.api_key.key_value
        )
        
        # Create extraction chain
        chain = create_extraction_chain({
            "properties": {
                "threat_actor": {"type": "string"},
                "malware_name": {"type": "string"},
                "attack_vector": {"type": "string"},
                "indicators": {"type": "string"},
                "targeted_sectors": {"type": "string"},
                "severity": {"type": "string"}
            },
            "required": ["threat_actor", "malware_name", "attack_vector"]
        }, llm)
        
        # Process each chunk
        all_results = []
        for text in texts:
            try:
                result = chain.run(text.page_content)
                if result:
                    all_results.extend(result)
            except Exception as e:
                print(f"Error processing chunk: {e}")
        
        # Prepare document for Elasticsearch
        es_document = {
            "document_id": document_id,
            "filename": file.filename,
            "upload_date": datetime.utcnow().isoformat(),
            "content": "\n".join(text.page_content for text in texts),
            "analysis_results": all_results,
            "metadata": metadata,
            "model_used": {
                "id": model.id,
                "name": model.model_name,
                "provider": model.provider
            }
        }
        
        # Store in Elasticsearch
        es = get_es()
        es.index(index="threat-intel", document=es_document, id=document_id)
        
        return {
            "document_id": document_id,
            "results": all_results,
            "metadata": metadata
        }
        
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    model_id: int = None,
    db: Session = Depends(get_db)
):
    """Upload and analyze a PDF file."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    if not model_id:
        # Use default model if none specified
        model = db.query(LLMModel).filter(
            LLMModel.is_active == True,
            LLMModel.provider == "openai"
        ).first()
        if not model:
            raise HTTPException(
                status_code=400,
                detail="No default model available. Please specify a model_id"
            )
        model_id = model.id
    
    return await process_pdf(file, model_id, db)

@router.get("/documents")
async def list_documents(
    query: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """List analyzed documents with optional filtering."""
    es = get_es()
    
    # Build search query
    must_conditions = []
    if query:
        must_conditions.append({
            "multi_match": {
                "query": query,
                "fields": ["content", "analysis_results.threat_actor", "analysis_results.malware_name"]
            }
        })
    
    if from_date or to_date:
        date_range = {}
        if from_date:
            date_range["gte"] = from_date
        if to_date:
            date_range["lte"] = to_date
        must_conditions.append({
            "range": {
                "upload_date": date_range
            }
        })
    
    body = {
        "query": {
            "bool": {
                "must": must_conditions
            }
        } if must_conditions else {"match_all": {}}
    }
    
    result = es.search(index="threat-intel", body=body)
    return result["hits"]["hits"]

@router.get("/documents/{document_id}")
async def get_document(document_id: str):
    """Get a specific document by ID."""
    es = get_es()
    try:
        result = es.get(index="threat-intel", id=document_id)
        return result["_source"]
    except Exception as e:
        raise HTTPException(status_code=404, detail="Document not found")

@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document by ID."""
    es = get_es()
    try:
        es.delete(index="threat-intel", id=document_id)
        return {"message": "Document deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail="Document not found")
