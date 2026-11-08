"""
Conjunto inicial de dados (item 5 do enunciado).

As distâncias são FICTÍCIAS (permitido pelo enunciado), escolhidas de propósito
para que cada situação exigida apareça no grafo:

  1. Ligação direta é a melhor rota ........ Viçosa -> Teixeiras = 20 km (direto)
  2. Melhor rota passa por intermediárias ... Viçosa -> Ervália
                                               direto = 60 km
                                               Viçosa -> Coimbra -> Ervália = 50 km  (melhor)
  3. Duas rotas com a mesma distância ....... Viçosa -> São Miguel do Anta
                                               Viçosa -> Teixeiras -> São Miguel do Anta = 50 km
                                               Viçosa -> Cajuri -> São Miguel do Anta    = 50 km
  4. Não existe rota ........................ Porto Firme e Presidente Bernardes só se
                                               ligam entre si (componente isolada do resto)
  5. Remover estrada altera a rota .......... remover Coimbra–Ervália faz Viçosa -> Ervália
                                               passar a ser a estrada direta (60 km)
  6. Remover cidade altera possibilidades ... remover Teixeiras apaga 4 estradas e acaba com o
                                               empate Viçosa -> São Miguel do Anta (sobra só o
                                               caminho por Cajuri, 50 km)

Total: 9 cidades e 14 estradas (o mínimo exigido é 8 e 12).
"""

CIDADES = [
    "Viçosa",
    "Coimbra",
    "Ervália",
    "Teixeiras",
    "Cajuri",
    "Paula Cândido",
    "São Miguel do Anta",
    "Porto Firme",
    "Presidente Bernardes",
]

# (cidade A, cidade B, distância em km) — as estradas valem nos dois sentidos
ESTRADAS = [
    ("Viçosa", "Coimbra", 25),
    ("Coimbra", "Ervália", 25),
    ("Viçosa", "Ervália", 60),
    ("Viçosa", "Teixeiras", 20),
    ("Teixeiras", "São Miguel do Anta", 30),
    ("Viçosa", "Cajuri", 25),
    ("Cajuri", "São Miguel do Anta", 25),
    ("Teixeiras", "Cajuri", 15),
    ("Viçosa", "Paula Cândido", 30),
    ("Paula Cândido", "Coimbra", 20),
    ("Paula Cândido", "Ervália", 35),
    ("Cajuri", "Paula Cândido", 40),
    ("Coimbra", "Teixeiras", 35),
    ("Porto Firme", "Presidente Bernardes", 18),
]
