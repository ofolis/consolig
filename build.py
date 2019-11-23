from pathlib import Path

import argparse
import extractor
import defcon

# List of font build configurations
fonts = [
    {
        "input_font": "consola.ttf",
        "ligature_ufo": "Consolig-Regular.ufo"
    }
]

# Define paths
build_dir = Path("build/")
input_dir = Path("input/")
temp_dir = Path("temp/")

# Set up paths
build_dir.mkdir(parents=True, exist_ok=True)
temp_dir.mkdir(parents=True, exist_ok=True)

for font in fonts:
    # Extract UFO from input font
    ufo = defcon.Font()
    extractor.extractUFO((input_dir / font["input_font"]), ufo)
    ufo.save(temp_dir / (font["input_font"] + ".ufo"))