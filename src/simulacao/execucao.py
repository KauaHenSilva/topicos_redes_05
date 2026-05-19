"""Fluxo compartilhado para executar e persistir a simulacao."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeAlias, TypedDict

from .configuracao import carregar_configuracao, preparar_configuracao_simulacao
from .simulador import SimuladorDrones


class EstadoDroneInteracao(TypedDict):
    posicao_atual: list[float]
    status: str


class ResultadoFinalSimulacao(TypedDict, total=False):
    qtd_interacoes: int
    tempo_total: float
    quantidade_bateu: int
    quantidade_ok: int
    quantidade_nao_concluiu: int
    taxa_sucesso: str
    taxa_fracasso: str
    taxa_colisao: str
    tempo_medio_para_chegada: float
    distancia_media_percorrida: float
    distancia_total_percorrida: float
    tempos_interacoes: dict[str, float]
    eventos_interacoes: dict[str, list[str]]
    avisos_configuracao: list[str]


InteracoesSimulacao: TypeAlias = dict[str, dict[str, EstadoDroneInteracao]]


@dataclass(frozen=True)
class ExecucaoSimulacao:
    interacoes: InteracoesSimulacao
    resultado_final: ResultadoFinalSimulacao


def carregar_configuracao_entrada(caminho: str | Path) -> dict[str, Any]:
    """Carrega a configuracao aceita pelo CLI.

    O arquivo pode ser o JSON da simulacao diretamente ou um JSON pequeno com
    a chave ``arquivo_configuracao`` apontando para outro arquivo.
    """

    arquivo = Path(caminho)
    dados = carregar_configuracao(arquivo)
    caminho_configuracao = dados.get("arquivo_configuracao")
    if not caminho_configuracao:
        return dados

    arquivo_configuracao = Path(str(caminho_configuracao))
    if not arquivo_configuracao.is_absolute():
        candidato_relativo = arquivo.parent / arquivo_configuracao
        if candidato_relativo.exists():
            arquivo_configuracao = candidato_relativo

    return carregar_configuracao(arquivo_configuracao)


def executar_simulacao(
    configuracao_json: dict[str, Any],
    *,
    max_iteracoes: int = 10000,
) -> ExecucaoSimulacao:
    """Executa o motor da simulacao a partir de uma configuracao JSON."""

    configuracao = preparar_configuracao_simulacao(configuracao_json)
    simulador = SimuladorDrones(configuracao, max_iteracoes=max_iteracoes)
    interacoes, resultado_final = simulador.executar()
    return ExecucaoSimulacao(
        interacoes=interacoes,
        resultado_final=resultado_final,
    )


def executar_simulacao_de_arquivo(
    caminho: str | Path,
    *,
    max_iteracoes: int = 10000,
) -> ExecucaoSimulacao:
    """Executa a simulacao lendo a configuracao de um arquivo JSON."""

    return executar_simulacao(
        carregar_configuracao_entrada(caminho),
        max_iteracoes=max_iteracoes,
    )


def salvar_resultado(
    diretorio_saida: str | Path,
    interacoes: InteracoesSimulacao,
    resultado_final: ResultadoFinalSimulacao,
) -> list[Path]:
    """Salva cada interacao e o resumo final em arquivos JSON."""

    diretorio = Path(diretorio_saida)
    diretorio.mkdir(parents=True, exist_ok=True)

    arquivos: list[Path] = []
    tempos = resultado_final["tempos_interacoes"]
    eventos = resultado_final["eventos_interacoes"]

    for nome_interacao, drones in interacoes.items():
        eventos_interacao = eventos.get(nome_interacao)
        arquivo_interacao = diretorio / f"{nome_interacao}.json"
        with arquivo_interacao.open("w", encoding="utf-8") as fp:
            json.dump(
                {
                    "nome": nome_interacao,
                    "tempo": tempos.get(nome_interacao, 0.0),
                    "eventos": eventos_interacao if eventos_interacao is not None else [],
                    "drones": drones,
                },
                fp,
                ensure_ascii=False,
                indent=2,
            )
        arquivos.append(arquivo_interacao)

    arquivo_resultado = diretorio / "resultado_final.json"
    with arquivo_resultado.open("w", encoding="utf-8") as fp:
        json.dump(resultado_final, fp, ensure_ascii=False, indent=2)
    arquivos.append(arquivo_resultado)
    return arquivos
