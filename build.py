from fontTools.feaLib.builder import addOpenTypeFeatures
from fontTools.ttLib import TTFont
from os import getcwd, path
from pathlib import Path
from shutil import rmtree
from xml.etree import ElementTree

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
        "inputFile": "consola.ttf",
        "outputFile": "Consolig-Regular.ttf",
        "sourceFile": "consolig-regular.ttf",
    },
    {
        "featureFile": "features.fea",
        "inputFile": "consolab.ttf",
        "outputFile": "Consolig-Bold.ttf",
        "sourceFile": "consolig-bold.ttf",
    },
    {
        "featureFile": "features.fea",
        "inputFile": "consolai.ttf",
        "outputFile": "Consolig-Italic.ttf",
        "sourceFile": "consolig-italic.ttf",
    },
    {
        "featureFile": "features.fea",
        "inputFile": "consolaz.ttf",
        "outputFile": "Consolig-BoldItalic.ttf",
        "sourceFile": "consolig-bold-italic.ttf",
    }
]

if __name__ == "__main__":
    # Perform startup tasks.
    print("Setting up directories")
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    for config in STYLE_CONFIGS:
        # Get properties from config.
        feature_file_path = SOURCES_DIR / config["featureFile"]
        input_file_path = INPUT_DIR / config["inputFile"]
        output_file_path = BUILD_DIR / config["outputFile"]
        source_file_path = SOURCES_DIR / config["sourceFile"]
        print(f"Processing source at \"{source_file_path}\"")
        if path.exists(source_file_path) and path.exists(input_file_path):
            # Output TTX (XML) files for fonts
            print("  Exporting XML from TTF files")
            input_font = TTFont(input_file_path)
            input_font.saveXML(TEMP_DIR / 'input.ttx')
            source_font = TTFont(source_file_path)
            source_font.saveXML(TEMP_DIR / 'source.ttx')
            # Set up XML trees
            print("  Parsing XML element trees")
            input_et = ElementTree.parse(TEMP_DIR / 'input.ttx')
            source_et = ElementTree.parse(TEMP_DIR / 'source.ttx')
            # Create glyph whitelist
            print("  Creating glyph whitelist")
            extra_names_element = source_et.getroot().find('post').find('extraNames')
            if extra_names_element == None:
                raise ValueError('Could not find "extraNames" element in source XML')
            glyph_whitelist = []
            for ps_name_element in extra_names_element.findall('psName'):
                ps_name_element_name = ps_name_element.attrib['name']
                if ps_name_element_name == None:
                    raise ValueError('Encountered source "psName" element with no "name" attribute')
                glyph_whitelist.append(ps_name_element_name)
            # Append new GlyphID elements
            print("  Appending new glyph IDs")
            input_glyph_order_element = input_et.getroot().find('GlyphOrder')
            if input_glyph_order_element == None:
                raise ValueError('Could not find "GlyphOrder" element in input XML')
            last_glyph_id = -1
            for glyph_id_element in input_glyph_order_element.findall('GlyphID'):
                glyph_id_element_id = glyph_id_element.attrib['id']
                if glyph_id_element_id == None:
                    raise ValueError('Encountered input "GlyphID" element with no "id" attribute')
                glyph_id_element_id = int(glyph_id_element_id)
                if glyph_id_element_id > last_glyph_id:
                    last_glyph_id = glyph_id_element_id
            glyph_id_map = {}
            source_glyph_order_element = source_et.getroot().find('GlyphOrder')
            if source_glyph_order_element == None:
                raise ValueError('Could not find "GlyphOrder" element in source XML')
            next_glyph_id = last_glyph_id + 1
            for glyph_id_element in source_glyph_order_element.findall('GlyphID'):
                glyph_id_element_id = glyph_id_element.attrib['id']
                glyph_id_element_name = glyph_id_element.attrib['name']
                if glyph_id_element_id == None or glyph_id_element_name == None:
                    raise ValueError('Encountered source "GlyphID" element with invalid attributes')
                if glyph_id_element_name in glyph_whitelist:
                    revised_glyph_id_element = ElementTree.SubElement(input_glyph_order_element, 'GlyphID', id = str(next_glyph_id), name = glyph_id_element_name)
                    glyph_id_map[glyph_id_element_id] = next_glyph_id
                    next_glyph_id += 1
            # Append new mtx elements
            print("  Appending new glyph spacing definitions")
            input_hmtx_element = input_et.getroot().find('hmtx')
            if input_hmtx_element == None:
                raise ValueError('Could not find "hmtx" element in input XML')
            source_hmtx_element = source_et.getroot().find('hmtx')
            if source_hmtx_element == None:
                raise ValueError('Could not find "hmtx" element in source XML')
            for mtx_element in source_hmtx_element.findall('mtx'):
                mtx_element_name = mtx_element.attrib['name']
                if mtx_element_name == None:
                    raise ValueError('Encountered source "mtx" element with no "name" attribute')
                if mtx_element_name in glyph_whitelist:
                    input_hmtx_element.append(mtx_element)
            # Append new map elements
            print("  Appending new glyph map entries")
            input_cmap_element = input_et.getroot().find('cmap')
            if input_cmap_element == None:
                raise ValueError('Could not find "cmap" element in input XML')
            input_cmap_format_map = {}
            for child_element in input_cmap_element:
                if child_element.tag.startswith('cmap_format'):
                    child_element_language = child_element.attrib['language']
                    child_element_plat_enc_id = child_element.attrib['platEncID']
                    child_element_platform_id = child_element.attrib['platformID']
                    if child_element_language == None or child_element_plat_enc_id == None or child_element_platform_id == None:
                        raise ValueError('Encountered input "cmap" child element with invalid attributes')
                    key_string = f"{child_element.tag}|{child_element_language}|{child_element_plat_enc_id}|{child_element_platform_id}"
                    if key_string in input_cmap_format_map:
                        raise ValueError('Encountered two identical input "cmap" child elements')
                    input_cmap_format_map[key_string] = child_element
            source_cmap_element = source_et.getroot().find('cmap')
            if source_cmap_element == None:
                raise ValueError('Could not find "cmap" element in source XML')
            source_cmap_formats = []
            for child_element in source_cmap_element:
                if child_element.tag.startswith('cmap_format'):
                    child_element_language = child_element.attrib['language']
                    child_element_plat_enc_id = child_element.attrib['platEncID']
                    child_element_platform_id = child_element.attrib['platformID']
                    if child_element_language == None or child_element_plat_enc_id == None or child_element_platform_id == None:
                        raise ValueError('Encountered source "cmap" child element with invalid attributes')
                    key_string = f"{child_element.tag}|{child_element_language}|{child_element_plat_enc_id}|{child_element_platform_id}"
                    if key_string in source_cmap_formats:
                        raise ValueError('Encountered two identical source "cmap" child elements')
                    if key_string in input_cmap_format_map:
                        for map_element in child_element.findall('map'):
                            map_element_name = map_element.attrib['name']
                            if map_element_name == None:
                                raise ValueError('Encountered source "map" element with no "name" attribute')
                            if map_element_name in glyph_whitelist:
                                input_cmap_format_map[key_string].append(map_element)
                    else:
                        new_cmap_format_element = ElementTree.Element(child_element.tag, language = child_element_language, platEncID = child_element_plat_enc_id, platformID = child_element_platform_id)
                        total_map_elements = 0
                        for map_element in child_element.findall('map'):
                            map_element_name = map_element.attrib['name']
                            if map_element_name == None:
                                raise ValueError('Encountered source "map" element with no "name" attribute')
                            if map_element_name in glyph_whitelist:
                                new_cmap_format_element.append(map_element)
                                total_map_elements += 1
                        if total_map_elements > 0:
                            input_cmap_element.append(new_cmap_format_element)
            # Append new TTGlyph elements
            print("  Appending new glyph geometry")
            input_glyf_element = input_et.getroot().find('glyf')
            if input_glyf_element == None:
                raise ValueError('Could not find "glyf" element in input XML')
            source_glyf_element = source_et.getroot().find('glyf')
            if source_glyf_element == None:
                raise ValueError('Could not find "glyf" element in source XML')
            for tt_glyph_element in source_glyf_element.findall('TTGlyph'):
                tt_glyph_element_name = tt_glyph_element.attrib['name']
                if tt_glyph_element_name == None:
                    raise ValueError('Encountered source "TTGlyph" element with no "name" attribute')
                if tt_glyph_element_name in glyph_whitelist:
                    input_glyf_element.append(tt_glyph_element)
            # Append new fpgm data
            print("  Appending new raster hint programming")
            input_fpgm_assembly_element = input_et.getroot().find('fpgm').find('assembly')
            if input_fpgm_assembly_element == None:
                raise ValueError('Could not find "assembly" element in input XML')
            source_fpgm_assembly_element = source_et.getroot().find('fpgm').find('assembly')
            if source_fpgm_assembly_element == None:
                raise ValueError('Could not find "assembly" element in source XML')
            input_fpgm_assembly_element.text += source_fpgm_assembly_element.text
            # Replace name element
            print("  Replacing font name and meta")
            input_name_element = input_et.getroot().find('name')
            if input_name_element == None:
                raise ValueError('Could not find "name" element in input XML')
            source_name_element = source_et.getroot().find('name')
            if source_name_element == None:
                raise ValueError('Could not find "name" element in source XML')
            input_et.getroot().remove(input_name_element)
            input_et.getroot().append(source_name_element)
            # Add extraNames element
            print("  Adding glyph name definitions")
            input_post_element = input_et.getroot().find('post')
            if input_post_element == None:
                raise ValueError('Could not find "post" element in input XML')
            source_post_element = source_et.getroot().find('post')
            if source_post_element == None:
                raise ValueError('Could not find "post" element in source XML')
            input_extra_names_element = input_post_element.find('extraNames')
            if input_extra_names_element != None:
                raise ValueError('Found "extraNames" element in input XML (this should not happen)')
            source_extra_names_element = source_post_element.find('extraNames')
            if source_extra_names_element == None:
                raise ValueError('Could not find "extraNames" element in source XML')
            input_post_element.append(source_extra_names_element)
            input_et.write(TEMP_DIR / 'output.ttx')
            output_font = TTFont(input_file_path)
            output_font.importXML(TEMP_DIR / 'output.ttx')
            # Set up substitution functionality.
            print("  Adding ligature substitution functionality")
            addOpenTypeFeatures(output_font, feature_file_path)
            # Save font.
            print("  Saving revised font to TTF file")
            output_font.save(output_file_path)
            output_font.close()
            print(f"Completed font \"{output_file_path}\"")
        else:
            print(f"Skipping missing input file \"{input_file_path}\"")
    # Perform cleanup tasks.
    print("Cleaning up directories")
    rmtree(TEMP_DIR)
    print("All build tasks are complete")