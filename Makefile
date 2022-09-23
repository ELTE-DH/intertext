.DEFAULT_GOAL = all
# Bash is needed for time, compgen, [[ and other builtin commands
SHELL := /bin/bash -o pipefail
RED := $(shell tput setaf 1)
GREEN := $(shell tput setaf 2)
NOCOLOR := $(shell tput sgr0)


# These targets do not show as possible target with bash completion
__extra-deps:
	@# Do extra stuff (e.g. compiling, downloading) before building the package
	@exit 0
.PHONY: __extra-deps

__clean-extra-deps:
	@# e.g. @rm -rf stuff
	@exit 0
.PHONY: __clean-extra-deps

clean: __clean-extra-deps
	@if [ -f "./venv/bin/poetry" ]; then rm -rf $$(./venv/bin/poetry env info -p); fi
	@rm -rf dist/ venv/ cache output
.PHONY: clean

venv:
	rm -rf venv
	python3 -m venv venv
	./venv/bin/pip install poetry
	./venv/bin/poetry env use python3
	./venv/bin/poetry install --no-root
.PHONY: venv

build: venv __extra-deps
	@poetry build
.PHONY: build

install: build
	 @poetry run pip install --upgrade dist/*.whl
.PHONY: install

run_sample: install
	./venv/bin/poetry run python src/intertext/intertext_main.py --infiles "sample_data/texts/*.txt" --metadata "sample_data/metadata.json"
	./venv/bin/poetry run python -m http.server 8000 --directory output
.PHONY: run_sample

all: clean venv install run_sample