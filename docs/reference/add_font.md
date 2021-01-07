## add_font ##

```python
fpdf.add_font(family: str, style = '', fname = '', uni = False)
```

### Description ###

Imports a TrueType, OpenType or Type1 font and makes it available.

**Warning:** for Type1 and legacy fonts it is necessary to generate a font definition file first with the `MakeFont` utility. This feature is currently deprecated in favour of TrueType Unicode font support (whose fonts are automatically processed with the included `ttfonts.py` utility).

**Note**: the font source files must be accessible. They are searched successively in (if these constants are defined):

  * `FPDF_FONTPATH` (by default, the `font` folder in the fpdf package directory)
  * `SYSTEM_TTFONTS` (e.g. `C:\WINDOWS\FONTS`)

If the file corresponding to the requested font is not found, the runtime exception "TTF Font file not found: ..." is raised.

For more information, see the [Unicode](../Unicode.md) support page.

This method should be called before the [set_font](set_font.md) method is used, and the font will be available for the whole document.

**Note**: due to the fact that font processing can occupy large amount of time, some data are cached.

Cache files are created in same folder by default. This can be changed by setting the `FPDF_CACHE_MODE` constant:

  * 0 - (by default), store the cache in the same folder as the font file
  * 1 - disable all caching
  * 2 - store cache files in the `FPDF_CACHE_DIR` directory with cryptic names

### Parameters ###

family:
> Font family. Used as a reference for [set_font](set_font.md), for example: `'dejavu'`.

style:
> Font style. Deprecated, maintained only for backward compatibility.

fname:
> Font file name (e.g. `'DejaVuSansCondensed.ttf'`). You can specify a full path; if not, the file will be searched in `FPDF_FONTPATH` or `SYSTEM_TTFONTS`.

uni:
> TTF Unicode flag (if set to `True`, TrueType font subset embedding will be enabled and text will be treated as `utf8` by default).

You must _not_ call _add_font_ for the standard PDF Latin-1 fonts (Courier, Helvetica, Times, Symbol, Zapfdingbats); use [set_font](set_font.md) directly in that case.

Calling this method with uni=False is discouraged as legacy font support is complex and deprecated.


### Example ###

```python
# Add a Unicode free font
pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)

# Add a Unicode system font (using full path)
pdf.add_font('sysfont', '', r"c:\WINDOWS\Fonts\arial.ttf", uni=True)
```

### See also ###

[set_font](set_font.md), [set_font_size](set_font_size.md), [cell](cell.md), [multi_cell](multi_cell.md), [write](write.md).
