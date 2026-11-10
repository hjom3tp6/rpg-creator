"""Tiny helpers shared by every engine script (they all live side by side in one directory).

Scripts import this with:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _common import saves_dir, atomic_write
"""
import json
import os


def saves_dir(root: str, game: str) -> str:
    """Per-game saves directory: <root>/saves/<game>. `game` is always required."""
    if not game:
        raise ValueError("game id is required")
    return os.path.join(root, "saves", game)


def atomic_write(path: str, text: str) -> None:
    """Write text to path via a temp file + os.replace (creates parent dirs)."""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def atomic_write_json(path: str, obj) -> None:
    atomic_write(path, json.dumps(obj, ensure_ascii=False, indent=2))


def read_text(path: str) -> str:
    """File contents, or "" when the file does not exist."""
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()
