"""
Camada de dados: guarda cidades e estradas num banco SQLite (arquivo rotas.db).

Toda regra de validação do enunciado fica aqui:
  - cidade precisa existir (teste 8)
  - distância precisa ser um inteiro maior que zero (teste 9)
  - a mesma estrada não pode ser cadastrada duas vezes, em nenhum sentido (teste 10)
  - remover uma cidade apaga as estradas dela (item 4.7)

Quando algo é inválido, as funções lançam ErroValidacao com uma mensagem
pronta para mostrar ao usuário.
"""

from __future__ import annotations

import sqlite3
import unicodedata
from contextlib import contextmanager
from pathlib import Path

import dados_iniciais

# Arquivo do banco, na mesma pasta deste código. Os testes trocam esse caminho.
CAMINHO_BANCO = Path(__file__).with_name("rotas.db")


class ErroValidacao(Exception):
    """Erro de regra de negócio (cidade inexistente, distância inválida etc.)."""


# ---------------------------------------------------------------------------
# Conexão e criação das tabelas
# ---------------------------------------------------------------------------

@contextmanager
def conexao():
    """Abre o banco, entrega a conexão e salva (commit) ao final se não houver erro."""
    con = sqlite3.connect(CAMINHO_BANCO)
    con.row_factory = sqlite3.Row          # permite acessar colunas pelo nome
    con.execute("PRAGMA foreign_keys = ON")  # sem isso o ON DELETE CASCADE não funciona
    try:
        yield con
        con.commit()
    finally:
        con.close()


ESQUEMA = """
CREATE TABLE IF NOT EXISTS cidades (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,   -- identificador único (nunca é reaproveitado)
    nome         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    codigo_ibge  INTEGER UNIQUE                       -- preenchido só se veio da API do IBGE
);

CREATE TABLE IF NOT EXISTS estradas (
    cidade_a   INTEGER NOT NULL REFERENCES cidades(id) ON DELETE CASCADE,
    cidade_b   INTEGER NOT NULL REFERENCES cidades(id) ON DELETE CASCADE,
    distancia  INTEGER NOT NULL CHECK (distancia > 0),
    PRIMARY KEY (cidade_a, cidade_b),
    CHECK (cidade_a < cidade_b)  -- guardamos sempre o menor id primeiro: A-B e B-A viram a mesma linha
);
"""


def inicializar_banco() -> None:
    """Cria as tabelas (se não existirem) e carrega os dados iniciais se o banco estiver vazio."""
    with conexao() as con:
        con.executescript(ESQUEMA)
        vazio = con.execute("SELECT COUNT(*) FROM cidades").fetchone()[0] == 0
    if vazio:
        carregar_dados_iniciais()


def carregar_dados_iniciais() -> None:
    for nome in dados_iniciais.CIDADES:
        cadastrar_cidade(nome)
    for nome_a, nome_b, km in dados_iniciais.ESTRADAS:
        cadastrar_estrada(nome_a, nome_b, km)


def restaurar_dados_iniciais() -> None:
    """Apaga tudo e volta ao conjunto inicial (útil antes da apresentação)."""
    with conexao() as con:
        con.execute("DELETE FROM estradas")
        con.execute("DELETE FROM cidades")
        # zera o contador de ids para as cidades voltarem a ser 1, 2, 3...
        con.execute("DELETE FROM sqlite_sequence WHERE name = 'cidades'")
    carregar_dados_iniciais()


# ---------------------------------------------------------------------------
# Cidades
# ---------------------------------------------------------------------------

def normalizar(texto: str) -> str:
    """'  São  Miguel ' -> 'sao miguel'. Usado para comparar nomes sem ligar para acento/maiúscula."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def listar_cidades() -> list[dict]:
    with conexao() as con:
        linhas = con.execute("SELECT id, nome, codigo_ibge FROM cidades ORDER BY id").fetchall()
    return [dict(l) for l in linhas]


def buscar_cidade(texto: str) -> dict:
    """
    Encontra uma cidade pelo id (ex.: '3') ou pelo nome (ex.: 'vicosa', 'Viçosa').
    Lança ErroValidacao se não existir (teste 8).
    """
    texto = (texto or "").strip()
    if not texto:
        raise ErroValidacao("Informe uma cidade (pelo nome ou pelo número de identificação).")

    for cidade in listar_cidades():
        if texto.isdigit() and cidade["id"] == int(texto):
            return cidade
        if normalizar(cidade["nome"]) == normalizar(texto):
            return cidade

    raise ErroValidacao(f"A cidade “{texto}” não está cadastrada.")


def cadastrar_cidade(nome: str, codigo_ibge: int | None = None) -> int:
    """Cadastra uma cidade e devolve o id gerado."""
    nome = " ".join((nome or "").split())
    if not nome:
        raise ErroValidacao("O nome da cidade não pode ficar em branco.")
    if nome.isdigit():
        raise ErroValidacao("O nome da cidade não pode ser só números.")

    for cidade in listar_cidades():
        if normalizar(cidade["nome"]) == normalizar(nome):
            raise ErroValidacao(f"“{cidade['nome']}” já está cadastrada (id {cidade['id']}).")
        if codigo_ibge is not None and cidade["codigo_ibge"] == codigo_ibge:
            raise ErroValidacao(f"Esse município do IBGE já está cadastrado como “{cidade['nome']}”.")

    with conexao() as con:
        cursor = con.execute(
            "INSERT INTO cidades (nome, codigo_ibge) VALUES (?, ?)", (nome, codigo_ibge)
        )
        return cursor.lastrowid


def remover_cidade(texto: str) -> tuple[str, int]:
    """Remove a cidade e todas as estradas ligadas a ela. Devolve (nome, nº de estradas removidas)."""
    cidade = buscar_cidade(texto)
    with conexao() as con:
        qtd_estradas = con.execute(
            "SELECT COUNT(*) FROM estradas WHERE cidade_a = ? OR cidade_b = ?",
            (cidade["id"], cidade["id"]),
        ).fetchone()[0]
        # O ON DELETE CASCADE apaga as estradas automaticamente
        con.execute("DELETE FROM cidades WHERE id = ?", (cidade["id"],))
    return cidade["nome"], qtd_estradas


# ---------------------------------------------------------------------------
# Estradas
# ---------------------------------------------------------------------------

def _ordenar(id_1: int, id_2: int) -> tuple[int, int]:
    """Garante que o menor id venha primeiro, para A-B e B-A serem a mesma estrada."""
    return (id_1, id_2) if id_1 < id_2 else (id_2, id_1)


def listar_estradas() -> list[dict]:
    with conexao() as con:
        linhas = con.execute(
            """
            SELECT e.cidade_a AS id_a, ca.nome AS nome_a,
                   e.cidade_b AS id_b, cb.nome AS nome_b,
                   e.distancia
            FROM estradas e
            JOIN cidades ca ON ca.id = e.cidade_a
            JOIN cidades cb ON cb.id = e.cidade_b
            ORDER BY ca.nome, cb.nome
            """
        ).fetchall()
    return [dict(l) for l in linhas]


def validar_distancia(valor) -> int:
    """Aceita só números inteiros maiores que zero (teste 9)."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ErroValidacao("A distância precisa ser um número.")
    if numero < 0:
        raise ErroValidacao(f"Distância negativa ({numero:g} km) não é permitida.")
    if numero == 0:
        raise ErroValidacao("A distância entre duas cidades diferentes precisa ser maior que zero.")
    if not numero.is_integer():
        raise ErroValidacao("Informe a distância em quilômetros inteiros (ex.: 25).")
    return int(numero)


def cadastrar_estrada(texto_a: str, texto_b: str, distancia) -> tuple[str, str, int]:
    cidade_a = buscar_cidade(texto_a)
    cidade_b = buscar_cidade(texto_b)
    if cidade_a["id"] == cidade_b["id"]:
        raise ErroValidacao("Uma estrada precisa ligar duas cidades diferentes.")
    km = validar_distancia(distancia)

    id_a, id_b = _ordenar(cidade_a["id"], cidade_b["id"])
    with conexao() as con:
        existente = con.execute(
            "SELECT distancia FROM estradas WHERE cidade_a = ? AND cidade_b = ?", (id_a, id_b)
        ).fetchone()
        if existente:  # teste 10
            raise ErroValidacao(
                f"Já existe estrada entre {cidade_a['nome']} e {cidade_b['nome']} "
                f"({existente['distancia']} km). Remova-a antes se quiser trocar a distância."
            )
        con.execute(
            "INSERT INTO estradas (cidade_a, cidade_b, distancia) VALUES (?, ?, ?)",
            (id_a, id_b, km),
        )
    return cidade_a["nome"], cidade_b["nome"], km


def remover_estrada(texto_a: str, texto_b: str) -> tuple[str, str, int]:
    cidade_a = buscar_cidade(texto_a)
    cidade_b = buscar_cidade(texto_b)
    id_a, id_b = _ordenar(cidade_a["id"], cidade_b["id"])
    with conexao() as con:
        existente = con.execute(
            "SELECT distancia FROM estradas WHERE cidade_a = ? AND cidade_b = ?", (id_a, id_b)
        ).fetchone()
        if not existente:  # item 4.6: informar quando a estrada não existir
            raise ErroValidacao(
                f"Não existe estrada cadastrada entre {cidade_a['nome']} e {cidade_b['nome']}."
            )
        con.execute("DELETE FROM estradas WHERE cidade_a = ? AND cidade_b = ?", (id_a, id_b))
    return cidade_a["nome"], cidade_b["nome"], existente["distancia"]
