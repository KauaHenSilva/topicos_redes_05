import pytest
from src.simulacao.configuracao import (
    preparar_configuracao_simulacao,
    ConfiguracaoSimulacao,
    _ler_tamanho_ambiente,
    _ler_pontos,
    _ler_drones,
    _resolver_posicao,
    _ler_paredes,
)


def test_tamanho_ambiente_valido():
    config = {"tamanho_ambiente": [20.0, 30.0]}
    assert _ler_tamanho_ambiente(config) == (20.0, 30.0)


def test_tamanho_ambiente_invalido():
    with pytest.raises(ValueError, match="tamanho_ambiente deve ter valores maiores que zero."):
        _ler_tamanho_ambiente({"tamanho_ambiente": [0, 10]})

    with pytest.raises(ValueError, match="tamanho_ambiente deve ser uma lista"):
        _ler_tamanho_ambiente({"tamanho_ambiente": [10]})


def test_ler_pontos_valido():
    pontos_config = {
        "A": {"x": 10, "y": 20, "r": 5},
        "B": {"x": 0, "y": 0}
    }
    pontos = _ler_pontos(pontos_config, (100.0, 100.0))
    assert len(pontos) == 2
    assert pontos["A"].x == 10.0
    assert pontos["A"].raio == 5.0
    assert pontos["B"].raio == 0.0


def test_ler_pontos_invalido():
    with pytest.raises(ValueError, match="Pontos deve conter pelo menos um ponto nomeado."):
        _ler_pontos({}, (100, 100))

    with pytest.raises(ValueError, match="fora do ambiente"):
        _ler_pontos({"A": {"x": 110, "y": 50}}, (100, 100))

    with pytest.raises(ValueError, match="nao pode ter raio negativo"):
        _ler_pontos({"A": {"x": 10, "y": 10, "r": -1}}, (100, 100))


def test_resolver_posicao():
    pontos = {"A": type("PontoMock", (), {"posicao": (10.0, 20.0), "nome": "A", "raio": 5.0})()}
    # Teste de referência por nome
    pos, nome, raio = _resolver_posicao("A", pontos, (100, 100), "ctx")
    assert pos == (10.0, 20.0)
    assert nome == "A"
    assert raio == 5.0

    # Teste de tupla ou lista
    pos, nome, raio = _resolver_posicao([30, 40], {}, (100, 100), "ctx")
    assert pos == (30.0, 40.0)
    assert nome == "(30.0, 40.0)"
    assert raio == 0.0

    # Teste dict
    pos, nome, raio = _resolver_posicao({"x": 50, "y": 60, "r": 2}, {}, (100, 100), "ctx")
    assert pos == (50.0, 60.0)
    assert raio == 2.0


def test_ler_drones_retrocompatibilidade_e_rota():
    pontos = {"A": type("P", (), {"posicao": (10, 10), "nome": "A", "raio": 1.0})(),
              "B": type("P", (), {"posicao": (20, 20), "nome": "B", "raio": 2.0})()}
    
    drones_config = {
        "drone1": {
            "posicao_inicial": "A",
            "posicao_destino": "B",
            "raio": 1.0,
            "velocidade": 5.0
        },
        "drone2": {
            "posicao_inicial": "A",
            "rota": ["B", {"x": 5, "y": 5}],
            "raio": 2.0,
            "velocidade": 10.0
        }
    }

    drones = _ler_drones(drones_config, pontos, (100, 100))
    
    # drone1 test backward compatibility
    assert drones["drone1"].posicao_atual == (10, 10)
    assert drones["drone1"].rota == [(20, 20)]
    assert drones["drone1"].rota_nomes == ["B"]
    
    # drone2 test multiple routes
    assert len(drones["drone2"].rota) == 2
    assert drones["drone2"].rota == [(20, 20), (5.0, 5.0)]
    assert drones["drone2"].rota_nomes == ["B", "(5.0, 5.0)"]


def test_preparar_configuracao_completa():
    config_raw = {
        "tamanho_ambiente": [100, 100],
        "Pontos": {"A": {"x": 10, "y": 10}},
        "drones": {
            "d1": {"posicao_inicial": "A", "posicao_destino": "A"}
        },
        "numero_drones": 5
    }
    
    config = preparar_configuracao_simulacao(config_raw)
    assert len(config.avisos) > 0
    assert "numero_drones informa 5" in config.avisos[0]
    assert len(config.drones) == 1


def test_ler_paredes_valido():
    paredes_config = {
        "Muro": {"p1": [10.0, 10.0], "p2": [50.0, 50.0]}
    }
    paredes = _ler_paredes(paredes_config, (100.0, 100.0))
    assert len(paredes) == 1
    assert paredes["Muro"].nome == "Muro"
    assert paredes["Muro"].p1 == (10.0, 10.0)
    assert paredes["Muro"].p2 == (50.0, 50.0)


def test_ler_paredes_invalido():
    with pytest.raises(ValueError, match="deve ter p1 e p2"):
        _ler_paredes({"P1": {"p1": [0, 0]}}, (100.0, 100.0))

    with pytest.raises(ValueError, match="p1 deve ser lista"):
        _ler_paredes({"P1": {"p1": 0, "p2": [0, 0]}}, (100.0, 100.0))

    with pytest.raises(ValueError, match="fora do ambiente"):
        _ler_paredes({"P1": {"p1": [150.0, 0.0], "p2": [0.0, 0.0]}}, (100.0, 100.0))

    assert _ler_paredes({}, (100.0, 100.0)) == {}
