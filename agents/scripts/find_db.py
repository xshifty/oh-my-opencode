#!/usr/bin/env python3
"""Find the OpenCode database path and print it as JSON.

Usage:
  python3 find_db.py                    — find the database automatically
  python3 find_db.py /path/to/db.db     — check a specific path
"""

import json
import sys

from shared import find_db_path


def main():
    db_path = None
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    try:
        result = {"db_path": db_path or find_db_path()}
    except FileNotFoundError as e:
        result = {"error": str(e)}

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
