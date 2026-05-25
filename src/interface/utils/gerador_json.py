"""Utilitarios para exportar a configuracao montada na interface."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


CAMINHO_CONFIG_PADRAO = Path("config/config.json")


def preparar_dados_interface(dados: dict[str, Any]) -> dict[str, Any]:
    """Normaliza uma copia dos dados visuais antes de salvar ou simular."""

    configuracao = copy.deepcopy(dados)
    configuracao.setdefault("numero_drones", 0)
    configuracao.setdefault("tamanho_ambiente", [0, 0])
    configuracao.setdefault("Pontos", {})
    configuracao.setdefault("drones", {})
    configuracao["numero_drones"] = len(configuracao["drones"])
    return configuracao


def carregar_configuracao_interface(caminho: str | Path) -> dict[str, Any]:
    """Carrega um JSON salvo pela interface para reaproveitar um cenario."""

    arquivo = Path(caminho)
    with arquivo.open("r", encoding="utf-8") as fp:
        dados = json.load(fp)

    if not isinstance(dados, dict):
        raise ValueError("O arquivo de configuração deve conter um objeto JSON.")

    caminho_configuracao = dados.get("arquivo_configuracao")
    if caminho_configuracao:
        arquivo_configuracao = Path(str(caminho_configuracao))
        if not arquivo_configuracao.is_absolute():
            arquivo_configuracao = arquivo.parent / arquivo_configuracao
        with arquivo_configuracao.open("r", encoding="utf-8") as fp:
            dados = json.load(fp)
        if not isinstance(dados, dict):
            raise ValueError("O arquivo de configuração deve conter um objeto JSON.")

    configuracao = preparar_dados_interface(dados)
    tamanho = configuracao["tamanho_ambiente"]
    if not isinstance(tamanho, list) or len(tamanho) != 2:
        raise ValueError("tamanho_ambiente deve ser uma lista [largura, altura].")

    largura, altura = float(tamanho[0]), float(tamanho[1])
    if largura <= 0 or altura <= 0:
        raise ValueError("tamanho_ambiente deve ter valores maiores que zero.")

    configuracao["tamanho_ambiente"] = [largura, altura]
    return configuracao


def salvar_configuracao_interface(
    dados: dict[str, Any],
    caminho: str | Path = CAMINHO_CONFIG_PADRAO,
) -> Path:
    """Salva a configuracao da interface em JSON e retorna o caminho usado."""

    arquivo = Path(caminho)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    configuracao = preparar_dados_interface(dados)
    with arquivo.open("w", encoding="utf-8") as fp:
        json.dump(configuracao, fp, ensure_ascii=False, indent=2)
    return arquivo
