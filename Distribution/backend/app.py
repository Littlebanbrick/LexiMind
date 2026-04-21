"""
app.py
LexiMind backend main application entry point
Integrates configuration, command parsing, LLM invocation, database operations,
and serves static frontend files for pure Python deployments.
"""

import time
import os
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables (before importing other modules)
load_dotenv()

from config import config
from command_parser import parse_command
from llm_client import query_llm
from database import (
    insert_history,
    record_word_query,
    insert_daily_article,
    get_today_article,
    get_latest_article
)

# Initialize Flask application
app = Flask(__name__, static_folder=None)  # Disable default static folder
CORS(app)  # Allow cross-origin requests (harmless even for same-origin)

# ---------- Frontend static files directory ----------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')

# ---------- Simple IP rate limiting ----------
ip_request_log = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds


def is_rate_limited(ip: str) -> bool:
    """Check if IP has exceeded the rate limit threshold"""
    now = time.time()
    ip_request_log[ip] = [
        ts for ts in ip_request_log[ip]
        if now - ts < RATE_LIMIT_WINDOW
    ]
    return len(ip_request_log[ip]) >= config.RATE_LIMIT_PER_IP


def log_request(ip: str):
    """Record a request timestamp"""
    ip_request_log[ip].append(time.time())


# ---------- Helper functions ----------
def validate_input(user_input: str) -> bool:
    """Check if input length is valid"""
    return len(user_input) <= config.MAX_INPUT_LENGTH


# ---------- Static file serving routes (must be before catch-all) ----------
@app.route('/')
def serve_index():
    """Serve the main index.html file"""
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/favicon.ico')
def blank_favicon():
    response = make_response('')
    response.headers['Content-Type'] = 'image/x-icon'
    # Disable caching for the favicon to prevent repeated requests
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    # Return 204 No Content to prevent browser from trying to render an empty icon
    return response, 204

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static assets (CSS, JS, images, etc.) from frontend directory"""
    return send_from_directory(FRONTEND_DIR, filename)


# ---------- API route definitions ----------
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})


@app.route('/api/query', methods=['POST'])
def handle_query():
    """Core query endpoint"""
    client_ip = request.remote_addr or 'unknown'

    if is_rate_limited(client_ip):
        return jsonify({
            "error": "Rate limit exceeded. Please try again later."
        }), 429

    data = request.get_json(silent=True)
    if not data or 'input' not in data:
        return jsonify({"error": "Missing 'input' field in request body"}), 400

    user_input = data['input'].strip()

    if not validate_input(user_input):
        return jsonify({
            "error": f"Input too long. Maximum {config.MAX_INPUT_LENGTH} characters allowed."
        }), 400

    log_request(client_ip)

    parsed = parse_command(user_input)
    if parsed is None:
        insert_history(user_input, 'INVALID', None)
        return jsonify({"error": "Invalid command format"}), 400

    command_type = parsed['type']
    payload = parsed.get('payload') or parsed.get('words')

    try:
        result_text = query_llm(command_type, payload)
    except Exception as e:
        insert_history(user_input, command_type, None)
        app.logger.error(f"LLM query failed: {e}")
        return jsonify({"error": "LLM service temporarily unavailable"}), 503

    if result_text is None:
        insert_history(user_input, command_type, None)
        return jsonify({"error": "Failed to get response from LLM"}), 503

    insert_history(user_input, command_type, result_text)

    if command_type in ('WORD', 'WORD_CN'):
        record_word_query(payload)
    elif command_type in ('PHRASE', 'PHRASE_CN'):
        record_word_query(payload)
    elif command_type == 'CMP':
        for word in payload:
            record_word_query(word)

    if command_type == 'DAILY_READING':
        insert_daily_article(result_text)

    return jsonify({"result": result_text})


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get recent history records (optional)"""
    from database import get_recent_history
    limit = request.args.get('limit', 20, type=int)
    if limit > 100:
        limit = 100
    history = get_recent_history(limit)
    return jsonify({"history": history})


@app.route('/api/stats/words', methods=['GET'])
def get_word_stats():
    """Get word query statistics (optional)"""
    from database import get_word_stats
    limit = request.args.get('limit', 50, type=int)
    if limit > 200:
        limit = 200
    stats = get_word_stats(limit=limit)
    return jsonify({"stats": stats})


# ---------- Error handling ----------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


# ---------- Application entry point ----------
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=config.FLASK_PORT,
        debug=(config.FLASK_ENV == 'development')
    )