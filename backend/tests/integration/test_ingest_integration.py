import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
import os
import tempfile

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_pdf():
    # Create a temporary PDF file with more realistic content
    content = b'''%PDF-1.4
1 0 obj
<< /Type /Catalog
   /Pages 2 0 R
>>
endobj
2 0 obj
<< /Type /Pages
   /Kids [3 0 R]
   /Count 1
>>
endobj
3 0 obj
<< /Type /Page
   /Parent 2 0 R
   /Resources << /Font << /F1 4 0 R >> >>
   /MediaBox [0 0 612 792]
   /Contents 5 0 R
>>
endobj
4 0 obj
<< /Type /Font
   /Subtype /Type1
   /BaseFont /Helvetica
>>
endobj
5 0 obj
<< /Length 68 >>
stream
BT
/F1 12 Tf
72 720 Td
(Test content for ingestion in PDF format) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000233 00000 n
0000000300 00000 n
trailer
<< /Size 6
   /Root 1 0 R
>>
startxref
417
%%EOF'''
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(content)
        return f.name

@pytest.fixture
def sample_txt():
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"Test content for ingestion")
        return f.name

def test_ingest_endpoint_success(client, sample_pdf, sample_txt):
    """Test successful document ingestion through the API."""
    # Prepare files for upload
    files = [
        ('files', ('test.pdf', open(sample_pdf, 'rb'), 'application/pdf')),
        ('files', ('test.txt', open(sample_txt, 'rb'), 'text/plain'))
    ]
    
    # Make request
    response = client.post(
        "/ingest",
        files=files,
        data={"namespace": "test"}
    )
    
    # Clean up
    os.unlink(sample_pdf)
    os.unlink(sample_txt)
    
    # Print error message if status code is not 200
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["namespace"] == "test"
    assert data["files_ingested"] == 2
    assert data["total_chunks"] > 0

def test_ingest_endpoint_no_files(client):
    """Test ingestion endpoint with no files."""
    response = client.post("/ingest", files=[])
    assert response.status_code == 422  # Validation error

def test_ingest_endpoint_unsupported_file(client):
    """Test ingestion endpoint with unsupported file type."""
    # Create a temporary unsupported file
    with tempfile.NamedTemporaryFile(suffix='.unsupported', delete=False) as f:
        f.write(b"test content")
        file_path = f.name
    
    # Prepare file for upload
    files = [
        ('files', ('test.unsupported', open(file_path, 'rb'), 'application/octet-stream'))
    ]
    
    # Make request
    response = client.post("/ingest", files=files)
    
    # Clean up
    os.unlink(file_path)
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["files_ingested"] == 0
    assert data["total_chunks"] == 0

def test_ingest_and_query_flow(client, sample_txt):
    """Test complete flow: ingest documents and then query them."""
    # Ingest document
    files = [
        ('files', ('test.txt', open(sample_txt, 'rb'), 'text/plain'))
    ]
    ingest_response = client.post("/ingest", files=files)
    assert ingest_response.status_code == 200
    
    # Query the ingested content
    query_response = client.post(
        "/query",
        json={"query": "Test content", "top_k": 1}
    )
    assert query_response.status_code == 200
    data = query_response.json()
    assert len(data["documents"]) > 0
    
    # Clean up
    os.unlink(sample_txt) 