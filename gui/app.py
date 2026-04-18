"""
gui/app.py — Entry point for the TMX Ice Guard GUI.

Usage:
    python gui/app.py
  or (from project root):
    python -m gui.app
"""

import os
import sys

# Work around a known pywebview issue on Windows where the .NET accessibility
# layer recursively traverses AccessibilityObject.Bounds.Empty until Python's
# default recursion limit (1 000) is hit.
# See: https://github.com/nicegui-dev/pywebview/issues/1032
if sys.platform == "win32":
    sys.setrecursionlimit(10_000)

# Make the project root importable regardless of how the script is invoked
_here = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_here)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import webview
from backend.api import Api


def main():
    api = Api()

    html_path = os.path.join(_here, "frontend", "index.html")
    html_url = f"file:///{html_path.replace(os.sep, '/')}"

    window = webview.create_window(
        title="TMX Ice Guard",
        url=html_url,
        js_api=api,
        width=800,
        height=700,
        min_size=(640, 560),
    )

    def on_started():
        api.window = window

    webview.start(on_started)


if __name__ == "__main__":
    main()
