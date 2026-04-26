#!/usr/bin/env python3
"""Shared tools for OpenCode session analysis scripts.

This is used by all get_*.py scripts to connect to the database.
"""

import json
import os
import sqlite3
from collections import Counter, defaultdict


def find_db_path() -> str:
    """Find the OpenCode database file. Checks common install locations."""
    candidates = [
        os.path.expanduser("~/.local/share/opencode/opencode.db"),
        os.path.join(os.environ.get("HOME", ""), ".config/opencode/opencode.db"),
        os.path.expanduser("~/Library/Application Support/opencode/opencode.db"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "OpenCode database not found. Check ~/.local/share/opencode/"
    )


def get_db(db_path: str) -> sqlite3.Connection:
    """Open a connection to the OpenCode database. Returns rows as dicts."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_rows(conn, query: str, params=()) -> list[dict]:
    """Run a query and return all rows as a list of dicts."""
    return [dict(r) for r in conn.execute(query, params).fetchall()]


def parse_part_data(part: dict) -> dict:
    """Read JSON data from a part row. Handles both string and dict formats."""
    data = part["data"]
    if isinstance(data, str):
        return json.loads(data)
    return data


def build_placeholders(ids: list[str]) -> tuple[str, list]:
    """Build SQL IN clause placeholders and params for a list of IDs.

    Example: ids=["a","b","c"] -> ("?,?,?", ["a","b","c"])
    """
    placeholders = ",".join("?" for _ in ids)
    return placeholders, [str(i) for i in ids]
