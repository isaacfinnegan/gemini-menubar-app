import rumps
long_name = "[Name]` or `Session Nickname: [Name]`. However, in the session JSON, the answer to the nickname request is stored in a `resultDisplay` field within a `toolUse` message, formatted as `**User answered:**\n Session Nickname → menubarfixup`."
print("Attempting to run with long name")
rumps.App("Test").menu = [long_name]
rumps.App("Test").run()
