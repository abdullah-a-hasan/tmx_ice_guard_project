# TMX Ice Guard

**Version 1.0b0**

TMX Ice Guard is a Python library (and optional desktop GUI) for converting **ICE context metadata** between different **TMX (Translation Memory eXchange)** platform flavors. Translation tools encode "previous/next segment" context in incompatible ways; TMX Ice Guard normalises and remaps those properties so ICE matches survive round-trips across platforms.

## Features

- **Remap ICE context metadata** between translation platform flavors in a single pass over the TMX file.
- **Auto-detect source platform** from the TMX `creationtool` header — no need to know which tool produced the file.
- **Supported platforms:** Phrase/Memsource, memoQ, XTM, TransPerfect (GlobalLink / Wordfast), RWS (Trados), Transifex.
- **Optional pretty-print** of output XML for human-readable diffs.
- **Zero runtime dependencies** for the library itself — uses only the Python standard library.
- **Desktop GUI** built with [pywebview](https://pywebview.flowrl.com/) for a point-and-click workflow (multi-file batch conversion with live progress).

## Installation

Install the library via `pip`:

```bash
pip install tmx-ice-guard
```

To use the **desktop GUI**, also install pywebview:

```bash
pip install pywebview>=5.0
```

## Usage

### Library

`ICEGuard.convert()` is a **generator** that yields progress events and writes the converted file incrementally. Iterate over it to drive the conversion:

```python
from tmx_ice_guard import ICEGuard

for event in ICEGuard.convert(
    in_file="example.tmx",
    out_file="example_converted.tmx",
    source_platform="auto",   # auto-detect from creationtool header
    target_platform="xtm",
    pretty=False,
):
    if event["type"] == "flavor":
        print(f"Detected source platform: {event['platform']}")
    elif event["type"] == "tu_progress":
        print(f"Processed {event['count']} TUs…")
    elif event["type"] == "done":
        print(f"Done — {event['count']} TUs converted "
              f"({event['source_platform']} → {event['target_platform']})")
```

**Event types**

| `type`        | Extra keys                              | When emitted                              |
|---------------|-----------------------------------------|-------------------------------------------|
| `flavor`      | `platform`                              | Once, after source platform is detected   |
| `tu_progress` | `count`                                 | Every 1 000 TUs                           |
| `done`        | `count`, `source_platform`, `target_platform` | After all TUs have been written     |

### Desktop GUI

1. Install pywebview: `pip install pywebview>=5.0`
2. From the project root, run:

```bash
python gui/app.py
```

The GUI lets you select one or more TMX files, choose an output folder and platform pair, and monitor per-file progress in a table.

## Supported Platforms

| Key         | Display name                   | Context level | Prev-text property        | Next-text property        |
|-------------|--------------------------------|---------------|---------------------------|---------------------------|
| `phrase`    | Phrase                         | tuv           | `context_prev`            | `context_next`            |
| `memoq`     | memoQ                          | tuv           | `x-context-pre`           | `x-context-post`          |
| `xtm`       | XTM                            | tu            | `x-previous-source-text`  | `x-next-source-text`      |
| `gl`        | TransPerfect (GL / Wordfast)   | tu            | `previousMd5Segment`      | `nextMd5Segment`          |
| `trados`    | RWS (Trados)                   | tu            | `x-ContextContent`        | —                         |
| `transifex` | Transifex                      | tu            | `context`                 | —                         |

Pass `source_platform="auto"` to let the library detect the platform automatically.

## Requirements

- Python 3.7 or higher
- No additional dependencies for the library
- `pywebview >= 5.0` for the desktop GUI only

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

For questions or further details, feel free to contact the author!