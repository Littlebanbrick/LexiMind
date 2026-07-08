"""
config.py
Reading configuration from environment variables, with support for .env files.
"""

import os
from dotenv import load_dotenv

# Loading environment variables from .env file (if it exists).
# This runs once when the module is imported, so every other module that
# imports `config` sees the populated environment without re-loading.
load_dotenv()


class Config:
    """Configuration class, providing default values and validation for necessary settings."""
    MAX_HISTORY_RECORDS = int(os.getenv("MAX_HISTORY_RECORDS", 1000))

    # llm api configs
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.siliconflow.cn/v1/chat/completions')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-ai/DeepSeek-V3')

    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Optional

    # Flask configs
    # Default to production: debug off, loopback-only binding.
    # For Docker/remote use, set FLASK_HOST=0.0.0.0 in the environment.
    FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')  # development / production

    # db configs
    DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'data', 'leximind.db'))

    # Safe-guard configs
    RATE_LIMIT_PER_IP = int(os.getenv('RATE_LIMIT_PER_IP', 10))      # Max requests per minute per ip
    MAX_INPUT_LENGTH = int(os.getenv('MAX_INPUT_LENGTH', 2000))      # Max chars in user input

    # Optional: logging configs
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls):
        """Ensure required settings exist. Raises ValueError if not."""
        if not cls.DEEPSEEK_API_KEY:
            raise ValueError(
                "DEEPSEEK_API_KEY is not set. "
                "Please create a .env file in the backend/ directory with your API key."
            )
        return True


# Global config instance for easy access across modules
config = Config()

# NOTE: validation is intentionally NOT run at import time so that importing
# this module (e.g. for unit tests of command_parser) does not crash.
# Call config.validate() explicitly at application startup (see app.py).
