import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..database import Base, get_db
from ..main import app
from ..models import APIKey, LLMModel

# 設置測試數據庫
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/test_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)

def test_create_api_key(client):
    response = client.post(
        "/api/api-keys/",
        json={
            "key_name": "test_key",
            "provider": "openai",
            "key_value": "test-api-key-value"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["key_name"] == "test_key"
    assert data["provider"] == "openai"
    assert "id" in data

def test_list_api_keys(client, test_db):
    # 創建測試數據
    test_key = APIKey(
        key_name="test_key",
        provider="openai",
        key_value="test-value"
    )
    test_db.add(test_key)
    test_db.commit()

    response = client.get("/api/api-keys/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["key_name"] == "test_key"

def test_update_api_key(client, test_db):
    # 創建測試數據
    test_key = APIKey(
        key_name="test_key",
        provider="openai",
        key_value="test-value"
    )
    test_db.add(test_key)
    test_db.commit()

    response = client.put(
        f"/api/api-keys/{test_key.id}",
        json={
            "key_name": "updated_key",
            "is_active": False
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["key_name"] == "updated_key"
    assert data["is_active"] == False

def test_delete_api_key(client, test_db):
    # 創建測試數據
    test_key = APIKey(
        key_name="test_key",
        provider="openai",
        key_value="test-value"
    )
    test_db.add(test_key)
    test_db.commit()

    response = client.delete(f"/api/api-keys/{test_key.id}")
    assert response.status_code == 200

    # 確認刪除
    response = client.get("/api/api-keys/")
    assert len(response.json()) == 0

def test_create_llm_model(client, test_db):
    # 首先創建 API key
    test_key = APIKey(
        key_name="test_key",
        provider="openai",
        key_value="test-value"
    )
    test_db.add(test_key)
    test_db.commit()

    response = client.post(
        "/api/llm-models/",
        json={
            "model_name": "gpt-4",
            "provider": "openai",
            "api_key_id": test_key.id,
            "configuration": {"temperature": 0.7}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model_name"] == "gpt-4"
    assert data["provider"] == "openai"

def test_list_available_models(client):
    response = client.get("/api/available-models")
    assert response.status_code == 200
    data = response.json()
    assert "openai" in data
    assert "gpt-4" in data["openai"]
