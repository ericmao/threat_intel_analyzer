from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import (
    APIKey, LLMModel,
    APIKeyCreate, APIKeyUpdate, APIKeyResponse,
    LLMModelCreate, LLMModelUpdate, LLMModelResponse
)

router = APIRouter()

@router.post("/api-keys/", response_model=APIKeyResponse)
def create_api_key(api_key: APIKeyCreate, db: Session = Depends(get_db)):
    """Create a new API key."""
    db_api_key = APIKey(
        key_name=api_key.key_name,
        key_value=api_key.key_value,
        provider=api_key.provider
    )
    db.add(db_api_key)
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

@router.get("/api-keys/", response_model=List[APIKeyResponse])
def list_api_keys(db: Session = Depends(get_db)):
    """List all API keys."""
    return db.query(APIKey).all()

@router.put("/api-keys/{key_id}", response_model=APIKeyResponse)
def update_api_key(key_id: int, api_key: APIKeyUpdate, db: Session = Depends(get_db)):
    """Update an API key."""
    db_api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not db_api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    for field, value in api_key.dict(exclude_unset=True).items():
        setattr(db_api_key, field, value)
    
    db.commit()
    db.refresh(db_api_key)
    return db_api_key

@router.delete("/api-keys/{key_id}")
def delete_api_key(key_id: int, db: Session = Depends(get_db)):
    """Delete an API key."""
    db_api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not db_api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    db.delete(db_api_key)
    db.commit()
    return {"message": "API key deleted"}

@router.post("/llm-models/", response_model=LLMModelResponse)
def create_llm_model(model: LLMModelCreate, db: Session = Depends(get_db)):
    """Create a new LLM model configuration."""
    db_model = LLMModel(**model.dict())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

@router.get("/llm-models/", response_model=List[LLMModelResponse])
def list_llm_models(db: Session = Depends(get_db)):
    """List all LLM models."""
    return db.query(LLMModel).all()

@router.put("/llm-models/{model_id}", response_model=LLMModelResponse)
def update_llm_model(model_id: int, model: LLMModelUpdate, db: Session = Depends(get_db)):
    """Update a LLM model configuration."""
    db_model = db.query(LLMModel).filter(LLMModel.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    for field, value in model.dict(exclude_unset=True).items():
        setattr(db_model, field, value)
    
    db.commit()
    db.refresh(db_model)
    return db_model

@router.delete("/llm-models/{model_id}")
def delete_llm_model(model_id: int, db: Session = Depends(get_db)):
    """Delete a LLM model configuration."""
    db_model = db.query(LLMModel).filter(LLMModel.id == model_id).first()
    if not db_model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    db.delete(db_model)
    db.commit()
    return {"message": "Model deleted"}

@router.get("/available-models")
def list_available_models():
    """List all available LLM models from different providers."""
    return {
        "openai": [
            "gpt-4",
            "gpt-4-turbo-preview",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ],
        "anthropic": [
            "claude-2",
            "claude-instant-1",
        ],
        "cohere": [
            "command",
            "command-light",
            "command-nightly",
        ]
    }
