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
        # Injected after window creation: api.window = window
        self.window = None

    # ------------------------------------------------------------------
    # File / folder dialogs
    # ------------------------------------------------------------------

    def open_files(self):
        """Open a multi-select file dialog filtered to .tmx files.

        Returns a list of absolute file paths, or an empty list if cancelled.
        """
        result = self.window.create_file_dialog(
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
        result = self.window.create_file_dialog(webview.FOLDER_DIALOG)
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

        for in_path in files:
            stem = os.path.splitext(os.path.basename(in_path))[0]
            out_path = os.path.join(out_dir, f"{stem}_converted.tmx")

            # Reset source_platform for each file so "auto" re-detects every time
            effective_source = source_platform

            try:
                info = ICEGuard.convert(
                    in_file=in_path,
                    out_file=out_path,
                    source_platform=effective_source,
                    target_platform=target_platform,
                    pretty=bool(pretty),
                )
                results.append(
                    {
                        "filename": os.path.basename(in_path),
                        "tu_count": info.get("count", 0),
                        "detected_source": info.get("source_platform", effective_source),
                        "success": True,
                        "error": None,
                    }
                )
            except Exception as exc:
                results.append(
                    {
                        "filename": os.path.basename(in_path),
                        "tu_count": 0,
                        "detected_source": effective_source,
                        "success": False,
                        "error": str(exc),
                    }
                )

        return results
