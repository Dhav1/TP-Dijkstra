"""
Grafo ponderado + algoritmo de Dijkstra (implementado à mão, sem bibliotecas de grafos).

Representação: LISTA DE ADJACÊNCIA em um dicionário.
    grafo[id_da_cidade] = [(id_vizinha, distancia_km), ...]

Exemplo com as cidades 1=Viçosa, 2=Coimbra, 3=Ervália:
    {
        1: [(2, 25), (3, 60)],
        2: [(1, 25), (3, 25)],
        3: [(2, 25), (1, 60)],
    }
Como as estradas valem nos dois sentidos, cada estrada aparece duas vezes
(uma na lista de cada cidade).
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field


def montar_grafo(cidades: list[dict], estradas: list[dict]) -> dict[int, list[tuple[int, int]]]:
    """Cria a lista de adjacência a partir do que está no banco."""
    grafo = {cidade["id"]: [] for cidade in cidades}
    for estrada in estradas:
        a, b, km = estrada["id_a"], estrada["id_b"], estrada["distancia"]
        grafo[a].append((b, km))  # ida
        grafo[b].append((a, km))  # volta
    return grafo


@dataclass
class ResultadoRota:
    origem: int
    destino: int
    caminho: list[int] | None      # sequência de ids, ou None se não existe rota
    distancia: float               # math.inf se não existe rota
    ha_empate: bool = False        # existe outra rota com a mesma distância mínima?
    passos: list[dict] = field(default_factory=list)  # registro de cada iteração (para explicar)

    @property
    def existe_rota(self) -> bool:
        return self.caminho is not None


def dijkstra(grafo, origem: int, destino: int | None = None):
    """
    Calcula a menor distância da ORIGEM até as outras cidades.

    Ideia: sempre "fechar" a cidade ainda não visitada que tem a MENOR distância
    conhecida. Como todas as distâncias são positivas, nenhum caminho futuro
    consegue chegar nela por menos — então a distância dela já é a definitiva.

    Devolve:
      distancia[v] -> menor distância conhecida da origem até v
      anterior[v]  -> cidade que vem antes de v no melhor caminho (para reconstruir a rota)
      empate[v]    -> True se existe mais de um caminho mínimo até v
      passos       -> lista com o que aconteceu em cada iteração
    """
    distancia = {v: math.inf for v in grafo}  # no início, tudo é "infinito"
    anterior = {v: None for v in grafo}
    empate = {v: False for v in grafo}
    visitados = set()
    passos = []

    distancia[origem] = 0
    fila = [(0, origem)]  # fila de prioridade (heap): sempre sai a menor distância primeiro

    while fila:
        dist_atual, atual = heapq.heappop(fila)

        if atual in visitados:
            continue  # entrada antiga na fila; essa cidade já foi fechada com um valor menor
        visitados.add(atual)

        passo = {"cidade": atual, "distancia": dist_atual, "atualizacoes": []}
        passos.append(passo)

        if atual == destino:
            break  # já temos a distância definitiva do destino; podemos parar

        # "Relaxamento": tenta melhorar a distância de cada vizinho passando pela cidade atual
        for vizinha, km in grafo[atual]:
            if vizinha in visitados:
                continue
            nova_distancia = dist_atual + km

            if nova_distancia < distancia[vizinha]:
                # Encontramos um caminho melhor até a vizinha
                passo["atualizacoes"].append(
                    {"cidade": vizinha, "antes": distancia[vizinha], "depois": nova_distancia}
                )
                distancia[vizinha] = nova_distancia
                anterior[vizinha] = atual
                empate[vizinha] = empate[atual]  # herda empates do caminho até a atual
                heapq.heappush(fila, (nova_distancia, vizinha))

            elif nova_distancia == distancia[vizinha]:
                # Caminho diferente com a MESMA distância: existe empate (teste 4).
                # Mantemos o primeiro caminho encontrado e só marcamos o empate.
                empate[vizinha] = True

    return distancia, anterior, empate, passos


def reconstruir_caminho(anterior: dict, origem: int, destino: int) -> list[int]:
    """Volta do destino até a origem seguindo 'anterior' e depois inverte a lista."""
    caminho = []
    cidade = destino
    while cidade is not None:
        caminho.append(cidade)
        cidade = anterior[cidade]
    caminho.reverse()
    return caminho if caminho[0] == origem else []


def menor_rota(grafo, origem: int, destino: int) -> ResultadoRota:
    """Função usada pela interface: roda o Dijkstra e já devolve a rota pronta."""
    if origem == destino:  # teste 1
        return ResultadoRota(origem, destino, caminho=[origem], distancia=0)

    distancia, anterior, empate, passos = dijkstra(grafo, origem, destino)

    if distancia[destino] == math.inf:  # teste 5: destino nunca foi alcançado
        return ResultadoRota(origem, destino, caminho=None, distancia=math.inf, passos=passos)

    return ResultadoRota(
        origem,
        destino,
        caminho=reconstruir_caminho(anterior, origem, destino),
        distancia=distancia[destino],
        ha_empate=empate[destino],
        passos=passos,
    )
