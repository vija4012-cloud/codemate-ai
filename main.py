
import os
from pathlib import Path

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# ==================================================
# CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

GEMINI_MODEL = "gemini-3.6-flash"

GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/"
    f"models/{GEMINI_MODEL}:generateContent"
)

app = FastAPI(
    title="CodeMate AI",
    description="AI-powered coding assistant",
    version="1.0.0",
)


# ==================================================
# REQUEST MODEL
# ==================================================

class CodeRequest(BaseModel):
    code: str
    language: str = "Python"
    action: str = "Explain Code"


# ==================================================
# AVAILABLE ACTIONS
# ==================================================

PROMPTS = {
    "Explain Code": (
        "Explain the following code clearly, step by step. "
        "Describe what it does and how it works. "
        "Include examples when useful."
    ),

    "Find Bugs": (
        "Find syntax errors, logical errors, runtime errors, "
        "and edge cases in the following code. Explain the "
        "problems and provide corrected code."
    ),

    "Code Review": (
        "Review the following code for readability, "
        "maintainability, security, and programming best "
        "practices. Suggest improvements."
    ),

    "Optimize Code": (
        "Optimize the following code for performance, "
        "efficiency, and readability. Explain the improvements "
        "and provide the optimized version."
    ),

    "Generate Unit Tests": (
        "Generate useful unit tests for the following code. "
        "Include normal cases, edge cases, and expected results."
    ),
}


# ==================================================
# FRONTEND ROUTE
# ==================================================

@app.get("/")
def home():
    index_file = STATIC_DIR / "index.html"

    if not index_file.is_file():
        raise HTTPException(
            status_code=404,
            detail="Frontend not found. Check that static/index.html exists.",
        )

    return FileResponse(index_file)


# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": "CodeMate AI",
        "provider": "Google Gemini",
        "model": GEMINI_MODEL,
        "api_key_configured": bool(
            os.getenv("GEMINI_API_KEY", "").strip()
        ),
    }


# ==================================================
# GEMINI ERROR MESSAGE HELPER
# ==================================================

def get_gemini_error(response):
    try:
        error_data = response.json()

        return error_data.get(
            "error", {}
        ).get(
            "message",
            "Google Gemini API request failed.",
        )

    except (ValueError, AttributeError):
        return response.text[:500] or (
            "Google Gemini API request failed."
        )


# ==================================================
# ANALYZE CODE
# ==================================================

@app.post("/api/analyze")
def analyze_code(request: CodeRequest):

    # Validate submitted code.
    code = request.code.strip()

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Please enter some code.",
        )

    # Validate requested action.
    if request.action not in PROMPTS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid action. Available actions: "
                + ", ".join(PROMPTS.keys())
            ),
        )

    # Read the Gemini API key.
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail=(
                "Gemini API key is missing. Set GEMINI_API_KEY "
                "in your terminal and restart the server."
            ),
        )

    # Build the prompt.
    prompt = f"""
You are CodeMate AI, an expert programming assistant.

Programming language: {request.language}

Task:
{PROMPTS[request.action]}

Instructions:
- Explain your answer clearly.
- Use headings when appropriate.
- Provide corrected code when necessary.
- Include examples where useful.
- Preserve the intended functionality of the original code.

Code to analyze:

```{request.language}
{code}
```
"""

    # Prepare the Gemini API request.
    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": (
                        "You are CodeMate AI, a helpful and reliable "
                        "programming assistant. Help users understand, "
                        "debug, review, test, and optimize code. "
                        "Provide clear explanations and accurate "
                        "programming solutions."
                    )
                }
            ]
        },

        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ],
            }
        ],

        "generationConfig": {
            "temperature": 0.2,
        },
    }

    # Send request to Google Gemini.
    try:
        response = requests.post(
            GEMINI_API_URL,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=120,
        )

        # Handle unsuccessful API responses.
        if not response.ok:
            error_message = get_gemini_error(response)

            print(
                "Gemini HTTP status:",
                response.status_code,
            )

            print(
                "Gemini error:",
                error_message,
            )

            if response.status_code == 429:
                raise HTTPException(
                    status_code=429,
                    detail=(
                        "Gemini API quota or rate limit reached. "
                        "Check your Google AI Studio quota. Details: "
                        + error_message
                    ),
                )

            if response.status_code in (400, 401, 403, 404):
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_message,
                )

            raise HTTPException(
                status_code=502,
                detail=(
                    f"Gemini returned HTTP {response.status_code}: "
                    f"{error_message}"
                ),
            )

        # Parse successful response.
        data = response.json()

        candidates = data.get("candidates", [])

        if not candidates:
            block_reason = data.get(
                "promptFeedback", {}
            ).get(
                "blockReason",
                "No response was returned.",
            )

            raise HTTPException(
                status_code=502,
                detail=f"Gemini returned no answer: {block_reason}",
            )

        # Extract generated text.
        parts = candidates[0].get(
            "content", {}
        ).get(
            "parts", []
        )

        result = "\n".join(
            part["text"]
            for part in parts
            if isinstance(part, dict) and "text" in part
        ).strip()

        if not result:
            raise HTTPException(
                status_code=502,
                detail="Gemini returned an empty response.",
            )

        # Return the result to the frontend.
        return {
            "success": True,
            "action": request.action,
            "language": request.language,
            "result": result,
            "model": GEMINI_MODEL,
            "provider": "Google Gemini",
        }

    # Preserve meaningful API error messages.
    except HTTPException:
        raise

    # Handle request timeout.
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail=(
                "Gemini took too long to respond. "
                "Please try again."
            ),
        )

    # Handle connection failures.
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not connect to Google Gemini. "
                "Check your internet connection."
            ),
        )

    # Handle other network errors.
    except requests.exceptions.RequestException as exc:
        print(
            f"Gemini request error: {type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "A network error occurred while contacting Gemini. "
                "Check the server terminal for details."
            ),
        )

    # Handle invalid JSON responses.
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Gemini returned an invalid response.",
        )


# ==================================================
# STATIC FILES
# ==================================================

if STATIC_DIR.is_dir():
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )


# ==================================================
# START SERVER
# ==================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
