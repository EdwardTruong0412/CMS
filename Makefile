SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.NOTPARALLEL:
.DEFAULT_GOAL := check

PYTHON ?= python3.13
API_DIR := $(CURDIR)/src/api
WEB_DIR := $(CURDIR)/src/web
VENV_BIN := $(API_DIR)/.venv/bin
TFLINT_HOME := $(CURDIR)/.cache/home
TFLINT_CONFIG := $(CURDIR)/.tflint.hcl

.PHONY: bootstrap deps check check-api check-web check-terraform

bootstrap:
	brew install tfenv tflint trivy python@3.13
	brew install --cask drawio
	tfenv install

deps:
	$(PYTHON) -m venv "$(API_DIR)/.venv"
	"$(VENV_BIN)/python" -m pip install --disable-pip-version-check -e "$(API_DIR)[dev]"
	cd "$(WEB_DIR)" && npm ci

check: check-api check-web check-terraform

check-api:
	@test -x "$(VENV_BIN)/pytest" || { echo "src/api/.venv is missing: run make deps"; exit 1; }
	cd "$(API_DIR)" && "$(VENV_BIN)"/ruff check .
	cd "$(API_DIR)" && "$(VENV_BIN)"/ruff format --check .
	cd "$(API_DIR)" && "$(VENV_BIN)/mypy"
	cd "$(API_DIR)" && "$(VENV_BIN)/pytest"

check-web:
	@test -d "$(WEB_DIR)/node_modules" || { echo "src/web/node_modules is missing: run make deps"; exit 1; }
	cd "$(WEB_DIR)" && npm run lint
	cd "$(WEB_DIR)" && npm run typecheck
	cd "$(WEB_DIR)" && npm run build

check-terraform:
	terraform fmt -check -recursive
	mkdir -p "$(TFLINT_HOME)"
	HOME="$(TFLINT_HOME)" tflint --init --config "$(TFLINT_CONFIG)"
	HOME="$(TFLINT_HOME)" tflint --recursive --config "$(TFLINT_CONFIG)"
