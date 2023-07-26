#!/usr/bin/env python3

# Invoke veraPDF CLI & parse its output
# Purpose of this script:
# * abort the validation pipeline with a non-zero error code if any check fails on a PDF sample
# * aggregate all checks performed in a concise summary
# * parallelize the execution of this analysis on all PDF files
# * allow to ignore some errors considered harmless, listed in verapdf-ignore.json

# USAGE: ./verapdf.py [$pdf_filepath|--process-all-test-pdf-files|--print-aggregated-report]

import sys
from subprocess import run, DEVNULL, PIPE

from scripts.checker_commons import main, HIDE_STDERR

CHECKS_DETAILS_URL = "https://docs.verapdf.org/validation/"
BAT_EXT = ".bat" if sys.platform in ("cygwin", "win32") else ""


def analyze_pdf_file(pdf_filepath):
    command = [
        "verapdf/verapdf" + BAT_EXT,
        "--format",
        "text",
        "-v",
        pdf_filepath,
    ]
    # print(" ".join(command))
    output = run(
        command, stdout=PIPE, stderr=DEVNULL if HIDE_STDERR else None
    ).stdout.decode()
    # print(output)
    return pdf_filepath, parse_output(output)


def parse_output(output):
    "Parse VeraPDF CLI output into a dict."
    lines = output.splitlines()
    try:
        grave_line = next(line for line in lines if line.startswith("GRAVE:"))
        return {"failure": grave_line}
    except StopIteration:
        # Skipping the first line
        errors = [line[len("  FAIL ") :] for line in lines[1:]]
        return {"errors": errors}


if __name__ == "__main__":
    main("verapdf", analyze_pdf_file, sys.argv, CHECKS_DETAILS_URL)
