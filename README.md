# TMX Ice Guard

TMX Ice Guard is a Python library designed to facilitate conversion between different **TMX (Translation Memory eXchange)** file formats. TMX is widely used in translation and localization workflows, and this library simplifies handling various TMX "flavors" through an easy and customizable interface.

## Features

- **Convert TMX formats:** Seamlessly transform between different flavors of TMX files.
- **Maintain data integrity:** Ensure the conversion process retains the full fidelity of translation memory data.
- **Lightweight and easy to use:** Designed for developers with minimal dependencies.
- **Extendable:** Add support for custom TMX processing or transformations as needed.

## Installation

You can install this package directly using `pip`:

```bash
pip install tmx-ice-guard
```

## Usage

Here's a quick example of how to use the library:

```python
from tmx_ice_guard import ICEGuard as IG

# Load an example TMX file and convert to a desired format
input_file = "example.tmx"
output_file = "converted_example.tmx"
src_platform = "auto"
tar_platform = "xtm"

IG.convert(in_file=input_file, out_file=output_file,source_platform=src_platform,
                target_platform=tar_platform)

print("Conversion complete!")
```

## Requirements

- Python 3.7 or higher
- No additional dependencies


## License

TBD

---

For questions or further details, feel free to contact the author!