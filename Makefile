PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

.PHONY: help venv install run run-cli run-gui

help:
	@echo "Comandos disponiveis:"
	@echo "  make venv      - cria o ambiente virtual em .venv"
	@echo "  make install   - instala as dependencias do requirements.txt"
	@echo "  make run       - executa a simulacao via terminal"
	@echo "  make run-cli   - executa a simulacao via terminal"
	@echo "  make run-gui   - executa a interface grafica"

venv: $(VENV_PYTHON)

$(VENV_PYTHON):
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV_PIP) install -r requirements.txt

run: run-cli

run-cli: install
	$(VENV_PYTHON) main.py

run-gui: install
	$(VENV_PYTHON) src/interface/main.py
