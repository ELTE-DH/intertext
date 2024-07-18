.DEFAULT_GOAL = all
# Bash is needed for time, compgen, [[ and other builtin commands
SHELL := /bin/bash -o pipefail
RED := $(shell tput setaf 1)
GREEN := $(shell tput setaf 2)
NOCOLOR := $(shell tput sgr0)
PYTHON ?= python3

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
	$(PYTHON) -m venv venv
	./venv/bin/pip install poetry
	./venv/bin/poetry env use python3
	./venv/bin/poetry install --no-root
.PHONY: venv

build: venv __extra-deps
	@./venv/bin/poetry build
.PHONY: build

build_client:
	@id | grep -q docker || (echo "ERROR: docker command without sudo is not available!" 1>&2; exit 1)
	@docker build src/intertext/client -t yarn
	@cd src/intertext/client && ./compile.sh
.PHONY: build_client

install: build
	 @./venv/bin/poetry run pip install --upgrade dist/*.whl
.PHONY: install

run_sample: install
	./venv/bin/poetry run python ./src/intertext/intertext_main.py --infiles "sample_data/texts/*.txt" --metadata "sample_data/metadata.json" --about_files_dir "sample_data/about_HTMLs" --image_directory "sample_data/images"
	./venv/bin/poetry run python -m http.server 8000 --directory output
.PHONY: run_sample

all: clean venv install run_sample
