from defcon import Font
from fontTools import merge
from fontTools.feaLib.builder import addOpenTypeFeatures
from fontTools.ufoLib import fontInfoAttributesVersion3, UFOReader
from os import getcwd, path
from pathlib import Path
from shutil import rmtree
from ufo2ft import compileTTF

# Directories
CWD = Path(getcwd())
BUILD_DIR = Path(CWD / "build/")
INPUT_DIR = Path(CWD / "input/")
SOURCES_DIR = Path(CWD / "sources/")
TEMP_DIR = Path(CWD / "temp/")
# Configs
STYLE_CONFIGS = [
    {
        "featureFile": "features.fea",
        "fileName": "Consolig-Regular",
        "inputFile": "consola.ttf"
    },
    {
        "featureFile": "features.fea",
        "fileName": "Consolig-Bold",
        "inputFile": "consolab.ttf"
    },
    {
        "featureFile": "features.fea",
        "fileName": "Consolig-Italic",
        "inputFile": "consolai.ttf"
    },
    {
        "featureFile": "features.fea",
        "fileName": "Consolig-BoldItalic",
        "inputFile": "consolaz.ttf"
    }
]
# Maps
NAME_INFO_MAP = {
    "0": "copyright",
    "1": "familyName",
    "2": "styleName",
    "3": "postscriptUniqueID",
    "4": "postscriptFullName",
    "5": "openTypeNameVersion",
    "6": "postscriptFontName",
    "7": "trademark",
    "8": "openTypeNameManufacturer",
    "9": "openTypeNameDesigner",
    "10": "openTypeNameDescription",
    "11": "openTypeNameManufacturerURL",
    "12": "openTypeNameDesignerURL",
    "13": "openTypeNameLicense",
    "14": "openTypeNameLicenseURL",
    "16": "openTypeNameWWSFamilyName",
    "17": "openTypeNamePreferredSubfamilyName",
    "18": "openTypeNamePreferredFamilyName",
    "19": "openTypeNameSampleText",
    "21": "openTypeNameWWSFamilyName",
    "22": "openTypeNameWWSSubfamilyName"
}

class Info(object):
    def __init__(self):
        for attr in fontInfoAttributesVersion3:
            setattr(self, attr, None)

def mergeTtfFiles(ttf_file_list):
    merger = merge.Merger()
    merged_tt_font = merger.merge(ttf_file_list)
    return merged_tt_font

def saveUfoToTtf(ufo_path, ttf_path):
    ufo = Font(ufo_path)
    ttf = compileTTF(ufo)
    ttf.save(ttf_path)

def updateNames(tt_font, ufo_reader):
    # Get info from UFO.
    info = Info()
    ufo_reader.readInfo(info)
    # Update name table.
    tt_name_table = tt_font["name"]
    for name in tt_name_table.names:
        name_id_string = str(name.nameID)
        if name_id_string not in NAME_INFO_MAP:
            continue
        info_property = NAME_INFO_MAP[name_id_string]
        if not hasattr(info, info_property):
            continue
        value = getattr(info, info_property)
        if value == None:
            continue
        tt_name_table.setName(value, name.nameID, name.platformID, name.platEncID, name.langID)

if __name__ == "__main__":
    # Perform startup tasks.
    print("Setting up directories.")
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    for config in STYLE_CONFIGS:
        # Get properties from config.
        feature_file_path = SOURCES_DIR / config["featureFile"]
        input_file_path = INPUT_DIR / config["inputFile"]
        output_file_path = BUILD_DIR / (config["fileName"] + ".ttf")
        source_file_path = SOURCES_DIR / (config["fileName"] + ".ufo")
        temp_file_path = TEMP_DIR / (config["fileName"] + ".ttf")
        print(f"Processing UFO source at \"{source_file_path}\".")
        if path.exists(input_file_path):
            # Convert Consolig to TTF.
            print(f"Converting UFO to TTF.")
            saveUfoToTtf(source_file_path, temp_file_path)
            # Merge TTF fonts.
            print(f"Merging TrueType data.")
            merged_tt_font = mergeTtfFiles([
                input_file_path,
                temp_file_path
            ])
            # Set up substitution functionality.
            print(f"Writing TrueType features.")
            addOpenTypeFeatures(merged_tt_font, feature_file_path)
            # Update font names.
            print(f"Updating TrueType names from UFO information.")
            consolig_ufo_reader = UFOReader(source_file_path)
            updateNames(merged_tt_font, consolig_ufo_reader)
            # Save font.
            print(f"Saving to TTF file.")
            merged_tt_font.save(output_file_path)
            merged_tt_font.close()
            print(f"Completed font \"{output_file_path}\".")
        else:
            print(f"Could not find input file \"{input_file_path}\". Skipping.")
        print("*** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***")
    # Perform cleanup tasks.
    print("Cleaning up directories.")
    rmtree(TEMP_DIR)
    print("All build tasks are complete.")