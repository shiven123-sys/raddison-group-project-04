"""
Claude Code Web (Gemini Edition) - Flask backend (final fixed version)
"""
from flask import Flask, render_template, request, jsonify, Response, send_file
import os, requests, json, tempfile, subprocess, io, time, zipfile

app = Flask(__name__, static_folder='static', template_folder='templates')

# ⚙️ CONFIG
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBwEdgr2FnftO4HhWdMqqnCC3IslciVzV0")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")  # ✅ fixed default (no models/)

# 🔹 Gemini API caller (fully corrected)
def call_gemini(prompt, model=None, timeout=60):
    model = model or GEMINI_MODEL
    # ✅ Ensure URL doesn't double “models/”
    if model.startswith("models/"):
        model_name = model
    else:
        model_name = f"models/{model}"

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "topP": 0.9, "topK": 40},
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code != 200:
            return {"error": f"Gemini API HTTP {resp.status_code}: {resp.text}"}

        result = resp.json()

        # 🧠 Extract text safely
        text = ""
        if "candidates" in result and result["candidates"]:
            c = result["candidates"][0]
            if "content" in c and "parts" in c["content"]:
                parts = c["content"]["parts"]
                if parts and "text" in parts[0]:
                    text = parts[0]["text"]
            elif "output" in c:
                text = c["output"]

        if not text:
            text = json.dumps(result, indent=2)

        return {"text": text}

    except Exception as e:
        return {"error": f"Gemini API call failed: {str(e)}"}

# 🏠 Frontend
@app.route("/")
def index():
    return render_template("index.html")

# 💬 Generate (normal)
@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    result = call_gemini(prompt)
    if "error" in result:
        return jsonify(result), 500

    return jsonify({"reply": result.get("text", "")})

# ⚡ Stream (typing)
@app.route("/api/stream", methods=["POST"])
def stream():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    result = call_gemini(prompt)
    if "error" in result:
        return jsonify(result), 500

    text = result.get("text", "[No response from Gemini]")

    def event_stream():
        for ch in text:
            yield f"data: {ch}\n\n"
            time.sleep(0.01)
        yield "data: [DONE]\n\n"

    return Response(event_stream(), mimetype="text/event-stream")

# 🧠 Run Python safely
@app.route("/api/run", methods=["POST"])
def run_code():
    data = request.get_json(force=True)
    code = data.get("code", "")
    if not code:
        return jsonify({"error": "No code provided"}), 400

    fd, filename = tempfile.mkstemp(suffix=".py", text=True)
    with os.fdopen(fd, "w") as f:
        f.write(code)

    try:
        proc = subprocess.run(
            ["python3", filename],
            capture_output=True,
            text=True,
            timeout=6,
        )
        out = proc.stdout or ""
        err = proc.stderr or ""
        return jsonify({"stdout": out, "stderr": err, "returncode": proc.returncode})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Execution timed out (6s)"}), 500
    except Exception as e:
        return jsonify({"error": f"Execution failed: {str(e)}"}), 500
    finally:
        try:
            os.remove(filename)
        except Exception:
            pass

# 📦 Scaffold ZIP
@app.route("/api/scaffold", methods=["POST"])
def scaffold():
    data = request.get_json(force=True)
    files = data.get("files", {})
    if not files:
        return jsonify({"error": "No files provided"}), 400

    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    mem_zip.seek(0)
    return send_file(
        mem_zip,
        download_name="scaffold.zip",
        as_attachment=True,
        mimetype="application/zip",
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
