# CodeMate AI 🤖

An AI-powered coding assistant that helps developers understand code,
identify bugs, improve code quality, optimize solutions, and generate
unit tests.

## 🚀 Features

- 📝 Code Explanation — Understand code step by step.
- 🐛 Bug Detection — Identify potential bugs and logical errors.
- 🔍 Code Review — Receive suggestions for readability and maintainability.
- ⚡ Code Optimization — Explore improvements to code quality and performance.
- 🧪 Unit Test Generation — Generate test cases for your code.
- 🌐 Multi-language Support — Analyze code written in Python, C, C++,
  Java, JavaScript, and other supported languages.
- 💻 Web Interface — Interact with the AI through a simple web application.
- 🔒 Local AI Inference — Run the AI model locally using Ollama.

## 🛠️ Technology Stack

**Backend**
- Python
- FastAPI
- Uvicorn

**Frontend**
- HTML
- CSS
- JavaScript

**AI**
- Ollama
- Qwen2.5-Coder 7B

## 📁 Project Structure

    codemate-ai/
    ├── static/
    │   └── index.html
    ├── main.py
    ├── requirements.txt
    ├── .gitignore
    └── README.md

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.10 or a compatible newer version
- Git
- Ollama

### 1. Clone the repository

    git clone YOUR_GITHUB_REPOSITORY_URL
    cd codemate-ai

Replace `YOUR_GITHUB_REPOSITORY_URL` with your repository's actual URL.

### 2. Create a virtual environment

Windows PowerShell:

    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

### 3. Install dependencies

    pip install -r requirements.txt

### 4. Install the AI model

    ollama pull qwen2.5-coder:7b

Ensure Ollama is running on your computer.

### 5. Start the application

    uvicorn main:app --reload

### 6. Open the application

Website:
http://127.0.0.1:8000/

API documentation:
http://127.0.0.1:8000/docs

## 🔍 How to Use

1. Open CodeMate AI in your browser.
2. Select your programming language.
3. Paste your code into the editor.
4. Select an analysis option.
5. Review the AI-generated response.

## ⚠️ Limitations

- AI-generated suggestions may contain errors.
- The application does not execute submitted code.
- Local AI inference requires Ollama and the configured model.
- Performance depends on available hardware and model settings.

## 🔮 Future Improvements

- Syntax highlighting and a richer code editor.
- User accounts and saved analyses.
- Additional programming language support.
- Downloadable code review reports.
- Automated test execution in a secure sandbox.
- Cloud-hosted AI inference for public deployment.

## 👨‍💻 Author

Developed as an AI-powered software development project.

## 📄 License

A license can be added when the project is ready for open-source distribution.