#!/bin/bash

# Install Datalogics PDF Checker on a Linux system

# USAGE: ./install-pdfchecker.sh [$install_dir_path]

set -o pipefail -o errexit -o nounset -o xtrace

BASE_URL=https://cdn.datalogics.com/evals
DOWNLOADED_FILENAME=PDF-Optimizer-Checker-Linux64.bsx
INSTALL_DIR_PATH=${1:-$PWD/PDF_Checker}
export TMPDIR=$(mktemp -d /tmp/pdfchecker.XXXXXX)

wget --quiet $BASE_URL/$DOWNLOADED_FILENAME

bsx_extract() {
    local bsx_filepath=${1?'Missing arg'}
    local archive=$(awk '/^__ARCHIVE_BELOW__/ {print NR + 1; exit 0; }' $bsx_filepath)
    tail -q -n+$archive $bsx_filepath | tar xzv -C $TMPDIR
    rm $bsx_filepath
}

# Reproducing the first lines of the .bsx "Self Extracting Installer" script:
bsx_extract $(ls *.bsx)
bsx_extract $TMPDIR/PDF_Checker.bsx

# Reproducing $TMPDIR/installer script behaviour:
mkdir -p "$INSTALL_DIR_PATH"
tar -xf $TMPDIR/PDFChecker.tar -C "$INSTALL_DIR_PATH"
rm -rf $TMPDIR
rm $INSTALL_DIR_PATH/*.pdf
