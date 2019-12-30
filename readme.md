# Consolig

Consolig is a version of Consolas that supports ligatures. Unlike other efforts, all ligatures in Consolig were made by hand from the original Consolas glyphs (they are not just copied from another ligature font).

Because Consolas cannot be redistributed, this project provides the tools to append the ligature glyphs and features to your personal copy of Consolas, generating a copy of Consolig.

**NOTE: For the pre-release, all font styles use the same ligature glyphs. Making style-specific glyphs is my next goal.**

## How to build

1. Copy your Consolas font files into the Consolig `/input` directory. On Windows, your Consolas files are located in `/Windows/Fonts` on your OS drive. The valid filenames are:
   - `consola.ttf` - Regular
   - `consolab.ttf` - Bold
   - `consolai.ttf` - Italic
   - `consolaz.ttf` - Bold Italic
2. Make sure that you have Python 3 and Python 3 PIP installed.
3. Install the required Python libraries.<br>
   `pip3 install defcon ufo2ft`
4. Execute the build script.
   - Linux<br>
     `python3 build.py`
   - Windows<br>
     `py build.py`
5. If everything goes well, you should now have Consolig font files in your `/build` directory.

## Credits

- Glyph substitution logic was taken from [Cascadia Code](https://github.com/microsoft/cascadia-code).
