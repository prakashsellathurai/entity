import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import ollama
from entityAgent.config import load_config
from entityAgent.platform_interaction import execute_command, list_processes

app = FastAPI()
config = load_config()

# Serve static files
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")

class ChatRequest(BaseModel):
    message: str
    history: List[dict]

class CommandRequest(BaseModel):
    command: str

@app.get("/")
async def read_root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        messages = request.history + [{"role": "user", "content": request.message}]
        response = ollama.chat(model=config.model, messages=messages)
        return {"response": response['message']['content']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute")
async def execute(request: CommandRequest):
    try:
        stdout, stderr, return_code = execute_command(request.command)
        return {
            "stdout": stdout,
            "stderr": stderr,
            "return_code": return_code
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/processes")
async def get_processes():
    try:
        processes = list_processes()
        return processes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
