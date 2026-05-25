import pytest
import os
from pathlib import Path
from src.simulacao.execucao import executar_simulacao_de_arquivo

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"

def test_cenario_patrulha_sucesso():
    caminho = CONFIG_DIR / "cenario_patrulha.json"
    if not caminho.exists():
        pytest.skip("Cenário patrulha não encontrado.")
    
    execucao = executar_simulacao_de_arquivo(str(caminho), max_iteracoes=50000)
    resultados = execucao.resultado_final
    
    assert resultados["quantidade_bateu"] >= 0
    assert "Drone 1" in resultados
    assert "Drone 4" in resultados


def test_cenario_engarrafamento_colisoes():
    caminho = CONFIG_DIR / "cenario_engarrafamento.json"
    if not caminho.exists():
        pytest.skip("Cenário engarrafamento não encontrado.")
    
    execucao = executar_simulacao_de_arquivo(str(caminho), max_iteracoes=10000)
    resultados = execucao.resultado_final
    
    assert resultados["quantidade_bateu"] > 0
    assert "Drone A" in resultados
    assert "Drone F" in resultados


def test_cenario_cruzamento():
    caminho = CONFIG_DIR / "cenario_cruzamento.json"
    if not caminho.exists():
        pytest.skip("Cenário cruzamento não encontrado.")
    
    execucao = executar_simulacao_de_arquivo(str(caminho), max_iteracoes=10000)
    resultados = execucao.resultado_final
    
    assert len(resultados["tempos_interacoes"]) > 1
    assert "Drone N-S" in resultados
