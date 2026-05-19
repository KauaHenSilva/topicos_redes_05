"""Entrada simples para executar o nucleo da simulacao."""

from __future__ import annotations

import argparse
from pathlib import Path
from datetime import datetime

from src.simulacao import (
    executar_simulacao_de_arquivo,
    salvar_resultado,
)


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


def imprimir_progresso(
    interacoes: dict[str, dict[str, object]],
    resultado_final: dict[str, object],
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
    execucao = executar_simulacao_de_arquivo(
        args.config,
        max_iteracoes=args.max_iteracoes,
    )
    # criar subpasta com timestamp para resultados para evitar sobrescrever execucoes anteriores
    pasta_base = Path(args.saida)
    pasta_timestamp = pasta_base / datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivos_saida = salvar_resultado(
        pasta_timestamp,
        execucao.interacoes,
        execucao.resultado_final,
    )

    imprimir_progresso(execucao.interacoes, execucao.resultado_final)
    print(f"Arquivos salvos em: {pasta_timestamp}")
    print(f"Total de arquivos gerados: {len(arquivos_saida)}")


if __name__ == "__main__":
    main()
