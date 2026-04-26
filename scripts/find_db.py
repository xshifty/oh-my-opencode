#!/usr/bin/env python3
"""Find OpenCode database file on this system."""
import sqlite3
import sys
import os

# Try common locations
candidates = [
    os.path.expanduser("~/.local/share/opencode/opencode.db"),
    os.path.expanduser("~/.opencode/data.sqlite"),
    "/tmp/opencode.db",
]

for path in candidates:
    if os.path.exists(path):
        print(f"{path}")
        sys.exit(0)

# Try to find it via sqlite3
import glob as g
for pattern in [
    "~/.local/share/opencode/*.db",
    "~/.opencode/*.sqlite",
]:
    for p in g.glob(os.path.expanduser(pattern)):
        if os.path.isfile(p):
            try:
                conn = sqlite3.connect(p)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cur.fetchall()]
                if 'session' in tables or 'sessions' in tables:
                    print(f"{p}")
                    conn.close()
                    sys.exit(0)
            except:
                pass

print("DB_NOT_FOUND")
sys.exit(1)
