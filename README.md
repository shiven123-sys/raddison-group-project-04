# Claude Code Web (Gemini Edition) - Full Package

This package contains the full Claude-style code generator demo (Flask + Monaco editor + streaming + code-runner + scaffold download).

**Important:** the code-runner executes Python code on the machine where the Flask app is running. Do NOT expose this server to untrusted users. Use locally for demos only.

Run:
1. Copy `.env.example` to `.env` and paste your `GEMINI_API_KEY`.
2. pip install -r requirements.txt
3. python app.py
4. Open http://127.0.0.1:5000
