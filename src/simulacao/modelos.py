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
    rota: list[tuple[float, float]]
    rota_nomes: list[str]
    rota_raios: list[float]
    raio: float
    velocidade: float
    indice_rota: int = 0
    status: str = "pegou"
    colidiu: bool = False
    entregou: bool = False
    nao_concluiu: bool = False
    tempo_missao: float = 0.0
    distancia_percorrida: float = 0.0

    @property
    def ativo(self) -> bool:
        return not self.colidiu and not self.entregou and not self.nao_concluiu

    @property
    def destino(self) -> tuple[float, float]:
        if self.indice_rota < len(self.rota):
            return self.rota[self.indice_rota]
        return self.rota[-1] if self.rota else self.posicao_atual

    @property
    def destino_nome(self) -> str:
        if self.indice_rota < len(self.rota_nomes):
            return self.rota_nomes[self.indice_rota]
        return self.rota_nomes[-1] if self.rota_nomes else ""

    @property
    def destino_raio(self) -> float:
        if self.indice_rota < len(self.rota_raios):
            return self.rota_raios[self.indice_rota]
        return self.rota_raios[-1] if self.rota_raios else 0.0

    def distancia_ate_destino(self) -> float:
        if not self.rota:
            return 0.0
        return distancia(self.posicao_atual, self.destino)


def distancia(a: tuple[float, float], b: tuple[float, float]) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def distancia_ponto_segmento(pt: tuple[float, float], p1: tuple[float, float], p2: tuple[float, float]) -> float:
    l2 = distancia(p1, p2)**2
    if l2 == 0:
        return distancia(pt, p1)
    t = ((pt[0] - p1[0]) * (p2[0] - p1[0]) + (pt[1] - p1[1]) * (p2[1] - p1[1])) / l2
    t = max(0.0, min(1.0, t))
    proj_x = p1[0] + t * (p2[0] - p1[0])
    proj_y = p1[1] + t * (p2[1] - p1[1])
    return distancia(pt, (proj_x, proj_y))


@dataclass(frozen=True)
class Parede:
    nome: str
    p1: tuple[float, float]
    p2: tuple[float, float]


def orientacao(p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]) -> int:
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
    if abs(val) < 1e-9:
        return 0
    return 1 if val > 0 else 2


def no_segmento(p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]) -> bool:
    return (max(p[0], r[0]) + 1e-9 >= q[0] >= min(p[0], r[0]) - 1e-9 and 
            max(p[1], r[1]) + 1e-9 >= q[1] >= min(p[1], r[1]) - 1e-9)


def segmentos_se_cruzam(
    p1: tuple[float, float], q1: tuple[float, float],
    p2: tuple[float, float], q2: tuple[float, float]
) -> bool:
    o1 = orientacao(p1, q1, p2)
    o2 = orientacao(p1, q1, q2)
    o3 = orientacao(p2, q2, p1)
    o4 = orientacao(p2, q2, q1)

    if o1 != o2 and o3 != o4:
        return True

    if o1 == 0 and no_segmento(p1, p2, q1): return True
    if o2 == 0 and no_segmento(p1, q2, q1): return True
    if o3 == 0 and no_segmento(p2, p1, q2): return True
    if o4 == 0 and no_segmento(p2, q1, q2): return True

    return False


def intersecao_segmentos(
    p1: tuple[float, float], q1: tuple[float, float],
    p2: tuple[float, float], q2: tuple[float, float]
) -> tuple[float, float] | None:
    if not segmentos_se_cruzam(p1, q1, p2, q2):
        return None

    a1 = q1[1] - p1[1]
    b1 = p1[0] - q1[0]
    c1 = a1 * p1[0] + b1 * p1[1]

    a2 = q2[1] - p2[1]
    b2 = p2[0] - q2[0]
    c2 = a2 * p2[0] + b2 * p2[1]

    det = a1 * b2 - a2 * b1
    if abs(det) < 1e-9:
        # Colineares
        return None

    x = (b2 * c1 - b1 * c2) / det
    y = (a1 * c2 - a2 * c1) / det
    return (x, y)

