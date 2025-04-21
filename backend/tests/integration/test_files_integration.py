import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

def make_file(name, content, media_type):
    return ('files', (name, io.BytesIO(content), media_type))

@pytest.fixture
def client():
    return TestClient(app)

def test_file_size_integration(client):
    """Integration test for file size handling."""
    # Create a test file with known size
    test_content = b"Hello, world!" * 100  # 1300 bytes
    test_file = make_file("test.txt", test_content, "text/plain")
    
    # Upload the file
    upload_response = client.post("/ingest", files=[test_file])
    assert upload_response.status_code == 200
    
    # Get the list of files
    files_response = client.get("/files")
    assert files_response.status_code == 200
    
    data = files_response.json()
    assert "files" in data
    files = data["files"]
    
    # Find our test file
    test_file_info = next((f for f in files if f["filename"] == "test.txt"), None)
    assert test_file_info is not None
    assert test_file_info["file_size"] == len(test_content) 