from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel

Base = declarative_base()

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_name = Column(String, unique=True, index=True)
    key_value = Column(String)
    provider = Column(String)  # e.g., 'openai', 'anthropic'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    models = relationship("LLMModel", back_populates="api_key")

class LLMModel(Base):
    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, unique=True, index=True)
    provider = Column(String)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"))
    is_active = Column(Boolean, default=True)
    configuration = Column(JSON)  # Store model-specific settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    api_key = relationship("APIKey", back_populates="models")

# Pydantic models for API
class APIKeyBase(BaseModel):
    key_name: str
    provider: str
    key_value: str

class APIKeyCreate(APIKeyBase):
    pass

class APIKeyUpdate(BaseModel):
    key_name: Optional[str] = None
    provider: Optional[str] = None
    key_value: Optional[str] = None
    is_active: Optional[bool] = None

class APIKeyResponse(APIKeyBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LLMModelBase(BaseModel):
    model_name: str
    provider: str
    api_key_id: int
    configuration: dict

class LLMModelCreate(LLMModelBase):
    pass

class LLMModelUpdate(BaseModel):
    model_name: Optional[str] = None
    provider: Optional[str] = None
    api_key_id: Optional[int] = None
    configuration: Optional[dict] = None
    is_active: Optional[bool] = None

class LLMModelResponse(LLMModelBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Elasticsearch document structure (for reference)
es_threat_intel_mapping = {
    "mappings": {
        "properties": {
            "document_id": {"type": "keyword"},
            "filename": {"type": "keyword"},
            "upload_date": {"type": "date"},
            "content": {"type": "text"},
            "analysis_results": {
                "properties": {
                    "threat_actor": {"type": "keyword"},
                    "malware_name": {"type": "keyword"},
                    "attack_vector": {"type": "text"},
                    "indicators": {"type": "keyword"},
                    "targeted_sectors": {"type": "keyword"},
                    "severity": {"type": "keyword"},
                    "analysis_date": {"type": "date"},
                    "model_used": {"type": "keyword"},
                    "relevance": {"type": "text"}
                }
            },
            "metadata": {
                "properties": {
                    "file_size": {"type": "long"},
                    "page_count": {"type": "integer"},
                    "language": {"type": "keyword"},
                    "last_modified": {"type": "date"}
                }
            }
        }
    }
}
