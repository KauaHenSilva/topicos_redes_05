VENV := .venv
ifeq ($(OS),Windows_NT)
	PYTHON ?= python
	VENV_BIN := $(VENV)/Scripts
else
	PYTHON ?= python3
	VENV_BIN := $(VENV)/bin
endif

VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip

.PHONY: help venv install run-gui test

help:
	@echo "Comandos disponiveis:"
	@echo "  make venv      - cria o ambiente virtual em .venv"
	@echo "  make install   - instala as dependencias do requirements.txt"
	@echo "  make run-gui   - executa a interface grafica"
	@echo "  make test      - executa a suite de testes com analise de cobertura"

venv: $(VENV_PYTHON)

$(VENV_PYTHON):
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV_PIP) install -r requirements.txt

run-gui: install
	$(VENV_PYTHON) main.py

test: install
	$(VENV_BIN)/pytest --cov=src
