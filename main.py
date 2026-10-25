import os
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

LOCAL_OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
LOCAL_MODEL = "qwen2.5-coder:7b"

app = FastAPI(title="CodeMate AI")


class CodeRequest(BaseModel):
    code: str
    language: str = "Python"
    action: str = "Explain Code"


PROMPTS = {
    "Explain Code": "Explain the following code clearly, step by step.",
    "Find Bugs": "Find bugs and errors in the following code. Explain the problems and suggest fixes.",
    "Code Review": "Review the following code for readability, maintainability, security, and best practices.",
    "Optimize Code": "Optimize the following code for performance and readability. Explain the improvements.",
    "Generate Unit Tests": "Generate useful unit tests for the following code, including normal and edge cases.",
}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": "CodeMate AI",
        "provider": "Groq" if GROQ_API_KEY else "Ollama",
        "model": GROQ_MODEL if GROQ_API_KEY else LOCAL_MODEL,
    }


@app.post("/api/analyze")
def analyze_code(request: CodeRequest):
    code = request.code.strip()

    if not code:
        raise HTTPException(status_code=400, detail="Please enter some code.")

    if request.action not in PROMPTS:
        raise HTTPException(status_code=400, detail="Invalid action selected.")

    prompt = f"""
You are CodeMate AI, an expert programming assistant.

Programming language: {request.language}
Task: {PROMPTS[request.action]}

Analyze the code below. Give a clear, useful answer with headings or examples when appropriate.

CODE:
{code}
"""

    try:
        if GROQ_API_KEY:
            response = requests.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are CodeMate AI, a helpful expert coding assistant.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
                timeout=120,
            )

            if response.status_code in (401, 403):
                raise HTTPException(
                    status_code=502,
                    detail="Groq authentication failed. Check the GROQ_API_KEY environment variable.",
                )

            if response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail="Groq rate limit or quota reached. Check your Groq account and try again later.",
                )

            response.raise_for_status()
            result = response.json()["choices"][0]["message"]["content"]
            model_used = GROQ_MODEL

        else:
            response = requests.post(
                LOCAL_OLLAMA_URL,
                json={
                    "model": LOCAL_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
                timeout=180,
            )
            response.raise_for_status()
            result = response.json()["message"]["content"]
            model_used = LOCAL_MODEL

        return {
            "success": True,
            "action": request.action,
            "result": result,
            "model": model_used,
        }

    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="The AI service took too long to respond. Please try again.",
        )
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to the AI service. Check your internet connection or ensure Ollama is running.",
        )
    except requests.exceptions.HTTPError as exc:
        error_detail = "The AI service returned an error."
        if exc.response is not None:
            try:
                error_detail = exc.response.json().get("error", {}).get(
                    "message", error_detail
                )
            except ValueError:
                pass
        raise HTTPException(status_code=502, detail=error_detail)
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="The AI service returned an unexpected response.",
        )


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")