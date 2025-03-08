#!/usr/bin/env python3

# Invoke veraPDF CLI & parse its output
# Purpose of this script:
# * abort the validation pipeline with a non-zero error code if any check fails on a PDF sample
# * aggregate all checks performed in a concise summary
# * parallelize the execution of this analysis on all PDF files
# * allow to ignore some errors considered harmless, listed in verapdf-ignore.json

# USAGE: ./verapdf.py [$pdf_filepath|--process-all-test-pdf-files|--print-aggregated-report]

import sys
from subprocess import run, PIPE, STDOUT

from scripts.checker_commons import main

CHECKS_DETAILS_URL = "https://docs.verapdf.org/validation/"
BAT_EXT = ".bat" if sys.platform in ("cygwin", "win32") else ""
FAIL_CODES = ("ERROR", "FAIL", "GRAVE", "SEVERE")
FAIL_IGNORED_PREFIXES = (  # We do not expect all PDF files to be PDF/A compliant
    "1b",
    "PDF/A Validation",
)


def analyze_pdf_file(pdf_filepath):
    try:
        command = [
            "verapdf/verapdf" + BAT_EXT,
            "--format",
            "text",
            "-v",
            pdf_filepath,
        ]
        # print(" ".join(command))
        output = run(command, check=False, stdout=PIPE, stderr=STDOUT).stdout.decode()
        # print(output)
        return pdf_filepath, parse_output(output)
    # pylint: disable=broad-exception-caught
    except BaseException as error:
        return pdf_filepath, error


def parse_output(output):
    "Parse VeraPDF CLI output into a dict."
    errors = []
    failure = ""
    warning = ""
    line_iterator = iter(output.splitlines())
    for line in line_iterator:
        if line.startswith("PASS ") or " PM org.verapdf" in line:
            continue  # 1st line of every message logged by VeraPDF, containing the current time
        if line.startswith("  FAIL "):
            errors.append(line[len("  FAIL ") :])
        elif any(line.startswith(fail_code) for fail_code in FAIL_CODES):
            if failure:
                failure += " + "
            _fail_code, _filepath, error = line.split(" ", 2)
            if not any(error.startswith(prefix) for prefix in FAIL_IGNORED_PREFIXES):
                failure += line
        elif line.startswith("WARNING: "):
            if warning:
                warning += " + "
            warning += line[len("WARNING: ") :] + " - " + next(line_iterator)
            # pylint: disable=redefined-loop-name
            for line in line_iterator:
                if not line:
                    break  # WARNING stacktraces end with an empty line
                if not line.startswith("\t"):  # ignoring stacktrace
                    warning += " - " + line
        else:
            raise RuntimeError(f"Unexpected line format: {line}")
    return {"failure": failure, "warning": warning, "errors": errors}


if __name__ == "__main__":
    main("verapdf", analyze_pdf_file, sys.argv, CHECKS_DETAILS_URL)
