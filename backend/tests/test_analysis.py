import pytest
import os
from fastapi.testclient import TestClient
from elasticsearch import Elasticsearch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..database import Base, get_db, get_es
from ..main import app
from ..models import APIKey, LLMModel

# 設置測試數據庫
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/test_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 設置測試 Elasticsearch
TEST_ES_HOST = os.getenv("TEST_ES_HOST", "localhost")
TEST_ES_PORT = os.getenv("TEST_ES_PORT", "9200")
es_client = Elasticsearch([f"http://{TEST_ES_HOST}:{TEST_ES_PORT}"])

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
def test_es():
    # 創建測試索引
    if not es_client.indices.exists(index="test-threat-intel"):
        from ..models import es_threat_intel_mapping
        es_client.indices.create(
            index="test-threat-intel",
            body=es_threat_intel_mapping
        )
    yield es_client
    # 清理測試索引
    if es_client.indices.exists(index="test-threat-intel"):
        es_client.indices.delete(index="test-threat-intel")

@pytest.fixture
def client(test_db, test_es):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    def override_get_es():
        return test_es
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_es] = override_get_es
    return TestClient(app)

@pytest.fixture
def test_pdf():
    # 創建測試 PDF 文件
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/MediaBox [0 0 612 792]\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 68\n>>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n(Test threat intelligence document with malware info.) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\n0000000254 00000 n\n0000000332 00000 n\ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n452\n%%EOF"
    
    with open("test.pdf", "wb") as f:
        f.write(pdf_content)
    yield "test.pdf"
    os.remove("test.pdf")

def test_upload_file(client, test_db, test_pdf):
    # 創建測試 API key 和模型
    test_key = APIKey(
        key_name="test_key",
        provider="openai",
        key_value="test-value"
    )
    test_db.add(test_key)
    test_db.commit()

    test_model = LLMModel(
        model_name="gpt-4",
        provider="openai",
        api_key_id=test_key.id,
        configuration={"temperature": 0}
    )
    test_db.add(test_model)
    test_db.commit()

    # 上傳文件
    with open(test_pdf, "rb") as f:
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", f, "application/pdf")},
            params={"model_id": test_model.id}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert "results" in data
    assert "metadata" in data

def test_list_documents(client, test_es):
    # 插入測試文檔
    test_doc = {
        "document_id": "test123",
        "filename": "test.pdf",
        "upload_date": "2025-01-30T00:00:00",
        "content": "Test threat intelligence content",
        "analysis_results": [
            {
                "threat_actor": "TestActor",
                "malware_name": "TestMalware",
                "attack_vector": "Test Attack"
            }
        ]
    }
    test_es.index(index="test-threat-intel", id="test123", document=test_doc)
    test_es.indices.refresh(index="test-threat-intel")

    response = client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["_source"]["document_id"] == "test123"

def test_search_documents(client, test_es):
    # 插入測試文檔
    test_doc = {
        "document_id": "test123",
        "filename": "test.pdf",
        "upload_date": "2025-01-30T00:00:00",
        "content": "Test threat intelligence content with TestMalware",
        "analysis_results": [
            {
                "threat_actor": "TestActor",
                "malware_name": "TestMalware",
                "attack_vector": "Test Attack"
            }
        ]
    }
    test_es.index(index="test-threat-intel", id="test123", document=test_doc)
    test_es.indices.refresh(index="test-threat-intel")

    response = client.get("/api/documents", params={"query": "TestMalware"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "TestMalware" in data[0]["_source"]["content"]

def test_get_document(client, test_es):
    # 插入測試文檔
    test_doc = {
        "document_id": "test123",
        "filename": "test.pdf",
        "upload_date": "2025-01-30T00:00:00",
        "content": "Test content"
    }
    test_es.index(index="test-threat-intel", id="test123", document=test_doc)
    test_es.indices.refresh(index="test-threat-intel")

    response = client.get("/api/documents/test123")
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == "test123"

def test_delete_document(client, test_es):
    # 插入測試文檔
    test_doc = {
        "document_id": "test123",
        "filename": "test.pdf",
        "upload_date": "2025-01-30T00:00:00",
        "content": "Test content"
    }
    test_es.index(index="test-threat-intel", id="test123", document=test_doc)
    test_es.indices.refresh(index="test-threat-intel")

    response = client.delete("/api/documents/test123")
    assert response.status_code == 200

    # 確認刪除
    response = client.get("/api/documents/test123")
    assert response.status_code == 404
