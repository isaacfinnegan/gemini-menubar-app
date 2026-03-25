import re

def extract_nickname(messages):
    """Attempts to find a nickname in the message history, searching backwards."""
    for msg in reversed(messages):
        # 1. Check top-level resultDisplay
        if 'resultDisplay' in msg:
            match = re.search(r'Session\s+Nickname\s+→\s*([^\n\r]+)', msg['resultDisplay'], re.IGNORECASE)
            if match:
                nickname = match.group(1).strip()
                if len(nickname) < 32 and not any(c in nickname for c in '[]{}()\\'):
                    return nickname

        # 2. Check nested toolCalls
        if 'toolCalls' in msg:
            for tc in reversed(msg['toolCalls']):
                if 'resultDisplay' in tc:
                    match = re.search(r'Session\s+Nickname\s+→\s*([^\n\r]+)', tc['resultDisplay'], re.IGNORECASE)
                    if match:
                        nickname = match.group(1).strip()
                        if len(nickname) < 32 and not any(c in nickname for c in '[]{}()\\'):
                            return nickname

        # 3. Check standard content
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

# Simulation of messages structure from the JSON
messages = [
    {
        "type": "gemini",
        "toolCalls": [
            {
                "name": "ask_user",
                "resultDisplay": "**User answered:**\n  Session Nickname → menubarfixup"
            }
        ]
    }
]

print(f"Extracted: {extract_nickname(messages)}")
