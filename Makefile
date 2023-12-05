VENV_NAME = venv
VENV_PATH = $(VENV_NAME)/bin/activate
SRC_DIR = fpdf
PYTHON := venv/bin/python

.PHONY: venv

venv:
ifeq ($(OS),Windows_NT)
	python -m venv $(VENV_NAME)
	. $(VENV_PATH) && pip install -r test/requirements.txt
else
	python3 -m venv $(VENV_NAME)
	. $(VENV_PATH); pip install -r test/requirements.txt
endif

.PHONY: test

test:
	@export FLASK_ENV=test && python -m pytest test/

.PHONY: install

install: venv
	. $(VENV_PATH); pip install --upgrade -r test/requirements.txt

.PHONY: clean

clean:
	rm -rf $(VENV_NAME)

check-autopep:
	${PYTHON} -m autopep8 $(SRC_DIR)/*.py test/*.py --in-place

check-isort:
	${PYTHON} -m isort --check-only $(SRC_DIR) test

check-flake:
	${PYTHON} -m flake8 $(SRC_DIR) test

check-mypy:
	${PYTHON} -m mypy --strict --implicit-reexport $(SRC_DIR) 

lint: check-flake check-mypy check-autopep check-isort

format:
	${PYTHON} -m autopep8 $(SRC_DIR)/*.py test/*.py --in-place
	${PYTHON} -m isort $(SRC_DIR) test