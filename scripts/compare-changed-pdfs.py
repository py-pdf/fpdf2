#!/usr/bin/env python3

# Generate a HTML page that makes it easy to visually compare all PDF files
# that are modified in the current branch, compared to the master branch.

# USAGE: ./compare-changed-pdfs.py [test_subdir_path]

import sys, webbrowser
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from os import makedirs, scandir
from pathlib import Path
from subprocess import check_output

from jinja2 import Environment, FileSystemLoader

PORT = 8000
TEMPLATE_FILENAME = "changed_pdfs_comparison.html"

SCRIPTS_DIR = Path(__file__).parent
REPO_DIR = SCRIPTS_DIR.parent
TMP_DIR = REPO_DIR / "master-checkouts"
VIEW_SLICE = slice(0, 50)


def scantree_dirs(path):
    "Recursively yield DirEntry objects for all sub-directories in the given folder"
    yield path
    for entry in scandir(path):
        if entry.is_dir():
            yield from scantree_dirs(entry.path)


target_dir = sys.argv[1] if len(sys.argv) > 1 else "test/"
print(f"Processing all PDF reference files in directory {target_dir}")

stdout = check_output("git diff --name-status master", shell=True)
changed_pdf_files = [
    line[1:].strip()
    for line in stdout.decode("utf-8").splitlines()
    if line.startswith(f"M\t{target_dir}") and line.endswith(".pdf")
]
changes_pdf_files_count = len(changed_pdf_files)
changed_pdf_files = changed_pdf_files[VIEW_SLICE]
is_shrunk = len(changed_pdf_files) < changes_pdf_files_count

for changed_pdf_file in changed_pdf_files:
    (TMP_DIR / Path(changed_pdf_file)).parent.mkdir(exist_ok=True, parents=True)
    command = f"git show master:{changed_pdf_file} > {TMP_DIR}/{changed_pdf_file}"
    print(command)
    check_output(command, shell=True)

env = Environment(
    loader=FileSystemLoader(str(SCRIPTS_DIR)),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)
template = env.get_template(TEMPLATE_FILENAME)
(REPO_DIR / TEMPLATE_FILENAME).write_text(
    template.render(
        changed_pdf_files=changed_pdf_files,
        is_shrunk=is_shrunk,
        changes_pdf_files_count=changes_pdf_files_count,
        VIEW_SLICE=VIEW_SLICE,
    )
)

httpd = HTTPServer(
    ("", PORT), partial(SimpleHTTPRequestHandler, directory=str(REPO_DIR))
)
webbrowser.open(f"http://localhost:{PORT}/{TEMPLATE_FILENAME}")
httpd.serve_forever()
