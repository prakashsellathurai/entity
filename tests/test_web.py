from fastapi.testclient import TestClient
from entityAgent.web.server import app
from unittest.mock import patch

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    # assert "text/html" in response.headers["content-type"]

@patch("ollama.chat")
def test_chat_api(mock_chat):
    mock_chat.return_value = {'message': {'content': 'Hello from LLM'}}
    
    response = client.post("/api/chat", json={
        "message": "Hello",
        "history": []
    })
    
    assert response.status_code == 200
    assert response.json() == {"response": "Hello from LLM"}

@patch("entityAgent.web.server.execute_command")
def test_execute_api(mock_execute):
    mock_execute.return_value = ("Output", "", 0)
    
    response = client.post("/api/execute", json={
        "command": "echo test"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["stdout"] == "Output"
    assert data["return_code"] == 0

@patch("entityAgent.web.server.list_processes")
def test_processes_api(mock_list):
    mock_list.return_value = [{"pid": 1, "name": "test", "username": "user"}]
    
    response = client.get("/api/processes")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "test"
