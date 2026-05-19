"""Modelos internos usados pelo simulador."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass(frozen=True)
class Ponto:
    nome: str
    x: float
    y: float
    raio: float = 0.0

    @property
    def posicao(self) -> tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Drone:
    nome: str
    posicao_atual: tuple[float, float]
    destino: tuple[float, float]
    destino_nome: str
    destino_raio: float
    raio: float
    velocidade: float
    status: str = "pegou"
    colidiu: bool = False
    entregou: bool = False
    nao_concluiu: bool = False
    tempo_missao: float = 0.0
    distancia_percorrida: float = 0.0

    @property
    def ativo(self) -> bool:
        return not self.colidiu and not self.entregou and not self.nao_concluiu

    def distancia_ate_destino(self) -> float:
        return distancia(self.posicao_atual, self.destino)


def distancia(a: tuple[float, float], b: tuple[float, float]) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])
