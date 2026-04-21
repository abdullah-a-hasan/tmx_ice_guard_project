import json
import os
import sys

# Make the project root importable when running from inside gui/
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import webview
from tmx_ice_guard import ICEGuard
from tmx_ice_guard.tmx_context_defs import tmx_context_defs


class Api:
    """Python object exposed to the JavaScript frontend via pywebview js_api."""

    def __init__(self):
        # Injected after window creation: api._window = window
        # The underscore prefix is intentional — pywebview's get_functions()
        # skips private attributes, which prevents it from recursively
        # traversing Window.native (the WinForms Form) and hitting the
        # infinite AccessibilityObject.Bounds.Empty chain on Windows.
        self._window = None

    # ------------------------------------------------------------------
    # File / folder dialogs
    # ------------------------------------------------------------------

    def open_files(self):
        """Open a multi-select file dialog filtered to .tmx files.

        Returns a list of absolute file paths, or an empty list if cancelled.
        """
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=("TMX Files (*.tmx)", "All Files (*.*)"),
        )
        if result is None:
            return []
        return list(result)

    def open_folder(self):
        """Open a folder-picker dialog.

        Returns the chosen directory path as a string, or None if cancelled.
        """
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if result is None:
            return None
        # pywebview returns a tuple with a single path for FOLDER_DIALOG
        return result[0] if result else None

    # ------------------------------------------------------------------
    # Platform metadata
    # ------------------------------------------------------------------

    def get_platforms(self):
        """Return the list of supported platform keys from tmx_context_defs.

        The special value "auto" (auto-detect source) is prepended so the UI
        can offer it as the default source option.
        """
        keys = list(tmx_context_defs.keys())
        return ["auto"] + keys

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------

    def convert_files(self, files, out_dir, source_platform, target_platform, pretty):
        """Convert a list of TMX files one at a time using ICEGuard.convert().

        The original API is single-file only; multi-file support is implemented
        here by looping and calling convert() once per file.

        Live progress events are pushed to the JS frontend via evaluate_js()
        as each file is processed.  Every event dict is enriched with:
          file_index  – 0-based index of the current file
          total_files – total number of files being converted

        Parameters
        ----------
        files : list[str]   Absolute paths of input TMX files.
        out_dir : str        Directory where converted files are written.
        source_platform : str  Source platform key (or "auto").
        target_platform : str  Target platform key.
        pretty : bool        Whether to pretty-print the output XML.

        Returns
        -------
        list[dict]  One dict per file with keys:
                    filename, tu_count, detected_source, success, error
        """
        results = []
        total = len(files)

        for file_index, in_path in enumerate(files):
            stem = os.path.splitext(os.path.basename(in_path))[0]
            out_path = os.path.join(out_dir, f"{stem}_converted.tmx")

            # Reset source_platform for each file so "auto" re-detects every time
            effective_source = source_platform
            info = None

            try:
                for event in ICEGuard.convert(
                    in_file=in_path,
                    out_file=out_path,
                    source_platform=effective_source,
                    target_platform=target_platform,
                    pretty=bool(pretty),
                ):
                    event["file_index"] = file_index
                    event["total_files"] = total

                    if event["type"] == "flavor":
                        effective_source = event["platform"]
                    elif event["type"] == "done":
                        info = event

                    self._push_progress(event)

                file_result = {
                    "filename": os.path.basename(in_path),
                    "tu_count": info.get("count", 0) if info else 0,
                    "detected_source": info.get("source_platform", effective_source) if info else effective_source,
                    "success": True,
                    "error": None,
                }
            except Exception as exc:
                file_result = {
                    "filename": os.path.basename(in_path),
                    "tu_count": 0,
                    "detected_source": effective_source,
                    "success": False,
                    "error": str(exc),
                }

            results.append(file_result)

            done_event = {
                "type": "file_done",
                "file_index": file_index,
                "total_files": total,
                **file_result,
            }
            self._push_progress(done_event)

        return results

    def _push_progress(self, event):
        """Push a progress event dict to the JS frontend via evaluate_js.

        Silently skips if the window bridge is not available.
        """
        if self._window is None:
            return
        try:
            self._window.evaluate_js(
                "window.onConversionProgress(" + json.dumps(event, ensure_ascii=True) + ")"
            )
        except Exception:
            pass
