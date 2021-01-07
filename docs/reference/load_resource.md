## load_resource ##

```python
fpdf.load_resource(reason: string, filename: string)
```

### Description ###

This method is used to load external resources, such as images. It is 
automatically called when resource added to document by [image](image.md). The 
implementation in library sre try to load resource from local file system or 
from network if filename starts with `http://` or `https://`. This method can 
be overrided within subclass if you want a specific processing. 

Returns file-like object.

### Parameters ###

reason:
> Resource type: `image`.

filename:
> filename or URL.

### See also ###

[image](image.md).

