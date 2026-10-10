# Security

## Security model

`fpdf2` operates on content and resource references explicitly provided to it. As a result, applications integrating `fpdf2` are responsible for validating untrusted input, enforcing appropriate filesystem and network restrictions, and choosing safe defaults for their deployment environment.

`fpdf2` is therefore only as secure as the application and runtime environment using it.

## Untrusted content

Extra care must be taken when rendering content formats that can reference additional resources, including:

- HTML via `write_html()`
- SVG images via `image()`
- template-driven image paths
- direct image paths or URLs passed to `image()`

These formats may contain references to local files or remote resources. If such content is attacker-controlled, it can cause the library to attempt to load those resources unless access is restricted.

Applications should avoid rendering untrusted HTML, SVG, or image paths without validation or an appropriate `resource_access_policy`.

## Built-in protections

`fpdf2` includes protections against some common parser-related attacks.

For example, SVG/XML parsing uses hardened XML handling intended to mitigate classes of attacks such as exponential entity expansion ("Billion Laughs"-style attacks).

These protections reduce risk in specific parsing paths, but they do not replace safe application design or input validation.

## SVG complexity limits

To reduce the risk of CPU and memory exhaustion while rendering SVG files,
`fpdf2` applies configurable SVG complexity limits through `FPDF.svg_limits`.

By default, SVG rendering limits:

* nested SVG `<use>` reference depth
* the number of drawing elements after SVG references are resolved

If an SVG exceeds those limits, `fpdf2` raises
`fpdf.errors.FPDFSvgLimitExceeded`. Applications that accept user-provided SVGs
can catch this exception and reject the input without relying on exception
message matching:

```python
from fpdf import FPDF
from fpdf.errors import FPDFSvgLimitExceeded

pdf = FPDF()
pdf.add_page()

try:
    pdf.image(user_svg_bytes, w=100)
except FPDFSvgLimitExceeded:
    # Reject the SVG, ask the user to simplify it, or retry only if trusted.
    ...
```

Trusted applications that need to render unusually large SVGs can raise the
limits for a document:

```python
from fpdf import FPDF
from fpdf.svg import SVGLimits

pdf = FPDF()
pdf.svg_limits = SVGLimits(
    max_use_depth=64,
    max_resolved_elements=500_000,
)
```

Each limit can be disabled with `None`, but this should only be done for trusted
SVG input:

```python
from fpdf import FPDF
from fpdf.svg import SVGLimits

pdf = FPDF()
pdf.svg_limits = SVGLimits(
    max_use_depth=None,
    max_resolved_elements=None,
)
```

Disabling or substantially raising SVG limits can allow a small SVG to consume
large amounts of CPU and memory. Keep the defaults for untrusted or partially
trusted SVG input.

## Resource access policy

To reduce the risk of unintended local file access or outbound network requests, `fpdf2` provides a configurable `resource_access_policy`.

This policy controls which resource types may be loaded while rendering content.

Example:

```python
from fpdf import FPDF, ResourceAccessPolicy

pdf = FPDF()
pdf.resource_access_policy = (
    ResourceAccessPolicy.LOCAL_FILES | ResourceAccessPolicy.REMOTE_PUBLIC
)
```

The policy applies globally to the `FPDF` instance and affects all resource loading performed through that document, including nested resources referenced from HTML or SVG.

By default, `fpdf2` restricts resource loading to local files and remote HTTP(S) resources that resolve to public network addresses. Access to private, loopback, and link-local network targets is blocked.

## Per-call override with `image()`

The `image()` method also accepts a `resource_access_policy` argument that overrides the document-wide setting for that specific call:

```python
from fpdf import FPDF, ResourceAccessPolicy

pdf = FPDF()
pdf.resource_access_policy = ResourceAccessPolicy.NONE

pdf.image(
    "https://example.com/logo.png",
    x=10,
    y=10,
    w=20,
    resource_access_policy=ResourceAccessPolicy.REMOTE_PUBLIC,
)
```

This override also applies to nested raster resources referenced from SVG files loaded through that `image()` call.

The resource access policy does not limit inline SVG expansion. An SVG that only
uses internal references, such as `<use href="#shape">`, can still be rejected
by SVG complexity limits even when `resource_access_policy` allows no external
resources.

## Recommended usage

When an application may handle user-provided or partially trusted content, prefer keeping the document-wide `resource_access_policy` restrictive and using per-call overrides only for specific trusted resources.

This is safer than relaxing the main policy for the entire `FPDF` instance.

Recommended pattern:

* keep `pdf.resource_access_policy` as strict as practical
* keep the default `pdf.svg_limits` for user-provided SVG content
* use `image(..., resource_access_policy=...)` only where a specific trusted resource needs broader access
* avoid changing the global policy to accommodate a single image source

This is especially important in applications that expose PDF generation features to end users.

## Additional recommendations

Applications using `fpdf2` with untrusted input should also consider:

* sanitizing or rejecting untrusted HTML and SVG content
* catching `FPDFSvgLimitExceeded` and treating it as rejected SVG input
* validating image paths and URLs before passing them to `fpdf2`
* applying network egress restrictions at the infrastructure level
* limiting filesystem access for the process running PDF generation
* running document generation in isolated environments when appropriate
