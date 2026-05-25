import pytest
from src.simulacao.modelos import Ponto, Drone, distancia


def test_ponto_inicializacao():
    ponto = Ponto(nome="A", x=10.0, y=20.0, raio=5.0)
    assert ponto.nome == "A"
    assert ponto.x == 10.0
    assert ponto.y == 20.0
    assert ponto.raio == 5.0
    assert ponto.posicao == (10.0, 20.0)


def test_distancia():
    assert distancia((0, 0), (3, 4)) == 5.0
    assert distancia((1, 1), (1, 1)) == 0.0


def test_drone_inicializacao_padrao():
    drone = Drone(
        nome="D1",
        posicao_atual=(0.0, 0.0),
        rota=[(10.0, 0.0)],
        rota_nomes=["P1"],
        rota_raios=[2.0],
        raio=1.0,
        velocidade=5.0
    )
    assert drone.nome == "D1"
    assert drone.ativo is True
    assert drone.destino == (10.0, 0.0)
    assert drone.destino_nome == "P1"
    assert drone.destino_raio == 2.0
    assert drone.distancia_ate_destino() == 10.0


def test_drone_rota_vazia():
    drone = Drone(
        nome="D1",
        posicao_atual=(5.0, 5.0),
        rota=[],
        rota_nomes=[],
        rota_raios=[],
        raio=1.0,
        velocidade=5.0
    )
    assert drone.destino == (5.0, 5.0)
    assert drone.destino_nome == ""
    assert drone.destino_raio == 0.0
    assert drone.distancia_ate_destino() == 0.0


def test_drone_ativo():
    drone = Drone(
        nome="D1", posicao_atual=(0,0), rota=[], rota_nomes=[], rota_raios=[],
        raio=1.0, velocidade=1.0
    )
    assert drone.ativo is True
    
    drone.colidiu = True
    assert drone.ativo is False
    
    drone.colidiu = False
    drone.entregou = True
    assert drone.ativo is False
    
    drone.entregou = False
    drone.nao_concluiu = True
    assert drone.ativo is False


def test_drone_multiplos_destinos():
    drone = Drone(
        nome="D1",
        posicao_atual=(0.0, 0.0),
        rota=[(10.0, 0.0), (10.0, 10.0)],
        rota_nomes=["P1", "P2"],
        rota_raios=[1.0, 2.0],
        raio=1.0,
        velocidade=5.0
    )
    assert drone.destino == (10.0, 0.0)
    assert drone.destino_nome == "P1"
    assert drone.destino_raio == 1.0
    
    drone.indice_rota += 1
    assert drone.destino == (10.0, 10.0)
    assert drone.destino_nome == "P2"
    assert drone.destino_raio == 2.0
    
    # Se indice_rota passar do limite, retorna o ultimo
    drone.indice_rota += 1
    assert drone.destino == (10.0, 10.0)
    assert drone.destino_nome == "P2"
    assert drone.destino_raio == 2.0

def test_parede_inicializacao():
    from src.simulacao.modelos import Parede
    p = Parede("P1", (0.0, 0.0), (10.0, 10.0))
    assert p.nome == "P1"
    assert p.p1 == (0.0, 0.0)
    assert p.p2 == (10.0, 10.0)

def test_segmentos_se_cruzam():
    from src.simulacao.modelos import segmentos_se_cruzam
    # Cruzam no meio
    assert segmentos_se_cruzam((0, 0), (10, 10), (0, 10), (10, 0)) is True
    # Nao cruzam, paralelos
    assert segmentos_se_cruzam((0, 0), (10, 0), (0, 10), (10, 10)) is False
    # Nao cruzam, nao paralelos
    assert segmentos_se_cruzam((0, 0), (5, 5), (6, 6), (10, 10)) is False
    # Colineares e sobrepostos
    assert segmentos_se_cruzam((0, 0), (10, 10), (5, 5), (15, 15)) is True
    # Tocam na ponta
    assert segmentos_se_cruzam((0, 0), (5, 5), (5, 5), (10, 0)) is True

def test_intersecao_segmentos():
    from src.simulacao.modelos import intersecao_segmentos
    # Cruzam no meio
    p = intersecao_segmentos((0, 0), (10, 10), (0, 10), (10, 0))
    assert p is not None
    assert abs(p[0] - 5.0) < 1e-5
    assert abs(p[1] - 5.0) < 1e-5

    # Nao cruzam
    assert intersecao_segmentos((0, 0), (10, 0), (0, 10), (10, 10)) is None

    # Colineares (retorna None por causa do determinante zero)
    assert intersecao_segmentos((0, 0), (10, 10), (5, 5), (15, 15)) is None
