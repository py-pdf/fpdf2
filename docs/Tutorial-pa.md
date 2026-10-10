# ਟਿਊਟੋਰੀਅਲ #

ਮੈਥਡਾਂ ਦੀ ਪੂਰੀ ਡਾਕੂਮੈਂਟੇਸ਼ਨ: [`fpdf.FPDF` API ਡੌਕ](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

## ਟਿਊਟੋ 1 - ਸਭ ਤੋਂ ਸਧਾਰਨ ਉਦਾਹਰਨ ##

ਆਓ ਕਲਾਸਿਕ ਉਦਾਹਰਨ ਨਾਲ ਸ਼ੁਰੂ ਕਰੀਏ:

```python
{% include "../tutorial/tuto1.py" %}
```

[ਨਤੀਜਾ PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto1.pdf)

ਲਾਇਬ੍ਰੇਰੀ ਫਾਈਲ ਨੂੰ ਸ਼ਾਮਲ ਕਰਨ ਤੋਂ ਬਾਅਦ, ਅਸੀਂ ਇੱਕ `FPDF` ਆਬਜੈਕਟ ਬਣਾਉਂਦੇ ਹਾਂ।
[FPDF](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF) ਕੰਸਟਰਕਟਰ ਇੱਥੇ ਡਿਫਾਲਟ ਵੈਲਿਊਜ਼ ਨਾਲ ਵਰਤਿਆ ਗਿਆ ਹੈ:
ਪੰਨੇ A4 ਪੋਰਟਰੇਟ ਵਿੱਚ ਹਨ ਅਤੇ ਮਾਪ ਦੀ ਇਕਾਈ ਮਿਲੀਮੀਟਰ ਹੈ।
ਇਸ ਨੂੰ ਸਪੱਸ਼ਟ ਤੌਰ 'ਤੇ ਇਸ ਤਰ੍ਹਾਂ ਨਿਰਧਾਰਤ ਕੀਤਾ ਜਾ ਸਕਦਾ ਸੀ:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

PDF ਨੂੰ ਲੈਂਡਸਕੇਪ ਮੋਡ (`L`) ਵਿੱਚ ਸੈੱਟ ਕਰਨਾ ਜਾਂ ਹੋਰ ਪੰਨਾ ਫਾਰਮੈਟ
(ਜਿਵੇਂ ਕਿ `Letter` ਅਤੇ `Legal`) ਅਤੇ ਮਾਪ ਇਕਾਈਆਂ (`pt`, `cm`, `in`) ਵਰਤਣਾ ਸੰਭਵ ਹੈ।

ਇਸ ਵੇਲੇ ਕੋਈ ਪੰਨਾ ਨਹੀਂ ਹੈ, ਇਸ ਲਈ ਸਾਨੂੰ
[add_page](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page) ਨਾਲ ਇੱਕ ਜੋੜਨਾ ਪਵੇਗਾ। ਮੂਲ ਬਿੰਦੂ ਉੱਪਰ-ਖੱਬੇ ਕੋਨੇ ਵਿੱਚ ਹੈ ਅਤੇ
ਮੌਜੂਦਾ ਸਥਿਤੀ ਡਿਫਾਲਟ ਤੌਰ 'ਤੇ ਬਾਰਡਰਾਂ ਤੋਂ 1 ਸੈਂਟੀਮੀਟਰ ਦੂਰ ਰੱਖੀ ਜਾਂਦੀ ਹੈ; ਮਾਰਜਿਨ ਨੂੰ
[set_margins](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins) ਨਾਲ ਬਦਲਿਆ ਜਾ ਸਕਦਾ ਹੈ।

ਟੈਕਸਟ ਪ੍ਰਿੰਟ ਕਰਨ ਤੋਂ ਪਹਿਲਾਂ,
[set_font](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) ਨਾਲ ਫੌਂਟ ਚੁਣਨਾ ਲਾਜ਼ਮੀ ਹੈ, ਨਹੀਂ ਤਾਂ ਡੌਕੂਮੈਂਟ ਅਵੈਧ ਹੋਵੇਗਾ।
ਅਸੀਂ Helvetica ਬੋਲਡ 16 ਚੁਣਦੇ ਹਾਂ:

```python
pdf.set_font('Helvetica', style='B', size=16)
```

ਅਸੀਂ `I` ਨਾਲ ਇਟੈਲਿਕ, `U` ਨਾਲ ਅੰਡਰਲਾਈਨ ਜਾਂ ਖਾਲੀ ਸਟ੍ਰਿੰਗ ਨਾਲ ਰੈਗੂਲਰ ਫੌਂਟ ਨਿਰਧਾਰਤ ਕਰ ਸਕਦੇ ਸੀ
(ਜਾਂ ਕੋਈ ਵੀ ਕੰਬੀਨੇਸ਼ਨ)। ਨੋਟ ਕਰੋ ਕਿ ਫੌਂਟ ਸਾਈਜ਼ ਪੁਆਇੰਟਸ ਵਿੱਚ ਦਿੱਤਾ ਗਿਆ ਹੈ,
ਮਿਲੀਮੀਟਰ (ਜਾਂ ਹੋਰ ਯੂਜ਼ਰ ਯੂਨਿਟ) ਵਿੱਚ ਨਹੀਂ; ਇਹ ਇੱਕੋ ਇੱਕ ਅਪਵਾਦ ਹੈ।
ਹੋਰ ਬਿਲਟ-ਇਨ ਫੌਂਟ ਹਨ `Times`, `Courier`, `Symbol` ਅਤੇ `ZapfDingbats`।

ਅਸੀਂ ਹੁਣ [cell](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) ਨਾਲ ਇੱਕ ਸੈੱਲ ਪ੍ਰਿੰਟ ਕਰ ਸਕਦੇ ਹਾਂ। ਸੈੱਲ ਇੱਕ ਆਇਤਾਕਾਰ ਖੇਤਰ ਹੈ,
ਸੰਭਵ ਤੌਰ 'ਤੇ ਫਰੇਮ ਵਾਲਾ, ਜਿਸ ਵਿੱਚ ਕੁਝ ਟੈਕਸਟ ਹੁੰਦਾ ਹੈ। ਇਹ ਮੌਜੂਦਾ ਸਥਿਤੀ 'ਤੇ ਰੈਂਡਰ ਹੁੰਦਾ ਹੈ।
ਅਸੀਂ ਇਸ ਦੇ ਅਕਾਰ, ਟੈਕਸਟ (ਕੇਂਦਰਿਤ ਜਾਂ ਅਲਾਈਨ), ਬਾਰਡਰ ਖਿੱਚਣੇ ਹਨ ਜਾਂ ਨਹੀਂ, ਅਤੇ ਮੌਜੂਦਾ ਸਥਿਤੀ
ਇਸ ਤੋਂ ਬਾਅਦ ਕਿੱਥੇ ਜਾਂਦੀ ਹੈ (ਸੱਜੇ, ਹੇਠਾਂ ਜਾਂ ਅਗਲੀ ਲਾਈਨ ਦੀ ਸ਼ੁਰੂਆਤ 'ਤੇ) ਨਿਰਧਾਰਤ ਕਰਦੇ ਹਾਂ।
ਫਰੇਮ ਜੋੜਨ ਲਈ, ਅਸੀਂ ਇਹ ਕਰਾਂਗੇ:

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

ਇਸ ਦੇ ਨਾਲ ਕੇਂਦਰਿਤ ਟੈਕਸਟ ਨਾਲ ਨਵਾਂ ਸੈੱਲ ਜੋੜਨ ਅਤੇ ਅਗਲੀ ਲਾਈਨ 'ਤੇ ਜਾਣ ਲਈ,
ਅਸੀਂ ਇਹ ਕਰਾਂਗੇ:

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**ਨੋਟ**: ਲਾਈਨ ਬ੍ਰੇਕ [ln](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.ln) ਨਾਲ ਵੀ ਕੀਤੀ ਜਾ ਸਕਦੀ ਹੈ। ਇਹ
ਮੈਥਡ ਬ੍ਰੇਕ ਦੀ ਉਚਾਈ ਵੀ ਨਿਰਧਾਰਤ ਕਰਨ ਦੀ ਆਗਿਆ ਦਿੰਦਾ ਹੈ।

ਅਖੀਰ ਵਿੱਚ, ਡੌਕੂਮੈਂਟ ਬੰਦ ਕੀਤਾ ਜਾਂਦਾ ਹੈ ਅਤੇ ਦਿੱਤੇ ਫਾਈਲ ਪਾਥ ਅਧੀਨ
[output](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.output) ਨਾਲ ਸੇਵ ਕੀਤਾ ਜਾਂਦਾ ਹੈ। ਬਿਨਾਂ ਕਿਸੇ ਪੈਰਾਮੀਟਰ ਦੇ, `output()`
PDF `bytearray` ਬਫਰ ਵਾਪਸ ਕਰਦਾ ਹੈ।

## ਟਿਊਟੋ 2 - ਹੈਡਰ, ਫੁੱਟਰ, ਪੇਜ ਬ੍ਰੇਕ ਅਤੇ ਚਿੱਤਰ ##

ਇੱਥੇ ਹੈਡਰ, ਫੁੱਟਰ ਅਤੇ ਲੋਗੋ ਵਾਲੀ ਦੋ ਪੰਨਿਆਂ ਦੀ ਉਦਾਹਰਨ ਹੈ:

```python
{% include "../tutorial/tuto2.py" %}
```

[ਨਤੀਜਾ PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto2.pdf)

ਇਹ ਉਦਾਹਰਨ ਪੰਨਾ ਹੈਡਰ ਅਤੇ ਫੁੱਟਰ ਪ੍ਰੋਸੈੱਸ ਕਰਨ ਲਈ [header](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.header) ਅਤੇ
[footer](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) ਮੈਥਡਾਂ ਦੀ ਵਰਤੋਂ ਕਰਦੀ ਹੈ। ਇਹ
ਆਟੋਮੈਟਿਕ ਕਾਲ ਹੁੰਦੇ ਹਨ। ਇਹ FPDF ਕਲਾਸ ਵਿੱਚ ਪਹਿਲਾਂ ਤੋਂ ਮੌਜੂਦ ਹਨ ਪਰ ਕੁਝ ਨਹੀਂ ਕਰਦੇ,
ਇਸ ਲਈ ਸਾਨੂੰ ਕਲਾਸ ਨੂੰ ਐਕਸਟੈਂਡ ਕਰਨਾ ਅਤੇ ਇਨ੍ਹਾਂ ਨੂੰ ਓਵਰਰਾਈਡ ਕਰਨਾ ਪਵੇਗਾ।

ਲੋਗੋ [image](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image) ਮੈਥਡ ਨਾਲ ਇਸਦੇ ਉੱਪਰ-ਖੱਬੇ ਕੋਨੇ ਅਤੇ ਚੌੜਾਈ ਨਿਰਧਾਰਤ ਕਰਕੇ ਪ੍ਰਿੰਟ ਕੀਤਾ ਜਾਂਦਾ ਹੈ। ਉਚਾਈ ਚਿੱਤਰ ਦੇ ਅਨੁਪਾਤ ਦੀ ਪਾਲਣਾ ਕਰਨ ਲਈ ਆਟੋਮੈਟਿਕ ਗਿਣੀ ਜਾਂਦੀ ਹੈ।

ਪੰਨਾ ਨੰਬਰ ਪ੍ਰਿੰਟ ਕਰਨ ਲਈ, ਸੈੱਲ ਦੀ ਚੌੜਾਈ ਵਜੋਂ ਇੱਕ ਨੱਲ ਵੈਲਿਊ ਪਾਸ ਕੀਤੀ ਜਾਂਦੀ ਹੈ। ਇਸਦਾ ਮਤਲਬ ਹੈ
ਕਿ ਸੈੱਲ ਪੰਨੇ ਦੇ ਸੱਜੇ ਮਾਰਜਿਨ ਤੱਕ ਫੈਲਣਾ ਚਾਹੀਦਾ ਹੈ; ਇਹ ਟੈਕਸਟ ਕੇਂਦਰਿਤ ਕਰਨ ਲਈ ਸੌਖਾ ਹੈ।
ਮੌਜੂਦਾ ਪੰਨਾ ਨੰਬਰ [page_no](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) ਮੈਥਡ ਦੁਆਰਾ ਵਾਪਸ ਕੀਤਾ ਜਾਂਦਾ ਹੈ;
ਕੁੱਲ ਪੰਨਿਆਂ ਦੀ ਗਿਣਤੀ ਲਈ, ਵਿਸ਼ੇਸ਼ ਵੈਲਿਊ `{nb}` ਵਰਤੀ ਜਾਂਦੀ ਹੈ
ਜੋ ਡੌਕੂਮੈਂਟ ਬੰਦ ਹੋਣ 'ਤੇ ਬਦਲੀ ਜਾਵੇਗੀ (ਇਸ ਵਿਸ਼ੇਸ਼ ਵੈਲਿਊ ਨੂੰ
[alias_nb_pages()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages) ਨਾਲ ਬਦਲਿਆ ਜਾ ਸਕਦਾ ਹੈ)।
ਨੋਟ ਕਰੋ [set_y](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) ਮੈਥਡ ਦੀ ਵਰਤੋਂ ਜੋ ਪੰਨੇ ਵਿੱਚ ਉੱਪਰ ਜਾਂ ਹੇਠਾਂ ਤੋਂ ਸ਼ੁਰੂ ਕਰਕੇ ਪੂਰਨ ਸਥਿਤੀ ਸੈੱਟ ਕਰਨ ਦੀ ਆਗਿਆ ਦਿੰਦੀ ਹੈ।

ਇੱਥੇ ਇੱਕ ਹੋਰ ਦਿਲਚਸਪ ਵਿਸ਼ੇਸ਼ਤਾ ਵਰਤੀ ਗਈ ਹੈ: ਆਟੋਮੈਟਿਕ ਪੇਜ ਬ੍ਰੇਕਿੰਗ। ਜਿਵੇਂ ਹੀ
ਕੋਈ ਸੈੱਲ ਪੰਨੇ ਵਿੱਚ ਸੀਮਾ ਪਾਰ ਕਰੇਗਾ (ਡਿਫਾਲਟ ਤੌਰ 'ਤੇ ਹੇਠੋਂ 2 ਸੈਂਟੀਮੀਟਰ),
ਬ੍ਰੇਕ ਕੀਤੀ ਜਾਂਦੀ ਹੈ ਅਤੇ ਫੌਂਟ ਬਹਾਲ ਕੀਤਾ ਜਾਂਦਾ ਹੈ। ਭਾਵੇਂ ਹੈਡਰ ਅਤੇ
ਫੁੱਟਰ ਆਪਣਾ ਫੌਂਟ (`helvetica`) ਚੁਣਦੇ ਹਨ, ਬਾਡੀ `Times` ਨਾਲ ਜਾਰੀ ਰਹਿੰਦੀ ਹੈ।
ਆਟੋਮੈਟਿਕ ਬਹਾਲੀ ਦੀ ਇਹ ਵਿਧੀ ਰੰਗਾਂ ਅਤੇ ਲਾਈਨ ਦੀ ਚੌੜਾਈ 'ਤੇ ਵੀ ਲਾਗੂ ਹੁੰਦੀ ਹੈ।
ਜੋ ਸੀਮਾ ਪੇਜ ਬ੍ਰੇਕ ਟ੍ਰਿਗਰ ਕਰਦੀ ਹੈ ਉਹ
[set_auto_page_break](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break) ਨਾਲ ਸੈੱਟ ਕੀਤੀ ਜਾ ਸਕਦੀ ਹੈ।


## ਟਿਊਟੋ 3 - ਲਾਈਨ ਬ੍ਰੇਕ ਅਤੇ ਰੰਗ ##

ਆਓ ਇੱਕ ਉਦਾਹਰਨ ਨਾਲ ਜਾਰੀ ਰੱਖੀਏ ਜੋ ਜਸਟੀਫਾਈਡ ਪੈਰਾਗ੍ਰਾਫ ਪ੍ਰਿੰਟ ਕਰਦੀ ਹੈ। ਇਹ
ਰੰਗਾਂ ਦੀ ਵਰਤੋਂ ਵੀ ਦਰਸਾਉਂਦੀ ਹੈ।

```python
{% include "../tutorial/tuto3.py" %}
```

[ਨਤੀਜਾ PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto3.pdf)

[ਜੂਲਸ ਵਰਨ ਟੈਕਸਟ](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

[get_string_width](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) ਮੈਥਡ ਮੌਜੂਦਾ ਫੌਂਟ ਵਿੱਚ ਸਟ੍ਰਿੰਗ ਦੀ ਲੰਬਾਈ ਨਿਰਧਾਰਤ ਕਰਨ ਦੀ ਆਗਿਆ ਦਿੰਦਾ ਹੈ, ਜੋ ਇੱਥੇ ਸਿਰਲੇਖ ਦੇ ਆਲੇ-ਦੁਆਲੇ ਫਰੇਮ ਦੀ ਸਥਿਤੀ ਅਤੇ ਚੌੜਾਈ ਦੀ ਗਣਨਾ ਕਰਨ ਲਈ ਵਰਤਿਆ ਜਾਂਦਾ ਹੈ। ਫਿਰ ਰੰਗ ਸੈੱਟ ਕੀਤੇ ਜਾਂਦੇ ਹਨ
([set_draw_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color),
[set_fill_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) ਅਤੇ
[set_text_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color) ਰਾਹੀਂ) ਅਤੇ ਲਾਈਨ ਦੀ ਮੋਟਾਈ
[set_line_width](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width) ਨਾਲ 1 ਮਿਲੀਮੀਟਰ ਸੈੱਟ ਕੀਤੀ ਜਾਂਦੀ ਹੈ (ਡਿਫਾਲਟ 0.2 ਦੇ ਮੁਕਾਬਲੇ)। ਅਖੀਰ ਵਿੱਚ, ਅਸੀਂ ਸੈੱਲ ਆਉਟਪੁੱਟ ਕਰਦੇ ਹਾਂ (ਆਖਰੀ ਪੈਰਾਮੀਟਰ true ਬੈਕਗ੍ਰਾਊਂਡ ਭਰਨ ਦਾ ਸੰਕੇਤ ਕਰਦਾ ਹੈ)।

ਪੈਰਾਗ੍ਰਾਫ ਪ੍ਰਿੰਟ ਕਰਨ ਲਈ ਵਰਤਿਆ ਜਾਣ ਵਾਲਾ ਮੈਥਡ [multi_cell](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) ਹੈ। ਟੈਕਸਟ ਡਿਫਾਲਟ ਤੌਰ 'ਤੇ ਜਸਟੀਫਾਈਡ ਹੁੰਦਾ ਹੈ।
ਹਰ ਵਾਰ ਜਦੋਂ ਲਾਈਨ ਸੈੱਲ ਦੇ ਸੱਜੇ ਕਿਨਾਰੇ 'ਤੇ ਪਹੁੰਚਦੀ ਹੈ ਜਾਂ ਕੈਰੀਜ ਰਿਟਰਨ ਕੈਰੈਕਟਰ (`\n`) ਮਿਲਦਾ ਹੈ,
ਲਾਈਨ ਬ੍ਰੇਕ ਹੁੰਦੀ ਹੈ ਅਤੇ ਮੌਜੂਦਾ ਦੇ ਹੇਠਾਂ ਆਟੋਮੈਟਿਕ ਨਵਾਂ ਸੈੱਲ ਬਣਦਾ ਹੈ।
ਸੱਜੀ ਸੀਮਾ ਤੋਂ ਪਹਿਲਾਂ ਸਭ ਤੋਂ ਨੇੜੇ ਦੇ ਸਪੇਸ ਜਾਂ ਸੌਫਟ-ਹਾਈਫਨ (`\u00ad`) 'ਤੇ ਆਟੋਮੈਟਿਕ ਬ੍ਰੇਕ ਹੁੰਦੀ ਹੈ।

ਦੋ ਡੌਕੂਮੈਂਟ ਵਿਸ਼ੇਸ਼ਤਾਵਾਂ ਨਿਰਧਾਰਤ ਕੀਤੀਆਂ ਗਈਆਂ ਹਨ: ਸਿਰਲੇਖ
([set_title](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) ਅਤੇ ਲੇਖਕ
([set_author](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author))। ਵਿਸ਼ੇਸ਼ਤਾਵਾਂ ਦੋ ਤਰੀਕਿਆਂ ਨਾਲ ਵੇਖੀਆਂ ਜਾ ਸਕਦੀਆਂ ਹਨ।
ਪਹਿਲਾ, Acrobat Reader ਨਾਲ ਸਿੱਧੇ ਡੌਕੂਮੈਂਟ ਖੋਲ੍ਹੋ, File ਮੈਨੂ 'ਤੇ ਜਾਓ
ਅਤੇ Document Properties ਵਿਕਲਪ ਚੁਣੋ। ਦੂਜਾ, ਪਲੱਗ-ਇਨ ਤੋਂ ਵੀ ਉਪਲਬਧ,
ਸੱਜਾ-ਕਲਿੱਕ ਕਰੋ ਅਤੇ Document Properties ਚੁਣੋ।

## ਟਿਊਟੋ 4 - ਮਲਟੀ ਕਾਲਮ ##

ਇਹ ਉਦਾਹਰਨ ਪਿਛਲੀ ਦਾ ਇੱਕ ਰੂਪ ਹੈ, ਜੋ ਦਿਖਾਉਂਦੀ ਹੈ ਕਿ ਟੈਕਸਟ ਨੂੰ ਕਈ ਕਾਲਮਾਂ ਵਿੱਚ ਕਿਵੇਂ ਵਿਛਾਉਣਾ ਹੈ।

```python
{% include "../tutorial/tuto4.py" %}
```

[ਨਤੀਜਾ PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto4.pdf)

[ਜੂਲਸ ਵਰਨ ਟੈਕਸਟ](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

ਪਿਛਲੇ ਟਿਊਟੋਰੀਅਲ ਤੋਂ ਮੁੱਖ ਫਰਕ
[`text_columns`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.text_column) ਮੈਥਡ ਦੀ ਵਰਤੋਂ ਹੈ।
ਇਹ ਸਾਰਾ ਟੈਕਸਟ ਇਕੱਠਾ ਕਰਦਾ ਹੈ ਅਤੇ ਬੇਨਤੀ ਕੀਤੇ ਕਾਲਮਾਂ ਦੀ ਗਿਣਤੀ ਵਿੱਚ ਵੰਡਦਾ ਹੈ, ਲੋੜ ਅਨੁਸਾਰ ਆਟੋਮੈਟਿਕ ਪੇਜ ਬ੍ਰੇਕ ਪਾਉਂਦਾ ਹੈ।

## ਟਿਊਟੋ 5 - ਟੇਬਲ ਬਣਾਉਣਾ ##

ਇਹ ਟਿਊਟੋਰੀਅਲ ਦੋ ਵੱਖ-ਵੱਖ ਟੇਬਲ ਬਣਾਉਣ ਦਾ ਤਰੀਕਾ ਦੱਸੇਗਾ।

```python
{% include "../tutorial/tuto5.py" %}
```

[ਨਤੀਜਾ PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto5.pdf) -
[ਦੇਸ਼ਾਂ ਦਾ CSV ਡੇਟਾ](https://github.com/py-pdf/fpdf2/raw/master/tutorial/countries.txt)

ਪਹਿਲੀ ਉਦਾਹਰਨ [`FPDF.table()`](https://py-pdf.github.io/fpdf2/Tables.html) ਨੂੰ ਡੇਟਾ ਫੀਡ ਕਰਕੇ ਸਭ ਤੋਂ ਸਧਾਰਨ ਤਰੀਕੇ ਨਾਲ ਪ੍ਰਾਪਤ ਕੀਤੀ ਗਈ ਹੈ।

ਦੂਜੀ ਟੇਬਲ ਕੁਝ ਸੁਧਾਰ ਲਿਆਉਂਦੀ ਹੈ: ਰੰਗ, ਸੀਮਤ ਟੇਬਲ ਚੌੜਾਈ, ਘੱਟ ਲਾਈਨ ਉਚਾਈ,
ਕੇਂਦਰਿਤ ਸਿਰਲੇਖ, ਕਸਟਮ ਚੌੜਾਈ ਵਾਲੇ ਕਾਲਮ, ਸੱਜੇ ਅਲਾਈਨ ਕੀਤੇ ਅੰਕੜੇ...
ਇਸ ਤੋਂ ਇਲਾਵਾ, ਹਰੀਜ਼ੌਂਟਲ ਲਾਈਨਾਂ ਹਟਾ ਦਿੱਤੀਆਂ ਗਈਆਂ ਹਨ।
ਇਹ ਉਪਲਬਧ ਵੈਲਿਊਜ਼ ਵਿੱਚੋਂ `borders_layout` ਚੁਣ ਕੇ ਕੀਤਾ ਗਿਆ:
[`TableBordersLayout`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TableBordersLayout)।

## ਟਿਊਟੋ 6 - ਲਿੰਕ ਬਣਾਉਣਾ ਅਤੇ ਟੈਕਸਟ ਸਟਾਈਲ ਮਿਲਾਉਣਾ ##

ਇਹ ਟਿਊਟੋਰੀਅਲ PDF ਡੌਕੂਮੈਂਟ ਅੰਦਰ ਲਿੰਕ ਪਾਉਣ ਦੇ ਕਈ ਤਰੀਕੇ ਦੱਸੇਗਾ,
ਨਾਲ ਹੀ ਬਾਹਰੀ ਸ੍ਰੋਤਾਂ ਦੇ ਲਿੰਕ ਜੋੜਨਾ।

ਇਹ ਇੱਕੋ ਟੈਕਸਟ ਵਿੱਚ ਵੱਖ-ਵੱਖ ਟੈਕਸਟ ਸਟਾਈਲ
(ਬੋਲਡ, ਇਟੈਲਿਕ, ਅੰਡਰਲਾਈਨ) ਵਰਤਣ ਦੇ ਕਈ ਤਰੀਕੇ ਵੀ ਦਿਖਾਏਗਾ।

```python
{% include "../tutorial/tuto6.py" %}
```

[ਨਤੀਜਾ PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-ਲੋਗੋ](https://py-pdf.github.io/fpdf2/fpdf2-logo.png)

ਇੱਥੇ ਟੈਕਸਟ ਪ੍ਰਿੰਟ ਕਰਨ ਲਈ ਦਿਖਾਇਆ ਗਿਆ ਨਵਾਂ ਮੈਥਡ
[write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write) ਹੈ।
ਇਹ [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) ਨਾਲ ਬਹੁਤ ਮਿਲਦਾ ਹੈ, ਮੁੱਖ ਫਰਕ ਇਹ ਹਨ:

- ਲਾਈਨ ਦਾ ਅੰਤ ਸੱਜੇ ਮਾਰਜਿਨ 'ਤੇ ਹੈ ਅਤੇ ਅਗਲੀ ਲਾਈਨ ਖੱਬੇ ਮਾਰਜਿਨ ਤੋਂ ਸ਼ੁਰੂ ਹੁੰਦੀ ਹੈ।
- ਮੌਜੂਦਾ ਸਥਿਤੀ ਟੈਕਸਟ ਦੇ ਅੰਤ 'ਤੇ ਚਲੀ ਜਾਂਦੀ ਹੈ।

ਇਸ ਲਈ ਮੈਥਡ ਸਾਨੂੰ ਟੈਕਸਟ ਦਾ ਇੱਕ ਹਿੱਸਾ ਲਿਖਣ, ਫੌਂਟ ਸਟਾਈਲ ਬਦਲਣ,
ਅਤੇ ਜਿੱਥੇ ਛੱਡਿਆ ਸੀ ਉੱਥੋਂ ਜਾਰੀ ਰੱਖਣ ਦੀ ਆਗਿਆ ਦਿੰਦਾ ਹੈ।

ਇੰਟਰਨਲ ਲਿੰਕ ਜੋੜਨ ਲਈ ਜੋ ਦੂਜੇ ਪੰਨੇ 'ਤੇ ਲੈ ਜਾਵੇ, ਅਸੀਂ
[add_link()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link) ਮੈਥਡ ਵਰਤਿਆ,
ਜੋ ਇੱਕ ਕਲਿੱਕ ਕਰਨ ਯੋਗ ਖੇਤਰ ਬਣਾਉਂਦਾ ਹੈ।

ਚਿੱਤਰ ਨਾਲ ਬਾਹਰੀ ਲਿੰਕ ਬਣਾਉਣ ਲਈ, ਅਸੀਂ
[image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image) ਵਰਤਿਆ।
ਇਸ ਮੈਥਡ ਵਿੱਚ ਇਸਦੇ ਆਰਗੂਮੈਂਟਾਂ ਵਿੱਚੋਂ ਇੱਕ ਵਜੋਂ ਲਿੰਕ ਪਾਸ ਕਰਨ ਦਾ ਵਿਕਲਪ ਹੈ।

ਵਿਕਲਪ ਵਜੋਂ, ਫੌਂਟ ਸਟਾਈਲ ਬਦਲਣ ਅਤੇ ਲਿੰਕ ਜੋੜਨ ਦਾ ਇੱਕ ਹੋਰ ਤਰੀਕਾ
`write_html()` ਮੈਥਡ ਵਰਤਣਾ ਹੈ। ਇਹ ਇੱਕ HTML ਪਾਰਸਰ ਹੈ, ਜੋ ਟੈਕਸਟ ਜੋੜਨ,
ਫੌਂਟ ਸਟਾਈਲ ਬਦਲਣ ਅਤੇ HTML ਨਾਲ ਲਿੰਕ ਜੋੜਨ ਦੀ ਆਗਿਆ ਦਿੰਦਾ ਹੈ।
