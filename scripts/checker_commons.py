"""
Code used both in pdfchecker.py & verapdf.py
"""

import json, os, sys
from collections import defaultdict
from multiprocessing import cpu_count, Pool

try:  # optional dependency to display a progress bar
    from tqdm import tqdm
except ImportError:
    tqdm = lambda _, total: _

MULTIPROC_PARALLELISM = True


def main(checker_name, analyze_pdf_file, argv, checks_details_url):
    if len(argv) != 2:
        print(argv, file=sys.stderr)
        print(
            f"Exactly one argument must be passed to {checker_name}.py", file=sys.stderr
        )
        sys.exit(2)
    elif argv[1] == "--print-aggregated-report":
        print_aggregated_report(checker_name, checks_details_url)
    elif argv[1] == "--process-all-test-pdf-files":
        process_all_test_pdf_files(checker_name, analyze_pdf_file)
    else:
        print(analyze_pdf_file(argv[1]))


def process_all_test_pdf_files(checker_name, analyze_pdf_file):
    pdf_filepaths = [
        entry.path
        for entry in scantree("test")
        if entry.is_file() and entry.name.endswith(".pdf")
    ]
    print(
        f"Starting parallel execution of {checker_name} on {len(pdf_filepaths)} PDF files with {cpu_count()} CPUs"
    )
    reports_per_pdf_filepath = {}
    if MULTIPROC_PARALLELISM:
        with Pool(cpu_count()) as pool:
            for pdf_filepath, report in tqdm(
                pool.imap_unordered(analyze_pdf_file, pdf_filepaths),
                total=len(pdf_filepaths),
            ):
                reports_per_pdf_filepath[pdf_filepath] = raise_on_error(report)
    else:
        for pdf_filepath in tqdm(pdf_filepaths, total=len(pdf_filepaths)):
            report = analyze_pdf_file(pdf_filepath)[1]
            reports_per_pdf_filepath[pdf_filepath] = raise_on_error(report)
    agg_report = aggregate(checker_name, reports_per_pdf_filepath)
    print(
        f"{checker_name} analysis succeeded - Failures:",
        len(agg_report["failures"]),
        "- Warnings:",
        len(agg_report["warnings"]),
        "- Errors:",
        len(agg_report["errors"]),
    )


def raise_on_error(report_or_error):
    """
    This error handling may seems strange or useless,
    but optionally returning an error from analyze_pdf_file()
    is good way to "bubble up" errors raised in this function
    that would otherwise be "hidden" by multiprocessing.Pool.imap_unordered
    """
    if isinstance(report_or_error, BaseException):
        print(
            "ERROR: re-running this script with MULTIPROC_PARALLELISM=False can improve the stacktrace"
        )
        raise report_or_error
    return report_or_error


def scantree(path):
    """Recursively yield DirEntry objects for given directory."""
    for entry in os.scandir(path):
        if entry.is_dir():
            yield from scantree(entry.path)
        else:
            yield entry


def aggregate(checker_name, reports_per_pdf_filepath):
    aggregated_report_filepath = f"{checker_name}-aggregated.json"
    agg_report = {
        "failures": defaultdict(list),
        "warnings": defaultdict(list),
        "errors": defaultdict(list),
    }
    try:
        with open(aggregated_report_filepath, encoding="utf8") as agg_file:
            prev_agg_report = json.load(agg_file)
        agg_report["failures"].update(prev_agg_report["failures"])
        agg_report["warnings"].update(prev_agg_report["warnings"])
        agg_report["errors"].update(prev_agg_report["errors"])
    except FileNotFoundError:
        print("Initializing a new JSON file for the aggregated report")
        report = list(reports_per_pdf_filepath.items())[0][1]
        if "version" in report:
            agg_report["version"] = report.pop("version")
    for pdf_filepath, report in reports_per_pdf_filepath.items():
        if report.get("failure"):
            agg_report["failures"][report["failure"]].append(pdf_filepath)
        elif report.get("warning"):
            agg_report["warnings"][report["warning"]].append(pdf_filepath)
        else:
            for error in report.get("errors", ()):
                agg_report["errors"][error].append(pdf_filepath)
    with open(aggregated_report_filepath, "w", encoding="utf8") as agg_file:
        json.dump(agg_report, agg_file, indent=4)
    return agg_report


def print_aggregated_report(checker_name, checks_details_url):
    aggregated_report_filepath = f"{checker_name}-aggregated.json"
    with open(aggregated_report_filepath, encoding="utf8") as agg_file:
        agg_report = json.load(agg_file)
    if "version" in agg_report:
        print(agg_report["version"])
    print("# AGGREGATED REPORT #")
    if agg_report["failures"]:
        print("Failures:")
        for failure, pdf_filepaths in sorted(agg_report["failures"].items()):
            print(
                f"* {failure}: x{len(pdf_filepaths)} - First 3 files: {', '.join(pdf_filepaths[:3])}"
            )
    if agg_report["warnings"]:
        print("Warnings:")
        for warning, pdf_filepaths in sorted(agg_report["warnings"].items()):
            print(
                f"* {warning}: x{len(pdf_filepaths)} - First 3 files: {', '.join(pdf_filepaths[:3])}"
            )
    if agg_report["errors"]:
        print("Errors:")
        for error, pdf_filepaths in sorted(
            sorted(agg_report["errors"].items(), key=lambda error: -len(error[1]))
        ):
            print(
                f"* {error}: x{len(pdf_filepaths)} - First 3 files: {', '.join(pdf_filepaths[:3])}"
            )
    print("\nDocumentation on the checks:", checks_details_url)
    fail_on_unexpected_check_failure(checker_name, agg_report)


def fail_on_unexpected_check_failure(checker_name, agg_report):
    "exit(1) if there is any non-passing & non-whitelisted error remaining"
    ignore_whitelist_filepath = f"scripts/{checker_name}-ignore.json"
    with open(ignore_whitelist_filepath, encoding="utf8") as ignore_file:
        ignored_error_codes = set(json.load(ignore_file)["errors"].keys())
    report_error_codes = set(agg_report["errors"].keys())
    non_whitelisted_errors = report_error_codes - ignored_error_codes
    if agg_report["failures"] or non_whitelisted_errors:
        print(
            "Non-whitelisted issues found:",
            ", ".join(
                sorted(agg_report["failures"].keys()) + sorted(non_whitelisted_errors)
            ),
        )
        sys.exit(1)
    non_matching_ignored_codes = ignored_error_codes - report_error_codes
    if non_matching_ignored_codes:
        print(
            "Those whitelisted error codes are not reported anymore:",
            ", ".join(non_matching_ignored_codes),
        )
        print(f"This is probably due to a {checker_name} version upgrade")
        print(
            "Those whitelisted error codes should me removed from:",
            ignore_whitelist_filepath,
        )
        sys.exit(1)
