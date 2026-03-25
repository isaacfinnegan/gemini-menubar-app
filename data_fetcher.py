import os
import json
import glob
import hashlib
import re
from datetime import datetime

# The root where Gemini CLI stores temporary project data
GEMINI_TMP_ROOT = os.path.expanduser('~/.gemini/tmp')
PROJECTS_CONFIG = os.path.expanduser('~/.gemini/projects.json')

def get_latest_sessions(limit=5):
    """Finds all session JSON files across all project temp directories."""
    if not os.path.exists(GEMINI_TMP_ROOT):
        return []
    
    # This pattern catches sessions in ~/.gemini/tmp/<project-dir>/chats/*.json
    search_pattern = os.path.join(GEMINI_TMP_ROOT, '*', 'chats', '*.json')
    files = glob.glob(search_pattern)
    
    if not files:
        return []

    # Sort by modification time, newest first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[:limit]

def get_project_name(project_hash):
    """Maps a project hash to its full directory path, using ~ for home."""
    if not os.path.exists(PROJECTS_CONFIG):
        return "Unknown"
    
    try:
        home = os.path.expanduser('~')
        with open(PROJECTS_CONFIG, 'r') as f:
            data = json.load(f)
            projects = data.get('projects', {})
            
            # Sort projects by path length (deepest first)
            sorted_paths = sorted(projects.keys(), key=len, reverse=True)
            
            for path in sorted_paths:
                h = hashlib.sha256(path.encode('utf-8')).hexdigest()
                if h == project_hash:
                    # Replace home with ~ if path starts with it
                    if path.startswith(home):
                        return path.replace(home, '~', 1)
                    return path
    except Exception:
        pass
        
    return "Unknown"

def extract_nickname(messages):
    """Extracts a nickname, prioritizing explicit registrations and ignoring technical noise/placeholders."""
    # Technical noise and generic placeholders to ignore
    NOISE = {
        'generalist', 'codebase_investigator', 'cli_help', 'subagent', 'nickname', 
        'gemini-subagents', 'menubar-app', 'menubarapp', 'rumps', 'python',
        'name', '[name]', '<name>', 'nickname-here'
    }
    
    for msg in messages:
        mtype = msg.get('type')
        
        # 1. Check for tool-based answers (ask_user)
        if 'toolCalls' in msg:
            for tc in msg['toolCalls']:
                display = tc.get('resultDisplay', '')
                if isinstance(display, str) and "User answered" in display:
                    match = re.search(r'Session\s+Nickname\s+→\s*([^\n\r]+)', display, re.IGNORECASE)
                    if match:
                        val = match.group(1).strip(' "\',.[]<>')
                        if val.lower() not in NOISE and len(val) < 30:
                            return val

        # 2. Check message content
        content = ""
        if isinstance(msg.get('content'), list):
            for part in msg['content']:
                if 'text' in part: content += part['text']
        elif isinstance(msg.get('content'), str):
            content = msg['content']
        
        if content:
            # STRIP CODE BLOCKS
            clean_content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
            
            # Gemini registration confirmation is the GOLD STANDARD
            if mtype == 'gemini':
                reg_match = re.search(r'Session\s+nickname\s+["\']([^"\'\n\r]+)["\']\s+registered', clean_content, re.IGNORECASE)
                if reg_match:
                    val = reg_match.group(1).strip(' "\',.[]<>')
                    if val.lower() not in NOISE:
                        return val
            
            # User explicit setting (must be at the start of a line to avoid picking up examples)
            if mtype == 'user':
                nick_match = re.search(r'(?:^|\n)(?:Session\s+)?Nickname:?\s*([^\n\r(]+)', clean_content, re.IGNORECASE)
                if nick_match:
                    val = nick_match.group(1).strip().strip(' "\',.[]<>')
                    if val.lower() not in NOISE and len(val) < 30:
                        return val
    
    return None

def parse_session_data(filepath):
    """Parses a single session file into a displayable dict."""
    try:
        mtime = os.path.getmtime(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        return None

    sid = data.get('sessionId', 'Unknown')
    p_hash = data.get('projectHash', '')
    messages = data.get('messages', [])
    
    # Try to get more accurate timestamp from the JSON itself
    last_updated_str = data.get('lastUpdated')
    if last_updated_str:
        try:
            # Parse "2026-03-22T05:24:27.149Z"
            dt = datetime.strptime(last_updated_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
            last_modified = dt.timestamp()
        except:
            last_modified = mtime
    else:
        last_modified = mtime

    nickname = extract_nickname(messages)
    
    # Calculate tokens from the last gemini message that has them
    tokens = {'total': 0, 'input': 0, 'output': 0}
    recent_actions = []
    subagent = None
    
    for msg in reversed(messages):
        if msg.get('type') == 'gemini':
            if tokens['total'] == 0 and 'tokens' in msg:
                t = msg['tokens']
                tokens = {'total': t.get('total', 0), 'input': t.get('input', 0), 'output': t.get('output', 0)}
            
            if 'toolCalls' in msg:
                for tc in reversed(msg['toolCalls']):
                    name = tc.get('name', 'Unknown')
                    if not subagent and name in ['generalist', 'codebase_investigator', 'cli_help']:
                        subagent = name
                    if len(recent_actions) < 5:
                        recent_actions.append(name)
        
        if tokens['total'] > 0 and len(recent_actions) >= 5:
            break

    return {
        'id': sid,
        'name': nickname if nickname else sid[:8],
        'workspace': get_project_name(p_hash),
        'tokens': tokens,
        'recent_actions': recent_actions,
        'subagent': subagent,
        'last_modified': last_modified
    }

def get_dashboard_data():
    """Aggregates data for the menubar app."""
    session_files = get_latest_sessions(limit=15)
    unique_sessions = {}
    
    for f in session_files:
        parsed = parse_session_data(f)
        if parsed and parsed['id'] not in unique_sessions:
            unique_sessions[parsed['id']] = parsed
            if len(unique_sessions) >= 3:
                break
                
    sessions = list(unique_sessions.values())
    latest = sessions[0] if sessions else None
    
    return {
        'active_sessions': [s['name'] for s in sessions],
        'full_sessions': sessions,
        'latest_tokens': latest['tokens'] if latest else None,
        'latest_actions': latest['recent_actions'] if latest else []
    }
