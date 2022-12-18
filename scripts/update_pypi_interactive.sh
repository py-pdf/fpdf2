#!/usr/bin/env bash
cd "$(dirname "$0")"
cd ..

# default usage: run script, hit enter

pypircfile=$HOME/.pypirc
touch "$pypircfile"

# if exists, ask to use + continue, or overwrite + continue
if [[ -e "$pypircfile" ]]; then
  if whiptail --yesno "Use existing ${pypircfile}?" 10 60; then
    echo "Using existing ${pypircfile}."
  else
    if whiptail --yesno "Overwrite existing ${pypircfile}?" 10 60; then
      # delete old
      rm -rf "$pypircfile";
      printf "enter username "; read username
      printf "enter password "; read password

      # make new
      cat > "$pypircfile" << EOF
[distutils]
index-servers =
    pypi

[pypi]
username:$username
password:$password
EOF

    else
      exit 1
    fi
  fi
fi

read -p "Has FPDF_VERSION been updated in fpdf/fpdf.py? (y/n) " -n 1 -r
echo
if ! [[ $REPLY =~ ^[Yy]$ ]]; then echo 'Aborting'; exit 1; fi

read -p "Has the latest version been updated in docs/index.md? (y/n) " -n 1 -r
echo
if ! [[ $REPLY =~ ^[Yy]$ ]]; then echo 'Aborting'; exit 1; fi

# build
python setup.py bdist_wheel
python setup.py sdist

# update PyPI
twine upload dist/*.whl
twine upload dist/*.tar.gz

# remove old stuff
rm -rf build/ dist/

