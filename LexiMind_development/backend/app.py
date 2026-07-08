"""
app.py
LexiMind backend main application entry point.
Integrates configuration, command parsing, LLM invocation, and database operations.

Dev variant: API-only (sits behind the nginx reverse proxy, which also serves
the static frontend). The Distribution variant additionally serves the frontend
files itself; keep the two in sync for shared logic, but do not duplicate static
serving here.
"""

from collections import defaultdict
import time

from flask import Flask, request, jsonify
from flask_cors import CORS

# config.py already calls load_dotenv(), so importing it populates the
# environment for every downstream module (database, llm_client). There is no
# need to call load_dotenv() again here.
from config import config
from command_parser import parse_command
from llm_client import query_llm
from database import (
    insert_history,
    record_word_query,
    insert_daily_article,
    get_today_article,
    get_latest_article,
    get_recent_history,
    get_word_stats,
)

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Ensure required configuration is present at startup (raises if missing).
config.validate()

# ---------- Simple IP rate limiting ----------
# Record request timestamps per IP (minute-level).
ip_request_log = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds


def is_rate_limited(ip: str) -> bool:
    """Check if IP has exceeded the rate limit threshold"""
    now = time.time()
    # Clean up expired records (keep requests within the last minute)
    ip_request_log[ip] = [
        ts for ts in ip_request_log[ip]
        if now - ts < RATE_LIMIT_WINDOW
    ]
    # Determine if limit exceeded
    return len(ip_request_log[ip]) >= config.RATE_LIMIT_PER_IP


def log_request(ip: str):
    """Record a request timestamp"""
    ip_request_log[ip].append(time.time())


# ---------- Helper functions ----------
def validate_input(user_input: str) -> bool:
    """Check if input length is valid"""
    return len(user_input) <= config.MAX_INPUT_LENGTH


# ---------- Route definitions ----------
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})


@app.route('/api/query', methods=['POST'])
def handle_query():
    """Core query endpoint"""
    # Get client IP address
    client_ip = request.remote_addr or 'unknown'

    # Rate limit check (applied before parsing, as before)
    if is_rate_limited(client_ip):
        return jsonify({
            "error": "Rate limit exceeded. Please try again later."
        }), 429

    # Parse JSON request body
    data = request.get_json(silent=True)
    if not data or 'input' not in data:
        return jsonify({"error": "Missing 'input' field in request body"}), 400

    user_input = data['input'].strip()

    # Input length validation
    if not validate_input(user_input):
        return jsonify({
            "error": f"Input too long. Maximum {config.MAX_INPUT_LENGTH} characters allowed."
        }), 400

    # 1. Command parsing
    parsed = parse_command(user_input)
    if parsed is None:
        # Invalid format
        insert_history(user_input, 'INVALID', None)
        return jsonify({"error": "Invalid command format"}), 400

    command_type = parsed['type']
    payload = parsed.get('payload') or parsed.get('words')

    # Daily reading: return today's article if one was already generated today,
    # instead of always regenerating (and burning tokens) on every request.
    if command_type == 'DAILY_READING':
        today_article = get_today_article()
        if today_article is not None:
            log_request(client_ip)
            insert_history(user_input, command_type, today_article['content'])
            return jsonify({"result": today_article['content']})

    # Only count this request against the rate limit once we know it will
    # actually invoke the LLM. Previously, invalid/over-length inputs also
    # consumed the per-IP quota even though they never reached the model.
    log_request(client_ip)

    # 2. Call LLM
    try:
        result_text = query_llm(command_type, payload)
    except Exception as e:
        # Log failed history
        insert_history(user_input, command_type, None)
        app.logger.error(f"LLM query failed: {e}")
        return jsonify({"error": "LLM service temporarily unavailable"}), 503

    if result_text is None:
        insert_history(user_input, command_type, None)
        return jsonify({"error": "Failed to get response from LLM"}), 503

    # 3. Database recording
    # Record user interaction history
    insert_history(user_input, command_type, result_text)

    # For word/phrase commands, update words table
    if command_type in ('WORD', 'WORD_CN'):
        record_word_query(payload)
    elif command_type in ('PHRASE', 'PHRASE_CN'):
        record_word_query(payload)
    elif command_type == 'CMP':
        for word in payload:
            record_word_query(word)

    # Daily reading command: store the freshly generated article
    if command_type == 'DAILY_READING':
        insert_daily_article(result_text)

    # 4. Return result
    return jsonify({"result": result_text})


# ---------- Optional read endpoints ----------
@app.route('/api/history', methods=['GET'])
def get_history():
    """Get recent history records (optional)"""
    limit = request.args.get('limit', 20, type=int)
    if limit > 100:
        limit = 100
    history = get_recent_history(limit)
    return jsonify({"history": history})


@app.route('/api/stats/words', methods=['GET'])
def word_stats():
    """Get word query statistics (optional)"""
    limit = request.args.get('limit', 50, type=int)
    if limit > 200:
        limit = 200
    stats = get_word_stats(limit=limit)
    return jsonify({"stats": stats})


@app.route('/api/daily-reading', methods=['GET'])
def get_daily_reading():
    """
    Return today's daily reading if it exists, otherwise the most recently
    generated article. Exposes the daily_articles table that was previously
    only written to, never read from a route.
    """
    article = get_today_article()
    if article is None:
        article = get_latest_article()
    if article is None:
        return jsonify({"result": None}), 404
    return jsonify({"result": article['content']})


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
    # In development, FLASK_ENV=development enables the Flask debugger.
    # Bind to config.FLASK_HOST (127.0.0.1 by default); set FLASK_HOST=0.0.0.0
    # in the environment only when you intentionally want remote access (e.g.
    # behind nginx in Docker) — never expose the debug server publicly.
    app.run(
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=(config.FLASK_ENV == 'development')
    )
