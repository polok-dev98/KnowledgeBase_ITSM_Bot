# app.py

from flask import Flask, request, jsonify, render_template
from modules.chat_engine import get_chat_response
import uuid

app = Flask(__name__, static_folder="static", template_folder="templates")

# In-memory session store (optional)
user_sessions = {}

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/start', methods=['POST'])
def start_session():
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        user_id = str(uuid.uuid4())[:8]

    session_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
    user_sessions[session_id] = {"user_id": user_id}

    return jsonify({
        "message": "Session started.",
        "user_id": user_id,
        "session_id": session_id
    })

@app.route('/chat', methods=['POST'])
async def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    session_id = data.get("session_id")
    user_id = data.get("user_id")

    if not message or not session_id or not user_id:
        return jsonify({"error": "Missing message, session_id, or user_id"}), 400

    try:
        response = await get_chat_response(message, session_id, user_id)
        return jsonify({
            "response": response,
            "session_id": session_id
        })
    except Exception as e:
        return jsonify({
            "response": f"Error: {str(e)}",
            "error": True
        }), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
