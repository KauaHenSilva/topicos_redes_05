import json
from src.simulacao.execucao import (
    carregar_configuracao_entrada,
    executar_simulacao,
    executar_simulacao_de_arquivo,
    salvar_resultado
)


def test_carregar_configuracao_entrada_direto(tmp_path):
    config = {"tamanho_ambiente": [10, 10]}
    arquivo = tmp_path / "config.json"
    with open(arquivo, "w") as f:
        json.dump(config, f)
    
    resultado = carregar_configuracao_entrada(arquivo)
    assert resultado == config


def test_carregar_configuracao_entrada_indireto(tmp_path):
    config = {"tamanho_ambiente": [10, 10]}
    arquivo_real = tmp_path / "real.json"
    with open(arquivo_real, "w") as f:
        json.dump(config, f)

    arquivo_ptr = tmp_path / "ptr.json"
    with open(arquivo_ptr, "w") as f:
        json.dump({"arquivo_configuracao": "real.json"}, f)
    
    resultado = carregar_configuracao_entrada(arquivo_ptr)
    assert resultado == config


def test_executar_simulacao():
    config_raw = {
        "tamanho_ambiente": [10, 10],
        "Pontos": {"A": {"x": 0, "y": 0}},
        "drones": {"d1": {"posicao_inicial": "A", "posicao_destino": "A"}}
    }
    execucao = executar_simulacao(config_raw, max_iteracoes=10)
    assert execucao.resultado_final["taxa_sucesso"] == "100%"
    assert execucao.resultado_final["quantidade_ok"] == 1


def test_executar_simulacao_de_arquivo(tmp_path):
    config_raw = {
        "tamanho_ambiente": [10, 10],
        "Pontos": {"A": {"x": 0, "y": 0}},
        "drones": {"d1": {"posicao_inicial": "A", "posicao_destino": "A"}}
    }
    arquivo = tmp_path / "config.json"
    with open(arquivo, "w") as f:
        json.dump(config_raw, f)

    execucao = executar_simulacao_de_arquivo(arquivo)
    assert execucao.resultado_final["quantidade_ok"] == 1


def test_salvar_resultado(tmp_path):
    interacoes = {
        "0": {"d1": {"posicao_atual": [0, 0], "status": "entregou"}}
    }
    resultado = {
        "tempos_interacoes": {"0": 1.0},
        "eventos_interacoes": {"0": ["evento"]}
    }
    
    arquivos = salvar_resultado(tmp_path, interacoes, resultado)
    assert len(arquivos) == 2 # 0.json e resultado_final.json
    
    with open(tmp_path / "0.json") as f:
        dados = json.load(f)
        assert dados["tempo"] == 1.0
        assert dados["drones"]["d1"]["status"] == "entregou"
