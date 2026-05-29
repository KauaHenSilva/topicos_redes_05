"""Motor orientado a eventos da simulacao de drones."""

from __future__ import annotations

from itertools import combinations
from math import sqrt
from typing import Any

import random

from .configuracao import ConfiguracaoSimulacao
from .modelos import Drone, distancia

EPSILON = 1e-9


class SimuladorDrones:
    """Executa a simulacao e produz interacoes e metricas finais."""

    def __init__(
        self,
        configuracao: ConfiguracaoSimulacao,
        *,
        max_iteracoes: int = 10000,
    ) -> None:
        if max_iteracoes <= 0:
            raise ValueError("max_iteracoes deve ser maior que zero.")

        self.configuracao = configuracao
        self.max_iteracoes = int(max_iteracoes)
        self.avisos = list(configuracao.avisos)

        self.tamanho_ambiente = configuracao.tamanho_ambiente
        self.pontos = configuracao.pontos
        self.drones = configuracao.drones
        self.paredes = configuracao.paredes

    def executar(self) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
        """Executa a simulacao completa."""

        interacoes: dict[str, dict[str, Any]] = {}
        tempos_interacoes: dict[str, float] = {}
        eventos_interacoes: dict[str, list[str]] = {}
        tempo_atual = 0.0

        interacoes["interacao_0"] = self._estado_interacao()
        tempos_interacoes["interacao_0"] = tempo_atual
        eventos_interacoes["interacao_0"] = ["inicio da simulacao"]

        eventos_iniciais = self._detectar_colisoes(tempo_atual=tempo_atual)
        eventos_iniciais.extend(self._marcar_entregas(tempo_atual=tempo_atual))
        if eventos_iniciais:
            interacoes["interacao_0"] = self._estado_interacao()
            eventos_interacoes["interacao_0"] = eventos_iniciais

        iteracao = 0
        while iteracao < self.max_iteracoes and any(
            drone.ativo for drone in self.drones.values()
        ):
            delta_tempo = self._calcular_tempo_ate_proximo_evento()
            if delta_tempo is None:
                break

            iteracao += 1
            tempo_atual += delta_tempo

            for drone in self.drones.values():
                if drone.ativo:
                    self._mover_drone(drone, delta_tempo, tempo_atual)

            eventos = self._detectar_colisoes(tempo_atual=tempo_atual)
            eventos.extend(self._marcar_entregas(tempo_atual=tempo_atual))
            if not eventos:
                eventos.append("movimento")

            nome_interacao = f"interacao_{iteracao}"
            interacoes[nome_interacao] = self._estado_interacao()
            tempos_interacoes[nome_interacao] = self._arredondar(tempo_atual)
            eventos_interacoes[nome_interacao] = eventos

        if any(drone.ativo for drone in self.drones.values()):
            for drone in self.drones.values():
                if drone.ativo:
                    drone.nao_concluiu = True
                    drone.status = "nao concluiu"
                    drone.tempo_missao = tempo_atual

            nome_interacao = f"interacao_{iteracao}"
            interacoes[nome_interacao] = self._estado_interacao()
            tempos_interacoes[nome_interacao] = self._arredondar(tempo_atual)
            eventos_interacoes[nome_interacao] = ["limite de interacoes atingido"]

        return interacoes, self._resultado_final(
            iteracao,
            tempo_atual,
            tempos_interacoes,
            eventos_interacoes,
        )

    def _calcular_tempo_ate_proximo_evento(self) -> float | None:
        tempos: list[float] = []
        drones_ativos = [drone for drone in self.drones.values() if drone.ativo]

        for drone in drones_ativos:
            tempo_entrega = self._tempo_ate_entrega(drone)
            if tempo_entrega is not None:
                tempos.append(tempo_entrega)

        for drone_a, drone_b in combinations(drones_ativos, 2):
            tempo_colisao = self._tempo_ate_colisao(drone_a, drone_b)
            if tempo_colisao is not None:
                tempos.append(tempo_colisao)

        for drone in drones_ativos:
            for parede in self.paredes.values():
                tempo_parede = self._tempo_ate_colisao_parede(drone, parede)
                if tempo_parede is not None:
                    tempos.append(tempo_parede)

        if not tempos:
            return None
        return max(0.0, min(tempos))

    def _tempo_ate_entrega(self, drone: Drone) -> float | None:
        distancia_restante = drone.distancia_ate_destino()
        distancia_ate_area_destino = max(0.0, distancia_restante - drone.destino_raio)
        if distancia_ate_area_destino <= EPSILON:
            return 0.0
        return distancia_ate_area_destino / drone.velocidade

    def _tempo_ate_colisao(self, drone_a: Drone, drone_b: Drone) -> float | None:
        pos_a = drone_a.posicao_atual
        pos_b = drone_b.posicao_atual
        vel_a = self._vetor_velocidade(drone_a)
        vel_b = self._vetor_velocidade(drone_b)

        delta_pos = (pos_a[0] - pos_b[0], pos_a[1] - pos_b[1])
        delta_vel = (vel_a[0] - vel_b[0], vel_a[1] - vel_b[1])
        raio_colisao = drone_a.raio + drone_b.raio

        a = delta_vel[0] ** 2 + delta_vel[1] ** 2
        b = 2 * (delta_pos[0] * delta_vel[0] + delta_pos[1] * delta_vel[1])
        c = delta_pos[0] ** 2 + delta_pos[1] ** 2 - raio_colisao**2

        if c <= EPSILON:
            return 0.0
        if abs(a) <= EPSILON:
            return None

        discriminante = b**2 - 4 * a * c
        if discriminante < 0:
            return None

        raiz = sqrt(discriminante)
        tempo_entrada = (-b - raiz) / (2 * a)
        if tempo_entrada < -EPSILON:
            return None
        
        return max(0.0, tempo_entrada)

    def _tempo_ate_colisao_parede(self, drone: Drone, parede: Any) -> float | None:
        # Se ele já jogou os dados e sobreviveu, a simulação não se preocupa mais com o tempo de batida
        if parede.nome in drone.zonas_risco_superadas:
            return None

        pos_atual = drone.posicao_atual
        vel = self._vetor_velocidade(drone)
        if abs(vel[0]) < EPSILON and abs(vel[1]) < EPSILON:
            return None

        from .modelos import intersecao_segmentos, distancia

        intersecao = intersecao_segmentos(pos_atual, drone.destino, parede.p1, parede.p2)
        if intersecao is None:
            return None

        dist = max(0.0, distancia(pos_atual, intersecao) - drone.raio)
        if dist <= EPSILON:
            return 0.0

        return dist / drone.velocidade

    def _vetor_velocidade(self, drone: Drone) -> tuple[float, float]:
        distancia_restante = drone.distancia_ate_destino()
        if distancia_restante <= EPSILON:
            return (0.0, 0.0)
        origem_x, origem_y = drone.posicao_atual
        destino_x, destino_y = drone.destino
        return (
            (destino_x - origem_x) / distancia_restante * drone.velocidade,
            (destino_y - origem_y) / distancia_restante * drone.velocidade,
        )

    def _mover_drone(
        self, drone: Drone, delta_tempo: float, tempo_atual: float
    ) -> None:
        distancia_restante = drone.distancia_ate_destino()
        if distancia_restante <= EPSILON:
            drone.tempo_missao = tempo_atual
            return

        deslocamento = min(drone.velocidade * delta_tempo, distancia_restante)
        if deslocamento <= EPSILON:
            drone.tempo_missao = tempo_atual
            return

        origem_x, origem_y = drone.posicao_atual
        destino_x, destino_y = drone.destino
        fator = deslocamento / distancia_restante
        nova_posicao = (
            origem_x + (destino_x - origem_x) * fator,
            origem_y + (destino_y - origem_y) * fator,
        )
        drone.posicao_atual = nova_posicao
        drone.distancia_percorrida += deslocamento
        drone.status = "foi para"
        drone.tempo_missao = tempo_atual

    def _detectar_colisoes(self, *, tempo_atual: float) -> list[str]:
        envolvidos: dict[str, set[str]] = {}
        eventos: list[str] = []
        candidatos = [drone for drone in self.drones.values() if drone.ativo]

        for drone_a, drone_b in combinations(candidatos, 2):
            if distancia(drone_a.posicao_atual, drone_b.posicao_atual) <= (drone_a.raio + drone_b.raio) + EPSILON:
                envolvidos.setdefault(drone_a.nome, set()).add(drone_b.nome)
                envolvidos.setdefault(drone_b.nome, set()).add(drone_a.nome)
                eventos.append(f"colisao: {drone_a.nome} com {drone_b.nome}")

        for nome, outros in envolvidos.items():
            drone = self.drones[nome]
            drone.colidiu = True
            drone.entregou = False
            drone.status = f"bateu({', '.join(sorted(outros))})"
            drone.tempo_missao = tempo_atual

        from .modelos import distancia_ponto_segmento
        for drone in candidatos:
            if drone.colidiu:
                continue
            for parede in self.paredes.values():
                # Já sobreviveu a essa tempestade? Ignora e segue o voo.
                if parede.nome in drone.zonas_risco_superadas:
                    continue

                dist = distancia_ponto_segmento(drone.posicao_atual, parede.p1, parede.p2)
                
                # O drone tocou na parede/zona
                if dist <= drone.raio + EPSILON:
                    # Rola o dado do destino (0.0 até 1.0)
                    if random.random() <= parede.probabilidade:
                        drone.colidiu = True
                        drone.entregou = False
                        drone.status = f"bateu_zona({parede.nome})"
                        drone.tempo_missao = tempo_atual
                        eventos.append(f"acidente: {drone.nome} não sobreviveu à zona {parede.nome}")
                        break
                    else:
                        # Sobreviveu! Registra na lista de imunidade dele.
                        drone.zonas_risco_superadas.add(parede.nome)
                        eventos.append(f"sorte: {drone.nome} sobreviveu à zona {parede.nome}")

        return eventos

    def _marcar_entregas(self, *, tempo_atual: float) -> list[str]:
        eventos: list[str] = []
        for drone in self.drones.values():
            if not drone.ativo:
                continue
            
            # O drone encostou no raio da base de destino atual
            if drone.distancia_ate_destino() <= drone.destino_raio + EPSILON:
                is_last_waypoint = drone.indice_rota + 1 >= len(drone.rota)
                
                # --- LÓGICA DE ENTREGA DA MERCADORIA ---
                if not drone.pacote_entregue:
                    if (drone.base_entrega and drone.destino_nome == drone.base_entrega) or (not drone.base_entrega and is_last_waypoint):
                        drone.pacote_entregue = True
                        drone.tempo_entrega = tempo_atual
                        eventos.append(f"entrega: {drone.nome} entregou o pacote em {drone.destino_nome}")

                # --- A SUA SOLUÇÃO MESTRA AQUI ---
                # O drone pousou/chegou na base. Zeramos a imunidade dele para o próximo trecho do voo!
                drone.zonas_risco_superadas.clear()

                if not is_last_waypoint:
                    # Tem próximo ponto na rota (escala)
                    drone.indice_rota += 1
                    drone.status = f"indo para {drone.destino_nome}"
                    eventos.append(f"rota: {drone.nome} passou por um waypoint e vai para {drone.destino_nome}")
                else:
                    # Acabou a rota inteira (voltou pra casa)
                    drone.entregou = True
                    drone.status = "entregou" if not drone.base_entrega else "missao concluida"
                    drone.tempo_missao = tempo_atual
                    eventos.append(f"fim_missao: {drone.nome} concluiu a rota")
                    
        return eventos

    def _estado_interacao(self) -> dict[str, Any]:
        return {
            nome: {
                "posicao_atual": self._arredondar_posicao(drone.posicao_atual),
                "status": drone.status,
            }
            for nome, drone in self.drones.items()
        }

    def _resultado_final(
        self,
        iteracoes: int,
        tempo_total: float,
        tempos_interacoes: dict[str, float],
        eventos_interacoes: dict[str, list[str]],
    ) -> dict[str, Any]:
        total = len(self.drones)
        qtd_colidiu = sum(1 for drone in self.drones.values() if drone.colidiu)
        qtd_entregou = sum(1 for drone in self.drones.values() if drone.entregou)
        qtd_nao_concluiu = sum(1 for drone in self.drones.values() if drone.nao_concluiu)
        distancia_total = sum(drone.distancia_percorrida for drone in self.drones.values())
        
        # --- NOVAS MÉTRICAS ---
        qtd_pacotes_entregues = sum(1 for drone in self.drones.values() if drone.pacote_entregue)
        qtd_colisoes_com_carga = sum(1 for drone in self.drones.values() if drone.colidiu and not drone.pacote_entregue)
        qtd_colisoes_vazio = sum(1 for drone in self.drones.values() if drone.colidiu and drone.pacote_entregue)
        # Calcula o tempo médio usando a nova métrica (quando o pacote chegou ao cliente)
        tempos_entrega = [drone.tempo_entrega for drone in self.drones.values() if drone.pacote_entregue]

        resultado: dict[str, Any] = {
            "qtd_interacoes": iteracoes,
            "tempo_total": self._arredondar(tempo_total),
            "quantidade_bateu": qtd_colidiu, # Retrocompatível
            "quantidade_ok": qtd_entregou, # Retrocompatível
            "quantidade_nao_concluiu": qtd_nao_concluiu,
            "pacotes_entregues": qtd_pacotes_entregues,       # NOVA
            "colisoes_com_carga": qtd_colisoes_com_carga,     # NOVA
            "colisoes_vazio": qtd_colisoes_vazio,             # NOVA
            "_taxa_sucesso": (qtd_entregou / total) if total else 0.0,
            "_taxa_fracasso": ((qtd_colidiu + qtd_nao_concluiu) / total) if total else 0.0,
            "_taxa_colisao": (qtd_colidiu / total) if total else 0.0,
            "tempo_medio_para_chegada": self._arredondar(sum(tempos_entrega) / len(tempos_entrega) if tempos_entrega else 0),
            "distancia_media_percorrida": self._arredondar(distancia_total / total),
            "distancia_total_percorrida": self._arredondar(distancia_total),
            "tempos_interacoes": tempos_interacoes,
            "eventos_interacoes": eventos_interacoes,
            "avisos_configuracao": self.avisos,
        }

        def fmt_pct(x: float) -> str:
            pct = x * 100
            if abs(pct - round(pct)) < 1e-9:
                return f"{int(round(pct))}%"
            return f"{round(pct,1)}%"

        resultado["taxa_sucesso"] = fmt_pct(resultado.pop("_taxa_sucesso"))
        resultado["taxa_fracasso"] = fmt_pct(resultado.pop("_taxa_fracasso"))
        resultado["taxa_colisao"] = fmt_pct(resultado.pop("_taxa_colisao"))

        for nome, drone in self.drones.items():
            resultado[nome] = {
                "colidiu": drone.colidiu,
                "entregou": drone.entregou,
                "pacote_entregue": drone.pacote_entregue, # NOVA
                "nao_concluiu": drone.nao_concluiu,
                "tempo_missao": self._arredondar(drone.tempo_missao),
                "tempo_entrega": self._arredondar(drone.tempo_entrega) if drone.pacote_entregue else 0.0, # NOVA
                "distancia_percorrida": self._arredondar(drone.distancia_percorrida),
            }

        return resultado

    def _arredondar_posicao(self, posicao: tuple[float, float]) -> list[float]:
        return [self._arredondar(posicao[0]), self._arredondar(posicao[1])]

    def _arredondar(self, valor: float) -> float:
        return round(float(valor), 4)
