#!/usr/bin/env python3

# Invoke veraPDF CLI & parse its output
# Purpose of this script:
# * abort the validation pipeline with a non-zero error code if any check fails on a PDF sample
# * aggregate all checks performed in a concise summary
# * allow to ignore some errors considered harmless, listed in verapdf-ignore.json

# USAGE: ./verapdf.py [$pdf_filepath]

import sys
from subprocess import PIPE, run

from scripts.checker_commons import aggregate, print_aggregated_report

AGGREGATED_REPORT_FILEPATH = "verapdf-aggregated.json"
IGNORE_WHITELIST_FILEPATH = "scripts/verapdf-ignore.json"
CHECKS_DETAILS_URL = "https://docs.verapdf.org/validation/pdfa-part1/ & https://docs.verapdf.org/validation/pdfa-parts-2-and-3/"
BAT_EXT = ".bat" if sys.platform in ("cygwin", "win32") else ""


def analyze_pdf_file(pdf_filepath):
    output = run(
        [
            "verapdf/verapdf" + BAT_EXT,
            "--format",
            "text",
            "-v",
            pdf_filepath,
        ],
        stdout=PIPE,
    ).stdout.decode()
    report = parse_output(output)
    aggregate(pdf_filepath, report, AGGREGATED_REPORT_FILEPATH)


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
    if len(sys.argv) < 2:
        print_aggregated_report(
            AGGREGATED_REPORT_FILEPATH, CHECKS_DETAILS_URL, IGNORE_WHITELIST_FILEPATH
        )
    elif len(sys.argv) > 2:
        print(sys.argv, file=sys.stderr)
        print("Exactly one argument must be passed to verapdf.py", file=sys.stderr)
        sys.exit(2)
    else:
        analyze_pdf_file(sys.argv[1])
