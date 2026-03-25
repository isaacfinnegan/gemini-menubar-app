import re

def extract_nickname(messages):
    """Attempts to find a nickname in the message history, searching backwards."""
    for msg in reversed(messages):
        # 1. Check toolUse resultDisplay
        if msg.get('type') == 'toolUse' and 'resultDisplay' in msg:
            result_display = msg['resultDisplay']
            match = re.search(r'(?:Session\s+)?Nickname\s+→\s*([^\n\r]+)', result_display, re.IGNORECASE)
            if match:
                nickname = match.group(1).strip()
                if len(nickname) < 32 and not any(c in nickname for c in '[]{}()\\'):
                    return nickname

        # 2. Check standard content (user messages)
        if msg.get('type') == 'gemini':
            continue
            
        content = ""
        if isinstance(msg.get('content'), list):
            for part in msg['content']:
                if 'text' in part:
                    content += part['text']
        elif isinstance(msg.get('content'), str):
            content = msg['content']
        
        match = re.search(r'(?:Session\s+)?Nickname:\s*(["\']?)([^"\n\r]+)\1', content, re.IGNORECASE)
        if match:
            nickname = match.group(2).strip()
            if len(nickname) < 32 and not any(c in nickname for c in '[]{}()\\'):
                return nickname
            
    return None

# Simulation of messages including the regex garbage that was picked up
messages = [
    {'type': 'user', 'content': 'Nickname: [Name]` or `Session Nickname: [Name]`. However, in the session JSON...'}, # This is what it was picking up
    {'type': 'toolUse', 'resultDisplay': '**User answered:**\n  Session Nickname → menubarfixup'} # This is what we WANT
]

print(f"Extracted: {extract_nickname(messages)}")
