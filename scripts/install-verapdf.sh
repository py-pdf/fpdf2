#!/bin/bash

# Install veraPDF on a Linux system

# USAGE: ./install-verapdf.sh

set -o pipefail -o errexit -o nounset -o xtrace

VERSION=1.29.15
PUB_KEY_FINGERPRINT=13DD102B4DD69354D12DE5A83184863278B17FE7
FILENAME=verapdf-greenfield-${VERSION}-installer.zip
ZIP_URL=https://software.verapdf.org/dev/${VERSION%.*}/${FILENAME}

rm -rf verapdf*
wget --quiet ${ZIP_URL}
wget --quiet ${ZIP_URL}.asc
gpg --keyserver keyserver.ubuntu.com --recv ${PUB_KEY_FINGERPRINT}
gpg --verify ${FILENAME}.asc
unzip verapdf*installer.zip
# Path to verapdf.properties must be relative to verapdf-*/ :
verapdf-*/verapdf-install -options ../scripts/verapdf.properties
# verapdf.properties targets an installation in /tmp, because an absolute path is required :
mv /tmp/verapdf .
verapdf/verapdf --version
rm -rf verapdf-*
