import json, os, sys
from collections import defaultdict


def main(
    checker_name,
    analyze_pdf_file,
    analyze_directory_of_pdf_files,
    argv,
    checks_details_url,
):
    if len(argv) != 2:
        print(argv, file=sys.stderr)
        print(
            f"Exactly one argument must be passed to {checker_name}.py", file=sys.stderr
        )
        sys.exit(2)
    elif argv[1] == "--print-aggregated-report":
        print_aggregated_report(checker_name, checks_details_url)
    elif argv[1] == "--process-all-test-pdf-files":
        process_all_test_pdf_files(checker_name, analyze_directory_of_pdf_files)
    else:
        print(analyze_pdf_file(argv[1]))


def process_all_test_pdf_files(checker_name, analyze_directory_of_pdf_files):
    reports_per_pdf_filepath = analyze_directory_of_pdf_files("test")

    agg_report = aggregate(checker_name, reports_per_pdf_filepath)
    print(
        "Failures:", len(agg_report["failures"]), "Errors:", len(agg_report["errors"])
    )


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
        "errors": defaultdict(list),
    }
    try:
        with open(aggregated_report_filepath, encoding="utf8") as agg_file:
            prev_agg_report = json.load(agg_file)
        agg_report["failures"].update(prev_agg_report["failures"])
        agg_report["errors"].update(prev_agg_report["errors"])
    except FileNotFoundError:
        print("Initializing a new JSON file for the aggregated report")
        report = list(reports_per_pdf_filepath.items())[0][1]
        if "version" in report:
            agg_report["version"] = report.pop("version")
    for pdf_filepath, report in reports_per_pdf_filepath.items():
        if "failure" in report:
            agg_report["failures"][report["failure"]].append(pdf_filepath)
        else:
            for error in report.get("errors", ()):
                agg_report["errors"][error].append(pdf_filepath)
    with open(aggregated_report_filepath, "w", encoding="utf8") as agg_file:
        json.dump(agg_report, agg_file, indent=4)
    return agg_report


def print_aggregated_report(checker_name, checks_details_url):
    aggregated_report_filepath = f"{checker_name}-aggregated.json"
    ignore_whitelist_filepath = f"scripts/{checker_name}-ignore.json"
    with open(aggregated_report_filepath, encoding="utf8") as agg_file:
        agg_report = json.load(agg_file)
    if "version" in agg_report:
        print(agg_report["version"])
    print("Documentation on the checks:", checks_details_url)
    print("# AGGREGATED REPORT #")
    if agg_report["failures"]:
        print("Failures:")
        for failure, pdf_filepaths in sorted(agg_report["failures"].items()):
            print(f"- {failure} ({len(pdf_filepaths)}): {', '.join(pdf_filepaths)}")
    print("Errors:")
    for error, pdf_filepaths in sorted(
        sorted(agg_report["errors"].items(), key=lambda error: -len(error[1]))
    ):
        print(f"- {error} ({len(pdf_filepaths)}): {', '.join(pdf_filepaths)}")
    fail_on_unexpected_check_failure(agg_report, ignore_whitelist_filepath)


def fail_on_unexpected_check_failure(agg_report, ignore_whitelist_filepath):
    "exit(1) if there is any non-passing & non-whitelisted error remaining"
    with open(ignore_whitelist_filepath, encoding="utf8") as ignore_file:
        ignore = json.load(ignore_file)
    errors = set(agg_report["errors"].keys()) - set(ignore["errors"].keys())
    if agg_report["failures"] or errors:
        print(
            "Non-whitelisted issues found:",
            ", ".join(sorted(agg_report["failures"].keys()) + sorted(errors)),
        )
        sys.exit(1)
