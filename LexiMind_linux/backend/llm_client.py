"""
llm_client.py
Encapsulates calls to SiliconCloud DeepSeek-V3 API.
Includes prompt templates and response handling for each command type.
"""

import os
import requests
from typing import Optional, Dict, Any
from config import config
import traceback

# Read llm config from env variables or config file
DEEPSEEK_API_KEY = config.DEEPSEEK_API_KEY
DEEPSEEK_API_URL = config.DEEPSEEK_API_URL
DEFAULT_MODEL = config.DEEPSEEK_MODEL

# Backup llm config (e.g., Gemini)
GEMINI_API_KEY = config.GEMINI_API_KEY


def _call_deepseek(prompt: str, temperature: float = 0.3) -> Optional[str]:
    """
    Sending a request to DS api, then returning the response text. Return None if failed.
    """
    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY is not set in environment variables")

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": 1024,
        "stream": False
    }

    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
    except requests.exceptions.RequestException as e:
        print(f"[LLM Error] Exception details:")
        traceback.print_exc()
        print(f"[LLM Error] Request failed: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        print(f"[LLM Error] Unexpected response format: {e}")
        return None


def query_llm(command_type: str, payload: Any) -> Optional[str]:
    """
    Genrating prompts based on command type and payload, then calling the llm.
    Returning the llm's response.
    """
    if command_type == 'WORD':
        word = payload
        prompt = f"""Explain "{word}" in English:
- meaning
- TOEFL usage
- 2 examples
No Chinese. Be concise."""

    elif command_type == 'WORD_CN':
        word = payload
        prompt = f"""Explain "{word}" in English, then add Chinese.
Format:
1. Meaning
2. TOEFL usage
3. 2 examples
4. Chinese translation.
English first, then Chinese."""

    elif command_type == 'PHRASE':
        phrase = payload
        prompt = f"""Explain "{phrase}" in English:
- meaning
- TOEFL usage
- 2 examples
No Chinese."""

    elif command_type == 'PHRASE_CN':
        phrase = payload
        prompt = f"""Explain "{phrase}" in English, then add Chinese.
Format:
1. Meaning
2. TOEFL usage
3. 2 examples
4. Chinese translation.
English first."""

    elif command_type == 'WRITING':
        text = payload
        prompt = f"""Review this TOEFL text:
1. Give improvement suggestions
2. Provide a revised version

Text:
{text}

English only."""

    elif command_type == 'DAILY_READING':
        prompt = """Write a 150–200 word TOEFL-level academic passage, based on current global events or popular science topics.
Add: Source: [Topic] | Adapted for LexiMind
No Chinese."""
        return _call_deepseek(prompt, temperature=0.7)

    elif command_type == 'GENERAL':
        user_prompt = payload
        prompt = f"""{user_prompt}

(Answer in English unless Chinese is requested.)"""

    elif command_type == 'CMP':
        words = payload
        words_str = ', '.join(f'"{w}"' for w in words)
        prompt = f"""Compare {words_str}:
- meaning differences
- usage (TOEFL)
- examples

English only. Be clear."""

    else:
        print(f"[LLM Error] Unknown command type: {command_type}")
        return None
    
    prompt += "Do not end with follow-up questions or suggestions."
    return _call_deepseek(prompt)


# Optional backup func for Gemini API etc.
def _call_gemini(prompt: str) -> Optional[str]:
    pass
