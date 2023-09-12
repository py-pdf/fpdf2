#!/usr/bin/env python3
# Script Dependencies:
#    fpdf2
#    livereload
#    xreload
import asyncio, logging, sys
from traceback import print_exc

from fpdf import FPDF
from livereload.watcher import get_watcher_class
from xreload import xreload


OUT_FILEPATH = "fpdf2-demo.pdf"


def build_pdf():
    pdf = FPDF()
    pdf.set_font("Helvetica", size=16)
    pdf.add_page()
    pdf.y += 50
    pdf.multi_cell(
        h=10,
        w=0,
        align="C",
        txt="""Hello fpdf2 user!
Launch this script with --watch
and then try to modify this text while the script is running""",
    )
    pdf.output(OUT_FILEPATH)
    print(f"{OUT_FILEPATH} has been rebuilt")


async def start_watch_and_rebuild():
    logging.basicConfig(
        format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )
    logging.getLogger("livereload").setLevel(logging.INFO)
    watcher = get_watcher_class()()
    watcher.watch(__file__, build_pdf)
    print("Watcher started...")
    await watch_periodically(watcher)


async def watch_periodically(watcher, delay_secs=0.8):
    try:
        watcher.examine()
    except Exception:
        print_exc()
    await asyncio.sleep(delay_secs)
    xreload(sys.modules[__name__], new_annotations={"XRELOADED": True})
    await asyncio.create_task(watch_periodically(watcher))


# This conditional ensure that the code below
# does not get executed when calling xreload on this module:
if not __annotations__.get("XRELOADED"):
    build_pdf()
    # The --watch mode is very handy when using a PDF reader
    # that performs hot-reloading, like Sumatra PDF Reader:
    if "--watch" in sys.argv:
        asyncio.run(start_watch_and_rebuild())
