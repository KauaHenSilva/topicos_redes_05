"""Carregamento e validacao da configuracao da simulacao."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from .modelos import Drone, Ponto, Parede


@dataclass(frozen=True)
class ConfiguracaoSimulacao:
    tamanho_ambiente: tuple[float, float]
    pontos: dict[str, Ponto]
    drones: dict[str, Drone]
    paredes: dict[str, Parede]
    avisos: list[str]


def carregar_configuracao(caminho: str | Path) -> dict[str, Any]:
    """Carrega o arquivo JSON usado como entrada da simulacao."""

    arquivo = Path(caminho)
    with arquivo.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def preparar_configuracao_simulacao(configuracao: dict[str, Any]) -> ConfiguracaoSimulacao:
    tamanho_ambiente = _ler_tamanho_ambiente(configuracao)
    pontos = _ler_pontos(configuracao.get("Pontos", {}), tamanho_ambiente)
    drones = _ler_drones(configuracao.get("drones", {}), pontos, tamanho_ambiente)
    paredes = _ler_paredes(configuracao.get("paredes", {}), tamanho_ambiente)
    avisos = _validar_numero_drones(configuracao.get("numero_drones"), len(drones))

    return ConfiguracaoSimulacao(
        tamanho_ambiente=tamanho_ambiente,
        pontos=pontos,
        drones=drones,
        paredes=paredes,
        avisos=avisos,
    )


def _ler_tamanho_ambiente(configuracao: dict[str, Any]) -> tuple[float, float]:
    tamanho = configuracao.get("tamanho_ambiente")
    if isinstance(tamanho, list):
        tamanho_lista = cast(list[Any], tamanho)
        if len(tamanho_lista) != 2:
            raise ValueError("tamanho_ambiente deve ser uma lista [largura, altura].")
        largura, altura = float(tamanho_lista[0]), float(tamanho_lista[1])
    elif isinstance(tamanho, tuple):
        tamanho_lista = cast(tuple[Any, Any], tamanho)
        if len(tamanho_lista) != 2:
            raise ValueError("tamanho_ambiente deve ser uma lista [largura, altura].")
        largura, altura = float(tamanho_lista[0]), float(tamanho_lista[1])
    else:
        raise ValueError("tamanho_ambiente deve ser uma lista [largura, altura].")

    if largura <= 0 or altura <= 0:
        raise ValueError("tamanho_ambiente deve ter valores maiores que zero.")
    return (largura, altura)


def _ler_pontos(
    pontos_config: dict[str, Any], tamanho_ambiente: tuple[float, float]
) -> dict[str, Ponto]:
    if not pontos_config:
        raise ValueError("Pontos deve conter pelo menos um ponto nomeado.")

    pontos: dict[str, Ponto] = {}
    for nome, dados in pontos_config.items():
        if not isinstance(dados, dict):
            raise ValueError(f"Ponto {nome} deve ser um objeto com x, y e r.")

        dados_ponto = cast(dict[str, Any], dados)
        ponto = Ponto(
            nome=nome,
            x=float(dados_ponto["x"]),
            y=float(dados_ponto["y"]),
            raio=float(dados_ponto.get("r", 0)),
        )
        _validar_posicao_no_ambiente(ponto.posicao, tamanho_ambiente, f"Ponto {nome}")
        if ponto.raio < 0:
            raise ValueError(f"Ponto {nome} nao pode ter raio negativo.")
        pontos[nome] = ponto
    return pontos


def _ler_paredes(
    paredes_config: dict[str, Any], tamanho_ambiente: tuple[float, float]
) -> dict[str, Parede]:
    if not paredes_config:
        return {}

    paredes: dict[str, Parede] = {}
    for nome, dados in paredes_config.items():
        if not isinstance(dados, dict):
            raise ValueError(f"Parede {nome} deve ser um objeto com p1 e p2.")

        dados_parede = cast(dict[str, Any], dados)
        if "p1" not in dados_parede or "p2" not in dados_parede:
            raise ValueError(f"Parede {nome} deve ter p1 e p2.")

        p1_list = dados_parede["p1"]
        p2_list = dados_parede["p2"]

        if not isinstance(p1_list, list) or len(p1_list) != 2:
            raise ValueError(f"Parede {nome} p1 deve ser lista [x, y].")
        if not isinstance(p2_list, list) or len(p2_list) != 2:
            raise ValueError(f"Parede {nome} p2 deve ser lista [x, y].")

        p1 = (float(p1_list[0]), float(p1_list[1]))
        p2 = (float(p2_list[0]), float(p2_list[1]))

        _validar_posicao_no_ambiente(p1, tamanho_ambiente, f"Parede {nome} p1")
        _validar_posicao_no_ambiente(p2, tamanho_ambiente, f"Parede {nome} p2")

        paredes[nome] = Parede(nome=nome, p1=p1, p2=p2)

    return paredes


def _ler_drones(
    drones_config: dict[str, Any],
    pontos: dict[str, Ponto],
    tamanho_ambiente: tuple[float, float],
) -> dict[str, Drone]:
    if not drones_config:
        raise ValueError("drones deve conter pelo menos um drone nomeado.")

    drones: dict[str, Drone] = {}
    for nome, dados in drones_config.items():
        if not isinstance(dados, dict):
            raise ValueError(f"Drone {nome} deve ser um objeto.")

        dados_drone = cast(dict[str, Any], dados)
        posicao_inicial, _inicial_nome, _inicial_raio = _resolver_posicao(
            dados_drone["posicao_inicial"],
            pontos,
            tamanho_ambiente,
            f"posicao_inicial de {nome}",
        )
        if "rota" in dados_drone:
            rota_raw = dados_drone["rota"]
            if not isinstance(rota_raw, list):
                raise ValueError(f"A rota de {nome} deve ser uma lista.")
        elif "posicao_destino" in dados_drone:
            rota_raw = [dados_drone["posicao_destino"]]
        else:
            raise ValueError(f"O Drone {nome} deve ter 'rota' ou 'posicao_destino'.")

        rota: list[tuple[float, float]] = []
        rota_nomes: list[str] = []
        rota_raios: list[float] = []

        for wp in rota_raw:
            pos, dest_nome, dest_raio = _resolver_posicao(
                wp,
                pontos,
                tamanho_ambiente,
                f"destino da rota de {nome}",
            )
            rota.append(pos)
            rota_nomes.append(dest_nome)
            rota_raios.append(dest_raio)

        raio = float(dados_drone.get("raio", 0))
        velocidade = float(dados_drone.get("velocidade", 1))

        if raio < 0:
            raise ValueError(f"Drone {nome} nao pode ter raio negativo.")
        if velocidade <= 0:
            raise ValueError(f"Drone {nome} deve ter velocidade maior que zero.")

        drones[nome] = Drone(
            nome=nome,
            posicao_atual=posicao_inicial,
            rota=rota,
            rota_nomes=rota_nomes,
            rota_raios=rota_raios,
            raio=raio,
            velocidade=velocidade,
        )
    return drones


def _resolver_posicao(
    valor: Any,
    pontos: dict[str, Ponto],
    tamanho_ambiente: tuple[float, float],
    contexto: str,
) -> tuple[tuple[float, float], str, float]:
    if isinstance(valor, str):
        if valor not in pontos:
            raise ValueError(f"{contexto} referencia ponto inexistente: {valor}.")
        ponto = pontos[valor]
        return ponto.posicao, ponto.nome, ponto.raio

    if isinstance(valor, list):
        valor_lista = cast(list[Any], valor)
        if len(valor_lista) != 2:
            raise ValueError(
                f"{contexto} deve ser o nome de um ponto, uma lista [x, y] ou um objeto com x e y."
            )
        posicao = (float(valor_lista[0]), float(valor_lista[1]))
        _validar_posicao_no_ambiente(posicao, tamanho_ambiente, contexto)
        return posicao, f"({posicao[0]}, {posicao[1]})", 0.0

    if isinstance(valor, tuple):
        valor_lista = cast(tuple[Any, Any], valor)
        if len(valor_lista) != 2:
            raise ValueError(
                f"{contexto} deve ser o nome de um ponto, uma lista [x, y] ou um objeto com x e y."
            )
        posicao = (float(valor_lista[0]), float(valor_lista[1]))
        _validar_posicao_no_ambiente(posicao, tamanho_ambiente, contexto)
        return posicao, f"({posicao[0]}, {posicao[1]})", 0.0

    if isinstance(valor, dict) and "x" in valor and "y" in valor:
        valor_dict = cast(dict[str, Any], valor)
        posicao = (float(valor_dict["x"]), float(valor_dict["y"]))
        _validar_posicao_no_ambiente(posicao, tamanho_ambiente, contexto)
        return posicao, f"({posicao[0]}, {posicao[1]})", float(valor_dict.get("r", 0))

    raise ValueError(
        f"{contexto} deve ser o nome de um ponto, uma lista [x, y] ou um objeto com x e y."
    )


def _validar_posicao_no_ambiente(
    posicao: tuple[float, float],
    tamanho_ambiente: tuple[float, float],
    contexto: str,
) -> None:
    largura, altura = tamanho_ambiente
    x, y = posicao
    if not 0 <= x <= largura or not 0 <= y <= altura:
        raise ValueError(
            f"{contexto} esta fora do ambiente: ({x}, {y}) para {largura}x{altura}."
        )


def _validar_numero_drones(numero_configurado: Any, total_definido: int) -> list[str]:
    if numero_configurado is None:
        return []

    numero = int(numero_configurado)
    if numero != total_definido:
        return [
            "numero_drones informa "
            f"{numero}, mas o JSON define {total_definido} drone(s); "
            "a simulacao usou os drones definidos em 'drones'."
        ]

    return []
