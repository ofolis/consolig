from pathlib import Path

import argparse
import extractor
import fontmake.instantiator
import fontTools.designspaceLib
import defcon
import os
import shutil
import ufo2ft
import ufoLib2
import fontTools

from inspect import getmembers
from pprint import pprint

# Static vars
BUILD_DIR = Path("build/")
DESIGNSPACE_FILE = "Consolig.designspace"
INPUT_DIR = Path("input/")
INPUT_STYLE_MAP = {
    "Bold": {
        "font_file": "consolab.ttf",
        "ufo_directory": "Consolig-Bold.ufo"
    },
    "Bold Italic": {
        "font_file": "consolaz.ttf",
        "ufo_directory": "Consolig-Bold-Italic.ufo"
    },
    "Italic": {
        "font_file": "consolai.ttf",
        "ufo_directory": "Consolig-Italic.ufo"
    },
    "Regular": {
        "font_file": "consola.ttf",
        "ufo_directory": "Consolig-Regular.ufo"
    }
}
SOURCES_DIR = Path("sources/")
TEMP_DIR = Path("temp/")


def step_merge_glyphs_from_ufo(path):
    def _merge(instance):
        ufo = ufoLib2.Font.open(path)
        print(f"[{instance.info.familyName} {instance.info.styleName}] Merging glyphs from \"{path}\".")
        for glyph in ufo.glyphOrder:
            if glyph not in instance.glyphOrder:
                instance.addGlyph(ufo[glyph])
    return _merge


def step_set_feature_file(n):
    fea = n.read_text()

    def _set(instance):
        print(f"[{instance.info.familyName} {instance.info.styleName}] Setting feature file from \"{n}\".")
        instance.features.text = fea
    return _set


def build_font_instance(generator, instance_descriptor, *steps):
    instance = generator.generate_instance(instance_descriptor)
    for step in steps:
        step(instance)
    setattr(instance.info, "openTypeOS2Panose",
            [2, 11, 6, 9, 2, 0, 0, 2, 0, 4])
    instance.info.openTypeGaspRangeRecords = [
        {
            "rangeMaxPPEM": 9,
            "rangeGaspBehavior": [1, 3]
        },
        {
            "rangeMaxPPEM": 50,
            "rangeGaspBehavior": [0, 1, 2, 3]
        },
        {
            "rangeMaxPPEM": 65535,
            "rangeGaspBehavior": [1, 3]
        },
    ]
    family_name = instance.info.familyName
    style_name = instance.info.styleName
    file_name = f"{family_name}.ttf".replace(" ", "")
    file_path = BUILD_DIR / file_name
    print(f"[{family_name} {style_name}] Compiling font.")
    instance_font = ufo2ft.compileTTF(
        instance, removeOverlaps=False, inplace=True)
    print(f"[{family_name} {style_name}] Saving font.")
    instance_font.save(file_path)
    print(f"[{family_name} {style_name}] Completed font at \"{file_path}\".")


if __name__ == "__main__":
    # Get args
    parser = argparse.ArgumentParser(description="build some fonts")
    parser.add_argument("-N", "--no-nerdfonts",
                        default=False, action="store_true")
    parser.add_argument("-P", "--no-powerline",
                        default=False, action="store_true")
    parser.add_argument("-M", "--no-mono", default=False, action="store_true")
    args = parser.parse_args()
    # Set up temp directory
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCES_DIR / DESIGNSPACE_FILE,
                    TEMP_DIR / DESIGNSPACE_FILE)
    for style_name in INPUT_STYLE_MAP:
        font_file = INPUT_STYLE_MAP[style_name]["font_file"]
        print(f"Attempting to extract UFO for \"{font_file}\".")
        if os.path.exists(INPUT_DIR / font_file):
            ufo_directory = INPUT_STYLE_MAP[style_name]["ufo_directory"]
            ufo = defcon.Font()
            extractor.extractUFO(
                (INPUT_DIR / font_file), ufo)
            ufo.save(TEMP_DIR / ufo_directory)
            print(f"UFO extracted to \"{ufo_directory}\".")
        else:
            print(f"Input font file is missing. Skipping.")
    # Load Designspace and filter out instances that are marked as non-exportable.
    designspace = fontTools.designspaceLib.DesignSpaceDocument.fromfile(
        TEMP_DIR / DESIGNSPACE_FILE)
    designspace.instances = [
        s
        for s in designspace.instances
        if s.lib.get("com.schriftgestaltung.export", True)
    ]
    # Prepare masters.
    generator = fontmake.instantiator.Instantiator.from_designspace(
        designspace)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    for instance_descriptor in designspace.instances:
        if instance_descriptor.styleName not in INPUT_STYLE_MAP:
            print(
                f"Cannot process instance. Style name \"{instance_descriptor.styleName}\" is not defined in map.")
            continue
        print(f"Building style \"{instance_descriptor.styleName}\".")
        # Define steps
        source_ufo_directory = SOURCES_DIR / \
            INPUT_STYLE_MAP[instance_descriptor.styleName]["ufo_directory"]
        step_merge_ligatures = step_merge_glyphs_from_ufo(source_ufo_directory)
        step_replace_features = step_set_feature_file(
            source_ufo_directory / "features.fea")
        # Build font
        build_font_instance(generator, instance_descriptor,
                            step_merge_ligatures, step_replace_features)
        print(
            f"Completed build for style \"{instance_descriptor.styleName}\".")
        print("*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***")
    shutil.rmtree(TEMP_DIR)
    print("All build tasks are complete.")
