import binascii
import socket
from glob import glob
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request

import pytest

import fpdf
from fpdf.image_datastructures import ImageCache

from test.conftest import assert_pdf_equal, ensure_rss_memory_below, time_execution

HERE = Path(__file__).resolve().parent
PNG_BYTES = (HERE / "png_images/c636287a4d7cb1a36362f7f236564cef.png").read_bytes()
SIMPLE_SVG_WITH_REMOTE_IMAGE = b"""
<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">
  <image href="https://public.example/image.png" x="0" y="0" width="10" height="10"/>
</svg>
"""


class MockResponse(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class MockOpener:
    def __init__(
        self,
        data: bytes,
        redirect_handler=None,
        redirect_to: str | None = None,
    ) -> None:
        self.data = data
        self.redirect_handler = redirect_handler
        self.redirect_to = redirect_to
        self.last_timeout = None

    def open(self, url: str, timeout=None):
        self.last_timeout = timeout
        if self.redirect_to:
            assert self.redirect_handler is not None
            self.redirect_handler.redirect_request(
                Request(url), None, 302, "Found", {}, self.redirect_to
            )
        return MockResponse(self.data)


def _mock_addrinfo_for(*addresses: str):
    addrinfo = []
    for address in addresses:
        family = socket.AF_INET6 if ":" in address else socket.AF_INET
        sockaddr = (address, 0, 0, 0) if family == socket.AF_INET6 else (address, 0)
        addrinfo.append((family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr))
    return addrinfo


def test_load_text_file():
    file = HERE / "__init__.py"
    contents = '"""This package contains image tests"""\n'
    bc = contents.encode()

    resource = fpdf.image_parsing.load_image(str(file)).getvalue()
    # loaded a text file in binary mode, may contain DOS style line endings.
    resource = resource.replace(b"\r\n", b"\n")
    assert bytes(resource) == bc


def test_load_base64_data(tmp_path):
    pdf = fpdf.FPDF()
    pdf.add_page()
    pdf.image(
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQBAMAAADt3eJSAAAAMFBMVEU0OkArMjhobHEoPUPFEBIuO0L+AAC2FBZ2JyuNICOfGx7xAwT"
        "jCAlCNTvVDA1aLzQ3COjMAAAAVUlEQVQI12NgwAaCDSA0888GCItjn0szWGBJTVoGSCjWs8TleQCQYV95evdxkFT8Kpe0PLDi5WfKd4LUsN5zS1sKFolt8bwAZrCa"
        "GqNYJAgFDEpQAAAzmxafI4vZWwAAAABJRU5ErkJggg=="
    )
    assert_pdf_equal(pdf, HERE / "load_base64_data.pdf", tmp_path)


def test_load_invalid_base64_data():
    pdf = fpdf.FPDF()
    pdf.add_page()
    with pytest.raises(binascii.Error):
        pdf.image("data:image/png;base64,GARBAGE")


# ensure memory usage does not get too high - this value depends on Python version:
@ensure_rss_memory_below(mib=6)
def test_share_images_cache(tmp_path):
    image_cache = None

    def build_pdf_with_big_images():
        nonlocal image_cache
        pdf = fpdf.FPDF()
        if image_cache is None:
            image_cache = pdf.image_cache
        else:
            pdf.image_cache = image_cache
        pdf.add_page()
        for img_path in glob(f"{HERE}/png_images/*.png"):
            pdf.image(img_path, h=pdf.eph)
        with (tmp_path / "out.pdf").open("wb") as pdf_file:
            pdf.output(pdf_file)
        # Reset the "usages" count:
        image_cache.reset_usages()

    with time_execution() as duration:
        build_pdf_with_big_images()
    first_time_duration = duration.seconds

    with time_execution() as duration:
        build_pdf_with_big_images()
    assert duration.seconds < first_time_duration / 2


def test_load_image_blocks_local_files_by_policy():
    file = HERE / "__init__.py"
    with pytest.raises(fpdf.FPDFResourceAccessError):
        fpdf.image_parsing.load_image(
            str(file), resource_access_policy=fpdf.ResourceAccessPolicy.NONE
        )


def test_load_image_allows_public_remote_by_default():
    opener = MockOpener(PNG_BYTES)
    with (
        patch(
            "fpdf.image_parsing.socket.getaddrinfo",
            return_value=_mock_addrinfo_for("93.184.216.34"),
        ),
        patch(
            "fpdf.image_parsing.build_opener",
            side_effect=lambda handler: setattr(opener, "redirect_handler", handler)
            or opener,
        ),
    ):
        resource = fpdf.image_parsing.load_image("https://public.example/image.png")
    assert resource.getvalue() == PNG_BYTES
    assert opener.last_timeout == fpdf.image_parsing.SETTINGS.network_timeout


def test_load_image_blocks_private_remote_by_default():
    with patch(
        "fpdf.image_parsing.socket.getaddrinfo",
        return_value=_mock_addrinfo_for("127.0.0.1"),
    ):
        with pytest.raises(fpdf.FPDFResourceAccessError):
            fpdf.image_parsing.load_image("http://private.example/image.png")


def test_load_image_blocks_private_redirect_by_default():
    def fake_getaddrinfo(host, *_args, **_kwargs):
        if host == "public.example":
            return _mock_addrinfo_for("93.184.216.34")
        if host == "private.example":
            return _mock_addrinfo_for("127.0.0.1")
        raise AssertionError(f"Unexpected hostname: {host}")

    with patch("fpdf.image_parsing.socket.getaddrinfo", side_effect=fake_getaddrinfo):
        with patch(
            "fpdf.image_parsing.build_opener",
            side_effect=lambda handler: MockOpener(
                PNG_BYTES,
                redirect_handler=handler,
                redirect_to="http://private.example/image.png",
            ),
        ):
            with pytest.raises(fpdf.FPDFResourceAccessError):
                fpdf.image_parsing.load_image("https://public.example/image.png")


def test_svg_preload_preserves_resource_access_error_for_blocked_redirect():
    def fake_getaddrinfo(host, *_args, **_kwargs):
        if host == "public.example":
            return _mock_addrinfo_for("93.184.216.34")
        if host == "private.example":
            return _mock_addrinfo_for("127.0.0.1")
        raise AssertionError(f"Unexpected hostname: {host}")

    with (
        patch("fpdf.image_parsing.socket.getaddrinfo", side_effect=fake_getaddrinfo),
        patch(
            "fpdf.image_parsing.build_opener",
            side_effect=lambda handler: MockOpener(
                b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>',
                redirect_handler=handler,
                redirect_to="http://private.example/image.svg",
            ),
        ),
    ):
        with pytest.raises(fpdf.FPDFResourceAccessError):
            fpdf.image_parsing.preload_image(
                ImageCache(), "https://public.example/image.svg"
            )


def test_image_per_call_policy_override_allows_private_remote():
    pdf = fpdf.FPDF()
    pdf.resource_access_policy = fpdf.ResourceAccessPolicy.NONE
    pdf.add_page()
    with (
        patch(
            "fpdf.image_parsing.socket.getaddrinfo",
            return_value=_mock_addrinfo_for("127.0.0.1"),
        ),
        patch(
            "fpdf.image_parsing.build_opener",
            side_effect=lambda handler: MockOpener(PNG_BYTES, redirect_handler=handler),
        ),
    ):
        pdf.image(
            "http://private.example/image.png",
            x=10,
            y=10,
            w=10,
            resource_access_policy=fpdf.ResourceAccessPolicy.ALL,
        )


def test_svg_image_per_call_policy_override_applies_to_nested_resources(tmp_path):
    svg_path = tmp_path / "nested.svg"
    svg_path.write_text(
        """
        <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">
        <image href="http://private.example/image.png" x="0" y="0" width="10" height="10"/>
        </svg>""",
        encoding="utf-8",
    )

    pdf = fpdf.FPDF()
    pdf.resource_access_policy = fpdf.ResourceAccessPolicy.NONE
    pdf.add_page()
    with (
        patch(
            "fpdf.image_parsing.socket.getaddrinfo",
            return_value=_mock_addrinfo_for("127.0.0.1"),
        ),
        patch(
            "fpdf.image_parsing.build_opener",
            side_effect=lambda handler: MockOpener(PNG_BYTES, redirect_handler=handler),
        ),
    ):
        pdf.image(
            svg_path,
            w=10,
            resource_access_policy=fpdf.ResourceAccessPolicy.ALL,
        )


def test_svg_object_draw_to_page_uses_document_resource_access_policy():
    svg = fpdf.svg.SVGObject(SIMPLE_SVG_WITH_REMOTE_IMAGE)
    pdf = fpdf.FPDF()
    pdf.resource_access_policy = fpdf.ResourceAccessPolicy.NONE
    pdf.add_page()

    with (
        patch(
            "fpdf.image_parsing.socket.getaddrinfo",
            return_value=_mock_addrinfo_for("93.184.216.34"),
        ),
        patch(
            "fpdf.image_parsing.build_opener",
            side_effect=lambda handler: MockOpener(PNG_BYTES, redirect_handler=handler),
        ),
    ):
        with pytest.raises(fpdf.FPDFResourceAccessError):
            svg.draw_to_page(pdf)

    assert svg.resource_access_policy == fpdf.ResourceAccessPolicy.DEFAULT


def test_write_html_uses_document_resource_access_policy():
    img_path = HERE / "png_images/c636287a4d7cb1a36362f7f236564cef.png"
    pdf = fpdf.FPDF()
    pdf.resource_access_policy = fpdf.ResourceAccessPolicy.NONE
    pdf.add_page()
    with pytest.raises(fpdf.FPDFResourceAccessError):
        pdf.write_html(f'<img src="{img_path}" width="10" height="10">')


def test_template_image_uses_document_resource_access_policy():
    img_path = HERE / "png_images/c636287a4d7cb1a36362f7f236564cef.png"
    pdf = fpdf.FPDF()
    pdf.resource_access_policy = fpdf.ResourceAccessPolicy.NONE
    pdf.add_page()
    template = fpdf.FlexTemplate(
        pdf,
        elements=[
            {
                "name": "img",
                "type": "I",
                "x1": 10,
                "y1": 10,
                "x2": 20,
                "y2": 20,
                "text": str(img_path),
            }
        ],
    )
    with pytest.raises(fpdf.FPDFResourceAccessError):
        template.render()


def test_text_columns_downscale_reload_uses_document_resource_access_policy():
    def fake_getaddrinfo(host, *_args, **_kwargs):
        if host == "public.example":
            return _mock_addrinfo_for("93.184.216.34")
        if host == "private.example":
            return _mock_addrinfo_for("127.0.0.1")
        raise AssertionError(f"Unexpected hostname: {host}")

    open_count = {"count": 0}

    class RedirectOnSecondOpen:
        def __init__(self, redirect_handler) -> None:
            self.redirect_handler = redirect_handler

        def open(self, url: str, timeout=None):  # pylint: disable=unused-argument
            open_count["count"] += 1
            if open_count["count"] == 2:
                self.redirect_handler.redirect_request(
                    Request(url),
                    None,
                    302,
                    "Found",
                    {},
                    "http://private.example/image.png",
                )
            return MockResponse(PNG_BYTES)

    pdf = fpdf.FPDF()
    pdf.resource_access_policy = fpdf.ResourceAccessPolicy.REMOTE_PUBLIC
    pdf.oversized_images = "downscale"
    pdf.add_page()

    with (
        patch("fpdf.image_parsing.socket.getaddrinfo", side_effect=fake_getaddrinfo),
        patch(
            "fpdf.image_parsing.build_opener",
            side_effect=RedirectOnSecondOpen,
        ),
    ):
        with pytest.raises(fpdf.FPDFResourceAccessError):
            with pdf.text_columns() as cols:
                cols.image("https://public.example/image.png", width=1, height=1)
