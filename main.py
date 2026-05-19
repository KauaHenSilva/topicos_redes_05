"""Entrada simples para executar o nucleo da simulacao."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import TypeAlias, TypedDict, cast

from src.simulacao import (
    SimuladorDrones,
    carregar_configuracao,
    preparar_configuracao_simulacao,
)


class EstadoDroneInteracao(TypedDict):
    posicao_atual: list[float]
    status: str


class ResultadoFinalSimulacao(TypedDict):
    tempos_interacoes: dict[str, float]
    eventos_interacoes: dict[str, list[str]]
    avisos_configuracao: list[str]


InteracoesSimulacao: TypeAlias = dict[str, dict[str, EstadoDroneInteracao]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulador de drones em ambiente 2D.")
    parser.add_argument(
        "--config",
        default="utils/variaveis.json",
        help="Caminho do JSON de configuracao da simulacao.",
    )
    parser.add_argument(
        "--max-iteracoes",
        type=int,
        default=10000,
        help="Limite de eventos antes de marcar drones como nao concluidos.",
    )
    parser.add_argument(
        "--saida",
        default="saida",
        help="Diretorio que recebera os arquivos JSON da simulacao.",
    )
    return parser.parse_args()


def salvar_resultado(
    diretorio_saida: str | Path,
    interacoes: InteracoesSimulacao,
    resultado_final: ResultadoFinalSimulacao,
) -> list[Path]:
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
        json.dump(
            resultado_final,
            fp,
            ensure_ascii=False,
            indent=2,
        )
    arquivos.append(arquivo_resultado)
    return arquivos


def imprimir_progresso(
    interacoes: InteracoesSimulacao,
    resultado_final: ResultadoFinalSimulacao,
) -> None:
    tempos = resultado_final["tempos_interacoes"]
    eventos = resultado_final["eventos_interacoes"]

    for aviso in resultado_final["avisos_configuracao"]:
        print(f"Aviso: {aviso}")

    print("Progresso da simulacao:")
    for nome_interacao, drones in interacoes.items():
        tempo = tempos.get(nome_interacao, 0.0)
        eventos_interacao = eventos.get(nome_interacao)
        eventos_texto = ", ".join(eventos_interacao) if eventos_interacao else ""
        estados: list[str] = []
        for nome_drone, dados in drones.items():
            estados.append(f"{nome_drone}:{dados['status']}")

        print(
            f"- {nome_interacao} | t={tempo} | "
            f"{eventos_texto} | " + ", ".join(estados)
        )


def main() -> None:
    args = parse_args()
    configuracao_execucao = carregar_configuracao(args.config)
    caminho_configuracao = cast(
        str | Path,
        configuracao_execucao.get("arquivo_configuracao", "utils/variaveis.json"),
    )
    configuracao = preparar_configuracao_simulacao(
        carregar_configuracao(caminho_configuracao)
    )
    simulador = SimuladorDrones(
        configuracao,
        max_iteracoes=args.max_iteracoes,
    )
    interacoes_raw, resultado_final_raw = simulador.executar()
    interacoes = cast(InteracoesSimulacao, interacoes_raw)
    resultado_final = cast(ResultadoFinalSimulacao, resultado_final_raw)
    arquivos_saida = salvar_resultado(args.saida, interacoes, resultado_final)

    imprimir_progresso(interacoes, resultado_final)
    print(f"Arquivos salvos em: {Path(args.saida)}")
    print(f"Total de arquivos gerados: {len(arquivos_saida)}")


if __name__ == "__main__":
    main()
