"""
Various utilities that could not be gathered logically in a specific module.

The contents of this module are internal to fpdf2, and not part of the public API.
They may change at any time without prior warning or any deprecation period,
in non-backward-compatible ways.
"""

import gc
import os
import warnings
from numbers import Number
from tracemalloc import get_traced_memory, is_tracing
from typing import Iterable, NamedTuple, Tuple, Union

# default block size from src/libImaging/Storage.c:
PIL_MEM_BLOCK_SIZE_IN_MIB = 16


class Padding(NamedTuple):
    top: Number = 0
    right: Number = 0
    bottom: Number = 0
    left: Number = 0

    @classmethod
    def new(cls, padding: Union[int, float, tuple, list]):
        """Return a 4-tuple of padding values from a single value or a 2, 3 or 4-tuple according to CSS rules"""
        if isinstance(padding, (int, float)):
            return Padding(padding, padding, padding, padding)
        if len(padding) == 2:
            return Padding(padding[0], padding[1], padding[0], padding[1])
        if len(padding) == 3:
            return Padding(padding[0], padding[1], padding[2], padding[1])
        if len(padding) == 4:
            return Padding(*padding)

        raise ValueError(
            f"padding shall be a number or a sequence of 2, 3 or 4 numbers, got {str(padding)}"
        )


def buffer_subst(buffer, placeholder, value):
    buffer_size = len(buffer)
    assert len(placeholder) == len(value), f"placeholder={placeholder} value={value}"
    buffer = buffer.replace(placeholder.encode(), value.encode(), 1)
    assert len(buffer) == buffer_size
    return buffer


def escape_parens(s):
    """Add a backslash character before , ( and )"""
    if isinstance(s, str):
        return (
            s.replace("\\", "\\\\")
            .replace(")", "\\)")
            .replace("(", "\\(")
            .replace("\r", "\\r")
        )
    return (
        s.replace(b"\\", b"\\\\")
        .replace(b")", b"\\)")
        .replace(b"(", b"\\(")
        .replace(b"\r", b"\\r")
    )


def get_scale_factor(unit: Union[str, Number]) -> float:
    """
    Get how many pts are in a unit. (k)

    Args:
        unit (str, float, int): Any of "pt", "mm", "cm", "in", or a number.
    Returns:
        float: The number of points in that unit (assuming 72dpi)
    Raises:
        ValueError
    """
    if isinstance(unit, Number):
        return float(unit)

    if unit == "pt":
        return 1
    if unit == "mm":
        return 72 / 25.4
    if unit == "cm":
        return 72 / 2.54
    if unit == "in":
        return 72.0
    raise ValueError(f"Incorrect unit: {unit}")


def convert_unit(
    to_convert: Union[float, int, Iterable[Union[float, int, Iterable]]],
    old_unit: Union[str, Number],
    new_unit: Union[str, Number],
) -> Union[float, tuple]:
    """
     Convert a number or sequence of numbers from one unit to another.

     If either unit is a number it will be treated as the number of points per unit.  So 72 would mean 1 inch.

     Args:
        to_convert (float, int, Iterable): The number / list of numbers, or points, to convert
        old_unit (str, float, int): A unit accepted by `fpdf.fpdf.FPDF` or a number
        new_unit (str, float, int): A unit accepted by `fpdf.fpdf.FPDF` or a number
    Returns:
        (float, tuple): to_convert converted from old_unit to new_unit or a tuple of the same
    """
    unit_conversion_factor = get_scale_factor(new_unit) / get_scale_factor(old_unit)
    if isinstance(to_convert, Iterable):
        return tuple(convert_unit(i, 1, unit_conversion_factor) for i in to_convert)
    return to_convert / unit_conversion_factor


ROMAN_NUMERAL_MAP = (
    ("M", 1000),
    ("CM", 900),
    ("D", 500),
    ("CD", 400),
    ("C", 100),
    ("XC", 90),
    ("L", 50),
    ("XL", 40),
    ("X", 10),
    ("IX", 9),
    ("V", 5),
    ("IV", 4),
    ("I", 1),
)


def int2roman(n):
    "Convert an integer to Roman numeral"
    result = ""
    if n is None:
        return result
    for numeral, integer in ROMAN_NUMERAL_MAP:
        while n >= integer:
            result += numeral
            n -= integer
    return result


def int_to_letters(n: int) -> str:
    "Convert an integer to a letter value (A to Z for the first 26, then AA to ZZ, and so on)"
    if n > 25:
        return int_to_letters(int((n / 26) - 1)) + int_to_letters(n % 26)
    return chr(n + ord("A"))


################################################################################
################### Utility functions to track memory usage ####################
################################################################################


def print_mem_usage(prefix):
    print(get_mem_usage(prefix))


def get_mem_usage(prefix) -> str:
    _collected_count = gc.collect()
    rss = get_process_rss()
    # heap_size, stack_size = get_process_heap_and_stack_sizes()
    # objs_size_sum = get_gc_managed_objs_total_size()
    pillow = get_pillow_allocated_memory()
    # malloc_stats = "Malloc stats: " + get_pymalloc_allocated_over_total_size()
    malloc_stats = ""
    if is_tracing():
        malloc_stats = "Malloc stats: " + get_tracemalloc_traced_memory()
    return f"{prefix:<40} {malloc_stats} | Pillow: {pillow} | Process RSS: {rss}"


def get_process_rss() -> str:
    rss_as_mib = get_process_rss_as_mib()
    if rss_as_mib:
        return f"{rss_as_mib:.1f} MiB"
    return "<unavailable>"


def get_process_rss_as_mib() -> Union[Number, None]:
    "Inspired by psutil source code"
    pid = os.getpid()
    try:
        with open(f"/proc/{pid}/statm", encoding="utf8") as statm:
            return (
                int(statm.readline().split()[1])
                * os.sysconf("SC_PAGE_SIZE")
                / 1024
                / 1024
            )
    except FileNotFoundError:  # /proc files only exist under Linux
        return None


def get_process_heap_and_stack_sizes() -> Tuple[str]:
    heap_size_in_mib, stack_size_in_mib = "<unavailable>", "<unavailable>"
    pid = os.getpid()
    try:
        with open(f"/proc/{pid}/maps", encoding="utf8") as maps_file:
            maps_lines = list(maps_file)
    except FileNotFoundError:  # This file only exists under Linux
        return heap_size_in_mib, stack_size_in_mib
    for line in maps_lines:
        words = line.split()
        addr_range, path = words[0], words[-1]
        addr_start, addr_end = addr_range.split("-")
        addr_start, addr_end = int(addr_start, 16), int(addr_end, 16)
        size = addr_end - addr_start
        if path == "[heap]":
            heap_size_in_mib = f"{size / 1024 / 1024:.1f} MiB"
        elif path == "[stack]":
            stack_size_in_mib = f"{size / 1024 / 1024:.1f} MiB"
    return heap_size_in_mib, stack_size_in_mib


def get_pymalloc_allocated_over_total_size() -> Tuple[str]:
    """
    Get PyMalloc stats from sys._debugmallocstats()
    From experiments, not very reliable
    """
    try:
        # pylint: disable=import-outside-toplevel
        from pymemtrace.debug_malloc_stats import get_debugmallocstats

        allocated, total = -1, -1
        for line in get_debugmallocstats().decode().splitlines():
            if line.startswith("Total"):
                total = int(line.split()[-1].replace(",", ""))
            elif line.startswith("# bytes in allocated blocks"):
                allocated = int(line.split()[-1].replace(",", ""))
        return f"{allocated / 1024 / 1024:.1f} / {total / 1024 / 1024:.1f} MiB"
    except ImportError:
        warnings.warn("pymemtrace could not be imported - Run: pip install pymemtrace")
        return "<unavailable>"


def get_gc_managed_objs_total_size() -> str:
    "From experiments, not very reliable"
    try:
        # pylint: disable=import-outside-toplevel
        from pympler.muppy import get_objects, getsizeof

        objs_total_size = sum(getsizeof(obj) for obj in get_objects())
        return f"{objs_total_size / 1024 / 1024:.1f} MiB"
    except ImportError:
        warnings.warn("pympler could not be imported - Run: pip install pympler")
        return "<unavailable>"


def get_tracemalloc_traced_memory() -> str:
    "Requires python -X tracemalloc"
    current, peak = get_traced_memory()
    return f"{current / 1024 / 1024:.1f} (peak={peak / 1024 / 1024:.1f}) MiB"


def get_pillow_allocated_memory() -> str:
    # pylint: disable=c-extension-no-member,import-outside-toplevel
    from PIL import Image

    stats = Image.core.get_stats()
    blocks_in_use = stats["allocated_blocks"] - stats["freed_blocks"]
    return f"{blocks_in_use * PIL_MEM_BLOCK_SIZE_IN_MIB:.1f} MiB"
