import rumps
import sys
import data_fetcher
import time
from datetime import datetime
from AppKit import NSAttributedString, NSMutableParagraphStyle, NSParagraphStyleAttributeName

class GeminiMenubarApp(rumps.App):
    def __init__(self):
        super(GeminiMenubarApp, self).__init__("🤖 Gemini", quit_button=None)
        self.menu = [rumps.MenuItem("Loading...")]
        self.refresh_data(None)

    @rumps.timer(2)
    def refresh_data(self, sender):
        try:
            data = data_fetcher.get_dashboard_data()
        except Exception as e:
            with open("app_error.log", "a") as f:
                f.write(f"{datetime.now()} - Error fetching data: {e}\n")
            return

        if not data:
            return

        # Clear existing menu items entirely
        self.menu.clear()

        sessions = data.get('full_sessions', [])
        
        # Determine overall app title (status dot and total count)
        active_count = 0
        total_count = len(sessions)
        
        for session in sessions:
            if (time.time() - session.get('last_modified', 0)) < 300:
                active_count += 1
                
        if total_count == 0:
            self.title = "🤖 0"
        elif active_count > 0:
            self.title = f"🟢 {total_count}"
        else:
            self.title = f"⚪️ {total_count}"

        if not sessions:
            self.menu.add(rumps.MenuItem("No active sessions"))
        else:
            active_items = []
            inactive_items = []

            for session in sessions:
                workspace = session.get('workspace', 'Unknown')
                name = session.get('name', 'Unknown')
                tokens = session.get('tokens', {})
                actions = session.get('recent_actions', [])
                last_modified = session.get('last_modified', 0)
                active_subagent = session.get('active_subagent')

                # Determine if session is active (updated in last 5 min)
                is_active = (time.time() - last_modified) < 300
                status_indicator = "🟢 " if is_active else "⚪️ "

                # Token info for display
                total_tokens = tokens.get('total', 0)
                input_context = tokens.get('input', 0)

                # Determine if session name is just a fallback ID
                sid = session.get('id', 'Unknown')
                is_fallback_id = name == sid[:8]
                
                # Primary Title (Line 1) focuses on the workspace
                display_name = workspace
                if not is_fallback_id:
                    display_name = f"{workspace} - {name}"
                
                title = f"{status_indicator}{display_name}"
                subtitle = f"   Tokens: {total_tokens:,} (In: {input_context:,})"
                full_title = f"{title}\n{subtitle}"
                
                # Rumps MenuItem title still needs to be set for internal keys, 
                # but we override the display with an attributedTitle
                session_item = rumps.MenuItem(title)
                
                # Create a paragraph style for padding and line spacing
                paragraph_style = NSMutableParagraphStyle.alloc().init()
                paragraph_style.setLineSpacing_(1.0)          # Reduced space between the 2 lines by 50%
                paragraph_style.setParagraphSpacing_(3.0)     # 3 pixels of padding at bottom
                paragraph_style.setParagraphSpacingBefore_(0.0) # No extra top padding
                
                attributes = {
                    NSParagraphStyleAttributeName: paragraph_style
                }
                
                attr_title = NSAttributedString.alloc().initWithString_attributes_(full_title, attributes)
                session_item._menuitem.setAttributedTitle_(attr_title)
                
                # Add subagent info
                if active_subagent:
                    session_item.add(rumps.MenuItem(f"Active Agent: {active_subagent}"))
                    session_item.add(rumps.separator)
                
                # Add submenus
                session_item.add(rumps.MenuItem(f"Session ID: {sid}"))
                session_item.add(rumps.separator)
                session_item.add(rumps.MenuItem(f"Total Tokens: {total_tokens:,}"))
                session_item.add(rumps.MenuItem(f"Context (Input): {input_context:,}"))
                
                if actions:
                    session_item.add(rumps.separator)
                    session_item.add(rumps.MenuItem("Recent Actions:"))
                    for i, action in enumerate(actions):
                        session_item.add(rumps.MenuItem(f"{i+1}. {action}"))
                        
                if is_active:
                    active_items.append(session_item)
                else:
                    inactive_items.append(session_item)

            if not active_items:
                self.menu.add(rumps.MenuItem("No active sessions"))
            else:
                for item in active_items:
                    self.menu.add(item)
            
            if inactive_items:
                self.menu.add(rumps.separator)
                older_menu = rumps.MenuItem("Older Sessions")
                for item in inactive_items:
                    older_menu.add(item)
                self.menu.add(older_menu)

        # Add the Quit button at the very end
        self.menu.add(rumps.separator)
        quit_item = rumps.MenuItem("Quit")
        quit_item.set_callback(rumps.quit_application)
        self.menu.add(quit_item)

if __name__ == "__main__":
    GeminiMenubarApp().run()
