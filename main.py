from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI(
    title="CodeMate AI",
    description="An AI-powered coding assistant and code reviewer",
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "qwen2.5-coder:7b"


class CodeRequest(BaseModel):
    code: str
    language: str = "Python"
    action: str = "Explain Code"


PROMPTS = {
    "Explain Code": (
        "Explain the following code clearly, step by step. "
        "Describe its purpose and important concepts."
    ),
    "Find Bugs": (
        "Analyze the following code for bugs, logical errors, and edge cases. "
        "Explain each issue and provide corrected code where appropriate."
    ),
    "Code Review": (
        "Review the following code for correctness, readability, maintainability, "
        "security concerns, and coding best practices. Give actionable feedback."
    ),
    "Optimize Code": (
        "Suggest ways to improve the performance and readability of the following "
        "code. Explain the improvements and provide an optimized version."
    ),
    "Generate Unit Tests": (
        "Generate useful unit tests for the following code, including normal cases, "
        "edge cases, and invalid inputs where relevant. State any assumptions."
    ),
}


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "CodeMate AI", "model": MODEL_NAME}


@app.post("/api/analyze")
def analyze_code(request: CodeRequest):
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Please enter some code.")

    if request.action not in PROMPTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported action. Choose one of: {', '.join(PROMPTS)}",
        )

    prompt = (
        f"{PROMPTS[request.action]}\n\n"
        f"Programming language: {request.language}\n\n"
        f"Code:\n```{request.language.lower()}\n"
        f"{request.code}\n```\n\n"
        "Format your response using clear headings and code blocks where useful. "
        "Do not claim to have executed the code unless you actually have."
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.2},
            },
            timeout=180,
        )
        response.raise_for_status()
        result = response.json()
        answer = result.get("message", {}).get("content", "")

        if not answer:
            raise HTTPException(
                status_code=502,
                detail="The AI model returned an empty response.",
            )

        return {"result": answer, "model": MODEL_NAME}

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Cannot connect to Ollama. Make sure Ollama is running "
                "on this computer."
            ),
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="The AI model took too long to respond. Please try again.",
        )
    except requests.exceptions.HTTPError:
        raise HTTPException(
            status_code=502,
            detail="Ollama returned an error. Check that the model is installed.",
        )


@app.get("/")
def home():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return {
            "message": "CodeMate AI backend is running!",
            "next_step": "Create static/index.html for the frontend.",
        }
    return FileResponse(index_file)


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")