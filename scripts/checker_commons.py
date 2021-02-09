import json, sys
from collections import defaultdict


def aggregate(pdf_filepath, report, aggregated_report_filepath):
    agg_report = {
        "failures": defaultdict(list),
        "errors": defaultdict(list),
    }
    try:
        with open(aggregated_report_filepath) as agg_file:
            prev_agg_report = json.load(agg_file)
        agg_report["failures"].update(prev_agg_report["failures"])
        agg_report["errors"].update(prev_agg_report["errors"])
    except FileNotFoundError:
        print("Initializing a new JSON file for the aggregated report")
        if "version" in report:
            agg_report["version"] = report.pop("version")
    if "failure" in report:
        failure = report["failure"]
        agg_report["failures"][failure].append(pdf_filepath)
    else:
        for error in report.get("errors", []):
            agg_report["errors"][error].append(pdf_filepath)
    with open(aggregated_report_filepath, "w") as agg_file:
        json.dump(agg_report, agg_file)


def print_aggregated_report(
    aggregated_report_filepath, checks_details_url, ignore_whitelist_filepath
):
    with open(aggregated_report_filepath) as agg_file:
        agg_report = json.load(agg_file)
    if "version" in agg_report:
        print(agg_report["version"])
    print("Documentation on the checks:", checks_details_url)
    print("# AGGREGATED REPORT #")
    if agg_report["failures"]:
        print("Failures:")
        for failure, pdf_filepaths in agg_report["failures"].items():
            print(f"- {failure} ({len(pdf_filepaths)}): {', '.join(pdf_filepaths)}")
    print("Errors:")
    sort_key = lambda error: -len(error[1])
    for error, pdf_filepaths in sorted(agg_report["errors"].items(), key=sort_key):
        print(f"- {error} ({len(pdf_filepaths)}): {', '.join(pdf_filepaths)}")
    fail_on_unexpected_check_failure(agg_report, ignore_whitelist_filepath)


def fail_on_unexpected_check_failure(agg_report, ignore_whitelist_filepath):
    "exit(1) if there is any non-passing & non-whitelisted error remaining"
    with open(ignore_whitelist_filepath) as ignore_file:
        ignore = json.load(ignore_file)
    errors = set(agg_report["errors"].keys()) - set(ignore["errors"].keys())
    if agg_report["failures"] or errors:
        print(
            "Non-whitelisted issues found:",
            ", ".join(sorted(agg_report["failures"].keys()) + sorted(errors)),
        )
        sys.exit(1)
