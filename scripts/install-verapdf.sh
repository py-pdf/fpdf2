#!/bin/bash

# Improved veraPDF installation script for Linux

# USAGE: ./install-verapdf.sh

# Define variables
verapdf_download_url="https://software.verapdf.org/rel/1.22/verapdf-greenfield-1.22.3-installer.zip"
installation_path="$PWD/verapdf"

# Function to check if a command is available
command_exists() {
  command -v "$1" > /dev/null 2>&1
}

# Check for dependencies
if ! command_exists wget || ! command_exists unzip; then
  echo "Error: Please install 'wget' and 'unzip' before running this script."
  exit 1
fi

# Clean up previous installations
rm -rf verapdf-*
rm -rf "$installation_path"

# Download veraPDF installer
wget --quiet "$verapdf_download_url"

# Check for download errors
if [ $? -ne 0 ]; then
  echo "Error: Download failed. Please check your internet connection and try again."
  exit 1
fi

# Extract the installer
unzip verapdf*installer.zip

# Check for extraction errors
if [ $? -ne 0 ]; then
  echo "Error: Extraction failed. Please check the downloaded file and try again."
  exit 1
fi

(
    # Press 1 to continue, 2 to quit, 3 to redisplay:
    echo 1
    # Select the installation path:
    echo "$installation_path"
    # Enter O for OK, C to Cancel:
    echo O
    # Press 1 to continue, 2 to quit, 3 to redisplay:
    echo 1
    # Include optional pack 'veraPDF Corpus and Validation model' - Enter Y for Yes, N for No:
    echo N
    # Include optional pack 'veraPDF Documentation' - Enter Y for Yes, N for No:
    echo N
    # Include optional pack 'veraPDF Sample Plugins' - Enter Y for Yes, N for No:
    echo N
    # Press 1 to continue, 2 to quit, 3 to redisplay:
    echo 1
) | verapdf-*/verapdf-install

# Check for installation errors
if [ $? -ne 0 ]; then
  echo "Error: Installation failed. Please check the installation settings and try again."
  exit 1
fi

rm -rf verapdf-*

# Successful installation message
echo "veraPDF has been successfully installed at: $installation_path"