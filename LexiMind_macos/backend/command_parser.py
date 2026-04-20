"""
command_parser.py
Parse user input, identify command type, and extract parameters.
Supported commands:
  $ word          - English word explanation
  $cn word        - English word explanation + Chinese translation
  $$ phrase       - English phrase explanation
  $$cn phrase     - English phrase explanation + Chinese translation
  $$$ text        - Writing revision
  daily-reading   - Daily reading
  > prompt        - General Q&A
  $cmp arg1 arg2 ... - Word/Phrase comparison (at least two arguments, phrases must be wrapped in quotes)
"""

import re
import shlex
from typing import Optional, Dict, Any, List


def parse_command(user_input: str) -> Optional[Dict[str, Any]]:
    """
    Parse user input and return command type and parameters.
    Returns None if the format is invalid.
    """
    if not isinstance(user_input, str):
        return None

    s = user_input.strip()

    # 1. Daily reading
    if s == 'daily-reading':
        return {'type': 'DAILY_READING'}

    # 2. General Q&A
    if s.startswith('>'):
        prompt = s[1:].strip()
        if prompt == '':
            return None
        return {'type': 'GENERAL', 'payload': prompt}

    # 3. Writing revision
    if s.startswith('$$$'):
        text = s[3:].strip()
        if text == '':
            return None
        return {'type': 'WRITING', 'payload': text}

    # 4. Phrase explanation (with Chinese)
    if s.startswith('$$cn'):
        phrase = s[4:].strip()
        if phrase == '':
            return None
        return {'type': 'PHRASE_CN', 'payload': phrase}

    # 5. Phrase explanation (English only)
    if s.startswith('$$'):
        phrase = s[2:].strip()
        if phrase == '':
            return None
        return {'type': 'PHRASE', 'payload': phrase}

    # 6. Word explanation (with Chinese)
    if s.startswith('$cn'):
        word = s[3:].strip()
        if word == '' or ' ' in word:
            return None
        return {'type': 'WORD_CN', 'payload': word}

    # 7. Word/phrase comparison (supports quoted phrases)
    if s.startswith('$cmp'):
        # Remove command prefix
        rest = s[4:].strip()
        if not rest:
            return None

        # Use shlex.split to handle quoted arguments
        # Note: shlex.split behaves differently on Windows by default; explicitly specify posix=True
        try:
            args = shlex.split(rest, posix=True)
        except ValueError:
            # Errors such as unmatched quotes
            return None

        # Filter out possible empty strings
        args = [arg.strip() for arg in args if arg.strip() != '']
        if len(args) < 2:
            return None

        return {'type': 'CMP', 'words': args}

    # 8. Word explanation (English only)
    if s.startswith('$'):
        word = s[1:].strip()
        if word == '' or ' ' in word:
            return None
        return {'type': 'WORD', 'payload': word}

    # No pattern matched
    return None


def get_command_description(command_type: str) -> str:
    """Return a description of the command type."""
    descriptions = {
        'WORD': 'English word explanation',
        'WORD_CN': 'English word explanation (with Chinese translation)',
        'PHRASE': 'English phrase explanation',
        'PHRASE_CN': 'English phrase explanation (with Chinese translation)',
        'WRITING': 'English writing polish and suggestions',
        'DAILY_READING': 'Daily English reading',
        'GENERAL': 'General Q&A',
        'CMP': 'Word/Phrase comparison',
    }
    return descriptions.get(command_type, 'Unknown command')


# Test code
if __name__ == '__main__':
    test_cases = [
        '$ abandon',
        '$cn abandon',
        '$$ take part in',
        '$$cn take part in',
        '$$$ This is a sample essay.',
        'daily-reading',
        '> What is TOEFL?',
        '$cmp affect effect influence',
        '$cmp "take part in" "join in" participate',
        "$cmp 'take off' 'get off'",
        '$cmp hello',                     # Invalid: fewer than two words
        '$',                              # Invalid
        'hello world',                    # Invalid
        '$cmp "unclosed quote',           # Invalid: unmatched quote
    ]
    for case in test_cases:
        result = parse_command(case)
        print(f"{case!r:45} -> {result}")