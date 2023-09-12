# Combine with livereload

A nice feature of PDF readers is when they detect changes to the `.pdf` files open
and automatically reload them in the viewer.
Adobe Acrobat Reader **does not** provide this feature but other viewers offer it,
like the free & open source [Sumatra PDF Reader](https://www.sumatrapdfreader.org) under Windows.

When using such PDF reader, it can be very useful to use a "watch" mode,
so that every change to the Python code will trigger the regeneration of the PDF file.

The following script is an example of using [`livereload`](https://pypi.org/project/livereload/) with `fpdf2` to do that.
Launched without parameters, this script only generates a PDF document.
But when launched with `--watch` as argument,
it will detect changes to the Python script itself,
and then reload itself with [`xreload`](https://pypi.org/project/xreload/),
and finally regenerate the PDF document.

```python
{% include "../tutorial/watch_with_livereload.py" %}
```

Note that the module reloading mechanism provided by `xreload`
has several limitations, _cf._ [`xreload.py`](https://github.com/Lucas-C/xreload/blob/master/src/xreload.py#L8).
