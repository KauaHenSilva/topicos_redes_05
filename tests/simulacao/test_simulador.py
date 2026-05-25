import pytest
from src.simulacao.modelos import Drone, Ponto
from src.simulacao.simulador import SimuladorDrones
from src.simulacao.configuracao import ConfiguracaoSimulacao

def _criar_config(drones_dict, paredes_dict=None):
    if paredes_dict is None:
        paredes_dict = {}
    pontos = {
        "A": Ponto("A", 0, 0, 0.0),
        "B": Ponto("B", 10, 0, 0.0),
        "C": Ponto("C", 10, 10, 0.0),
    }
    return ConfiguracaoSimulacao(
        tamanho_ambiente=(20.0, 20.0),
        pontos=pontos,
        drones=drones_dict,
        paredes=paredes_dict,
        avisos=[]
    )

def test_drone_rota_multipla():
    drone1 = Drone(
        nome="drone1", posicao_atual=(0.0, 0.0),
        rota=[(10.0, 0.0), (10.0, 10.0)], rota_nomes=["B", "C"],
        rota_raios=[0.0, 0.0], raio=0.5, velocidade=1.0
    )
    simulador = SimuladorDrones(_criar_config({"drone1": drone1}), max_iteracoes=1000)
    interacoes, resultado = simulador.executar()
    
    assert resultado["drone1"]["entregou"] is True
    assert resultado["drone1"]["colidiu"] is False
    assert resultado["quantidade_ok"] == 1
    assert resultado["taxa_sucesso"] == "100%"

def test_max_iteracoes_invalido():
    with pytest.raises(ValueError, match="max_iteracoes deve ser maior que zero"):
        SimuladorDrones(_criar_config({}), max_iteracoes=0)

def test_colisao_frontal():
    drone1 = Drone("D1", (0.0, 0.0), [(10.0, 0.0)], ["B"], [0.0], 1.0, 1.0)
    drone2 = Drone("D2", (10.0, 0.0), [(0.0, 0.0)], ["A"], [0.0], 1.0, 1.0)
    
    simulador = SimuladorDrones(_criar_config({"D1": drone1, "D2": drone2}))
    interacoes, resultado = simulador.executar()
    
    assert resultado["D1"]["colidiu"] is True
    assert resultado["D2"]["colidiu"] is True
    assert resultado["quantidade_bateu"] == 2
    assert resultado["taxa_colisao"] == "100%"

def test_nao_concluiu():
    # Drone muito lento para chegar em 5 iteracoes (tempo max seria 5 * dist/vel mas iteracoes conta diferente)
    # Na verdade, se houver outro drone ou evento, as iteracoes passam.
    # Mas se for 1 drone, ele calcula o delta_tempo para chegar direto!
    # Entao ele SEMPRE chega em 1 iteracao se não houver colisão limitando.
    # Para forçar nao concluiu, precisamos de iteracoes esgotadas.
    # Se max_iteracoes for 0 ele ja quebra na inicializacao.
    # Mas iteracao só incrementa a cada evento.
    pass

def test_nao_concluiu_via_max_iteracoes():
    # Para gerar iteracoes infinitas / estourar limite, 
    # criamos dois drones que não colidem mas geram muitos micro-eventos?
    # Não, podemos forçar definindo max_iteracoes=1 e tendo uma rota longa que requeira varios waypoints.
    drone1 = Drone("D1", (0.0, 0.0), [(5.0, 0.0), (10.0, 0.0)], ["P1", "P2"], [0.0, 0.0], 0.5, 1.0)
    simulador = SimuladorDrones(_criar_config({"D1": drone1}), max_iteracoes=1)
    interacoes, resultado = simulador.executar()
    
    assert resultado["D1"]["nao_concluiu"] is True
    assert resultado["D1"]["entregou"] is False

def test_ja_no_destino():
    drone1 = Drone("D1", (0.0, 0.0), [(0.0, 0.0)], ["A"], [0.0], 0.5, 1.0)
    simulador = SimuladorDrones(_criar_config({"D1": drone1}))
    interacoes, resultado = simulador.executar()
    
    assert resultado["D1"]["entregou"] is True
    assert resultado["D1"]["distancia_percorrida"] == 0.0

def test_drone_parado_na_frente():
    # D1 vai pra (10,0), D2 ja esta no meio parado (5,0) indo pro mesmo lugar ja entregue (ou parado).
    # Como o simulador lida?
    drone1 = Drone("D1", (0.0, 0.0), [(10.0, 0.0)], ["B"], [0.0], 1.0, 1.0)
    drone2 = Drone("D2", (5.0, 0.0), [(0.0, 0.0)], ["P"], [0.0], 1.0, 1.0) # indo para oeste (contra o D1)
    
    simulador = SimuladorDrones(_criar_config({"D1": drone1, "D2": drone2}))
    interacoes, resultado = simulador.executar()
    
    assert resultado["D1"]["colidiu"] is True
    assert resultado["D2"]["colidiu"] is True

def test_drone_alcanca_destino_com_raio_maior():
    # Distancia 10, raio do destino é 5.
    # O Drone deve andar 5 e dizer que entregou.
    drone1 = Drone("D1", (0.0, 0.0), [(10.0, 0.0)], ["B"], [5.0], 0.5, 1.0)
    simulador = SimuladorDrones(_criar_config({"D1": drone1}))
    interacoes, resultado = simulador.executar()
    
    assert resultado["D1"]["entregou"] is True
    assert abs(resultado["D1"]["distancia_percorrida"] - 5.0) < 1e-5

def test_detectar_colisao_inicial():
    drone1 = Drone("D1", (0.0, 0.0), [(10.0, 0.0)], ["B"], [0.0], 1.0, 1.0)
    drone2 = Drone("D2", (1.0, 0.0), [(10.0, 0.0)], ["B"], [0.0], 1.0, 1.0)
    # A distancia inicial entre D1 e D2 eh 1.0. A soma dos raios eh 2.0.
    # Eles colidem no instante t=0.
    simulador = SimuladorDrones(_criar_config({"D1": drone1, "D2": drone2}))
    interacoes, resultado = simulador.executar()
    
    assert resultado["D1"]["colidiu"] is True
    assert resultado["D2"]["colidiu"] is True
    assert resultado["tempo_total"] == 0.0

def test_colisao_com_parede():
    from src.simulacao.modelos import Parede
    drone1 = Drone("D1", (0.0, 0.0), [(10.0, 0.0)], ["B"], [0.0], 1.0, 1.0)
    parede = Parede("Muro", (5.0, -5.0), (5.0, 5.0)) # Parede cruza no x=5
    
    config = _criar_config({"D1": drone1}, {"Muro": parede})
    
    simulador = SimuladorDrones(config)
    interacoes, resultado = simulador.executar()
    
    assert resultado["D1"]["colidiu"] is True
    assert resultado["D1"]["entregou"] is False
    assert "bateu_parede(Muro)" in interacoes[list(interacoes.keys())[-1]]["D1"]["status"]
