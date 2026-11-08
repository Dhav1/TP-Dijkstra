"""
Roda os 10 testes obrigatórios (item 6) num banco temporário e mostra o resultado.

Para executar:  python testes.py
(O banco de verdade, rotas.db, não é alterado.)
"""

import tempfile
from pathlib import Path

import banco
import grafo


def rota(origem: str, destino: str) -> grafo.ResultadoRota:
    """Atalho: monta o grafo com o estado atual do banco e roda o Dijkstra."""
    cidades, estradas = banco.listar_cidades(), banco.listar_estradas()
    g = grafo.montar_grafo(cidades, estradas)
    o, d = banco.buscar_cidade(origem), banco.buscar_cidade(destino)
    return grafo.menor_rota(g, o["id"], d["id"])


def nomes(resultado: grafo.ResultadoRota) -> str:
    if not resultado.existe_rota:
        return "sem rota"
    nome_de = {c["id"]: c["nome"] for c in banco.listar_cidades()}
    return " → ".join(nome_de[i] for i in resultado.caminho) + f" | {resultado.distancia} km"


def espera_erro(funcao, *args) -> str:
    try:
        funcao(*args)
    except banco.ErroValidacao as erro:
        return str(erro)
    raise AssertionError("era esperado um erro, mas a operação foi aceita")


def executar():
    resultados = []

    def teste(numero, descricao, verificacao):
        try:
            detalhe = verificacao()
            resultados.append(True)
            print(f"[OK]    Teste {numero:2d} – {descricao}\n        {detalhe}")
        except AssertionError as erro:
            resultados.append(False)
            print(f"[FALHOU] Teste {numero:2d} – {descricao}\n        {erro}")

    def t1():
        r = rota("Viçosa", "Viçosa")
        assert r.distancia == 0 and r.caminho == [r.origem], nomes(r)
        return nomes(r)

    def t2():
        r = rota("Viçosa", "Teixeiras")  # estrada direta de 20 km é a melhor
        assert r.distancia == 20 and len(r.caminho) == 2, nomes(r)
        return nomes(r)

    def t3():
        r = rota("Viçosa", "Ervália")  # direta = 60 km, mas por Coimbra = 50 km
        assert r.distancia == 50 and len(r.caminho) == 3, nomes(r)
        return nomes(r) + "  (a estrada direta tem 60 km)"

    def t4():
        r = rota("Viçosa", "São Miguel do Anta")  # por Teixeiras ou por Cajuri: 50 km
        assert r.distancia == 50 and r.ha_empate, nomes(r)
        return nomes(r) + "  (empate detectado)"

    def t5():
        r = rota("Viçosa", "Porto Firme")
        assert not r.existe_rota, nomes(r)
        return "Viçosa → Porto Firme: não existe rota"

    def t6():
        antes = nomes(rota("Viçosa", "Ervália"))
        banco.remover_estrada("Coimbra", "Ervália")
        r = rota("Viçosa", "Ervália")
        assert r.distancia == 60, nomes(r)
        return f"antes: {antes}  |  depois de remover Coimbra–Ervália: {nomes(r)}"

    def t7():
        nome, qtd = banco.remover_cidade("Teixeiras")
        r = rota("Viçosa", "São Miguel do Anta")
        assert qtd == 4 and r.distancia == 50 and not r.ha_empate, nomes(r)
        msg = espera_erro(banco.buscar_cidade, "Teixeiras")
        return f"{nome} removida com {qtd} estradas; agora {nomes(r)} sem empate; busca: “{msg}”"

    def t8():
        msg = espera_erro(rota, "Viçosa", "Belo Horizonte")
        return f"mensagem: “{msg}”"

    def t9():
        msg = espera_erro(banco.cadastrar_estrada, "Viçosa", "Porto Firme", -15)
        return f"mensagem: “{msg}”"

    def t10():
        msg = espera_erro(banco.cadastrar_estrada, "Coimbra", "Viçosa", 99)  # sentido invertido
        return f"mensagem: “{msg}”"

    teste(1, "Origem e destino iguais", t1)
    teste(2, "Existe estrada direta", t2)
    teste(3, "Menor rota passa por cidades intermediárias", t3)
    teste(4, "Duas rotas com a mesma distância mínima", t4)
    teste(5, "Não existe conexão entre origem e destino", t5)
    teste(6, "Uma estrada é removida", t6)
    teste(7, "Uma cidade é removida", t7)
    teste(8, "Cidade informada não existe", t8)
    teste(9, "Distância informada é negativa", t9)
    teste(10, "Estrada cadastrada novamente", t10)

    print(f"\n{sum(resultados)} de {len(resultados)} testes passaram.")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as pasta:
        banco.CAMINHO_BANCO = Path(pasta) / "teste.db"
        banco.inicializar_banco()
        executar()
