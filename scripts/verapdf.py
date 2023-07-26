#!/usr/bin/env python3

# Invoke veraPDF CLI & parse its output
# Purpose of this script:
# * abort the validation pipeline with a non-zero error code if any check fails on a PDF sample
# * aggregate all checks performed in a concise summary
# * parallelize the execution of this analysis on all PDF files
# * allow to ignore some errors considered harmless, listed in verapdf-ignore.json

# USAGE: ./verapdf.py [$pdf_filepath|--process-all-test-pdf-files|--print-aggregated-report]

import json
import sys
from subprocess import run, PIPE
from multiprocessing import cpu_count

from scripts.checker_commons import main

CHECKS_DETAILS_URL = "https://docs.verapdf.org/validation/"
BAT_EXT = ".bat" if sys.platform in ("cygwin", "win32") else ""


def analyze_pdf_file(pdf_filepath):
    command = [
        "verapdf/verapdf" + BAT_EXT,
        "--format",
        "json",
        pdf_filepath,
    ]
    # print(" ".join(command))
    output = run(command, stdout=PIPE).stdout.decode()

    return parse_output(output)


def analyze_directory_of_pdf_files(root):
    print(f"Starting execution of verapdf on directory {root}.")
    command = [
        "verapdf/verapdf" + BAT_EXT,
        "--format",
        "json",
        "--processes",
        str(cpu_count()),
        "--recurse",
        root,
    ]
    # print(" ".join(command))
    output = run(command, stdout=PIPE).stdout.decode()

    return parse_output(output)


def parse_output(output):
    "Parse VeraPDF CLI output into a dict."
    output_dict = json.loads(output)

    print(output_dict.keys())

    reports_per_pdf_filepath = {}
    for output_job in output_dict["report"]["jobs"]:
        file_path = output_job["itemDetails"]["name"]
        if "taskException" in output_job:
            reports_per_pdf_filepath[file_path] = {
                "failure": output_job["taskException"]["exceptionMessage"]
            }
        else:
            errors = [
                f"{rule_summary['clause']}-{rule_summary['testNumber']}"
                for rule_summary in output_job["validationResult"]["details"][
                    "ruleSummaries"
                ]
            ]
            reports_per_pdf_filepath[file_path] = {"errors": errors}

    return reports_per_pdf_filepath


if __name__ == "__main__":
    main(
        "verapdf",
        analyze_pdf_file,
        analyze_directory_of_pdf_files,
        sys.argv,
        CHECKS_DETAILS_URL,
    )
