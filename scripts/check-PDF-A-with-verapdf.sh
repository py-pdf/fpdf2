#!/bin/bash
# USAGE: ./check-PDF-A-with-verapdf.sh
set -o pipefail -o errexit -o nounset -o xtrace
cd "$(dirname "$0")"/..
for pdf_file in test/pdf-a/*.pdf; do
    ./verapdf/verapdf --format text -v $pdf_file
done
