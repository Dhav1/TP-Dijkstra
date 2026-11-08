"""
Desenho do grafo com matplotlib.

O networkx é usado SOMENTE para posicionar e desenhar os vértices.
O cálculo da rota é feito pelo nosso Dijkstra em grafo.py.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # desenha em memória, sem abrir janela
import matplotlib.pyplot as plt
import networkx as nx

# Verde das placas de rodovia brasileiras para destacar a rota
COR_ROTA = "#00703C"
COR_ESTRADA = "#9AA3AD"
COR_CIDADE = "#FFFFFF"
COR_BORDA = "#2F3B47"
COR_TEXTO = "#1F2933"


def posicionar(g: nx.Graph) -> dict:
    """
    Calcula a posição de cada cidade no desenho.
    Cada parte desconectada do grafo é posicionada separadamente e colocada
    lado a lado, para que cidades isoladas não fiquem perdidas num canto.
    """
    componentes = sorted(nx.connected_components(g), key=len, reverse=True)
    maior = len(componentes[0])
    pos, x_atual = {}, 0.0
    for comp in componentes:
        sub = g.subgraph(comp)
        escala = (len(comp) / maior) ** 0.5  # partes menores ocupam menos espaço
        # seed fixa: o desenho fica igual entre uma consulta e outra
        local = nx.spring_layout(sub, seed=7, scale=escala, iterations=300) if len(comp) > 1 \
            else {next(iter(comp)): (0.0, 0.0)}
        for n, (x, y) in local.items():
            pos[n] = (x + x_atual + escala, y)
        x_atual += 2 * escala + 0.6
    return pos


def desenhar_grafo(cidades: list[dict], estradas: list[dict], caminho: list[int] | None = None):
    g = nx.Graph()
    for c in cidades:
        g.add_node(c["id"], nome=c["nome"])
    for e in estradas:
        g.add_edge(e["id_a"], e["id_b"], km=e["distancia"])

    fig, ax = plt.subplots(figsize=(9, 6), dpi=110)
    fig.patch.set_alpha(0)
    ax.set_axis_off()

    if not cidades:
        ax.text(0.5, 0.5, "Nenhuma cidade cadastrada", ha="center", va="center", color=COR_ESTRADA)
        return fig

    pos = posicionar(g)

    arestas_rota = set()
    if caminho and len(caminho) > 1:
        arestas_rota = {frozenset(par) for par in zip(caminho, caminho[1:])}

    normais = [(a, b) for a, b in g.edges if frozenset((a, b)) not in arestas_rota]
    da_rota = [(a, b) for a, b in g.edges if frozenset((a, b)) in arestas_rota]

    nx.draw_networkx_edges(g, pos, edgelist=normais, ax=ax, width=1.6, edge_color=COR_ESTRADA)
    nx.draw_networkx_edges(g, pos, edgelist=da_rota, ax=ax, width=5, edge_color=COR_ROTA)

    nx.draw_networkx_edge_labels(
        g, pos, ax=ax,
        edge_labels={(a, b): f"{d['km']} km" for a, b, d in g.edges(data=True)},
        font_size=8, font_color=COR_TEXTO,
        bbox={"boxstyle": "round,pad=0.2", "fc": "white", "ec": "none", "alpha": 0.9},
    )

    na_rota = set(caminho or [])
    nx.draw_networkx_nodes(
        g, pos, ax=ax, node_size=520,
        node_color=[COR_ROTA if n in na_rota else COR_CIDADE for n in g.nodes],
        edgecolors=COR_BORDA, linewidths=1.5,
    )
    # número da cidade dentro do círculo e nome logo abaixo
    for n, (x, y) in pos.items():
        ax.text(x, y, str(n), ha="center", va="center", fontsize=8, fontweight="bold",
                color="white" if n in na_rota else COR_BORDA)
        ax.annotate(g.nodes[n]["nome"], (x, y), xytext=(0, -15), textcoords="offset points",
                    ha="center", va="top", fontsize=9, color=COR_TEXTO,
                    bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": COR_BORDA,
                          "lw": 0.6, "alpha": 0.95})

    ax.margins(0.12)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    return fig
