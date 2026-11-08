# Sistema de Cálculo de Rotas entre Cidades

Trabalho prático de INF104 – Estrutura de Dados (UNIVIÇOSA).
Calcula a menor rota entre cidades usando um grafo ponderado e o algoritmo de Dijkstra,
com interface gráfica no navegador.

**Tecnologias:** Python, Streamlit (interface), SQLite (banco de dados), API do IBGE (opcional,
para importar nomes de municípios), matplotlib + networkx (apenas para desenhar o grafo).

---

## Como executar

1. Instale o Python 3.12 ou mais recente (python.org). No Windows, marque **“Add python.exe to PATH”**.
2. Abra esta pasta no VS Code (**File > Open Folder**) e abra o terminal com **Ctrl+'**.
3. Crie e ative o ambiente virtual:
   ```
   python -m venv .venv
   .venv\Scripts\activate          (Windows)
   source .venv/bin/activate       (Mac/Linux)
   ```
   Se o PowerShell bloquear, rode antes: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
4. Instale as bibliotecas:
   ```
   pip install -r requirements.txt
   ```
5. Abra a interface:
   ```
   streamlit run app.py
   ```
   O navegador abre em `http://localhost:8501`. Para encerrar, use o botão
   **Encerrar programa** ou **Ctrl+C** no terminal.

Para rodar os 10 testes obrigatórios automaticamente: `python testes.py`

---

## Estrutura dos arquivos

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Interface gráfica (abas, formulários, botões, resultados) |
| `grafo.py` | Lista de adjacência e algoritmo de Dijkstra |
| `banco.py` | Banco SQLite: cadastro, remoção, consultas e todas as validações |
| `dados_iniciais.py` | 9 cidades e 14 estradas carregadas na primeira execução |
| `visualizacao.py` | Desenho do grafo com a rota destacada |
| `ibge.py` | Busca de municípios na API pública do IBGE |
| `testes.py` | Executa os 10 testes obrigatórios num banco temporário |
| `rotas.db` | Banco de dados (criado automaticamente) |

Não há separação “backend/frontend” com requisições HTTP: o `app.py` importa e chama
diretamente as funções de `banco.py` e `grafo.py`.

---

## Modelagem

**Vértices** são as cidades (`id` único + `nome`) e **arestas** são as estradas, com peso igual
à distância em km. As estradas são não direcionadas (valem nos dois sentidos).

**No banco (SQLite):**
- `cidades(id, nome, codigo_ibge)`: o `id` é gerado automaticamente e nunca é reaproveitado.
- `estradas(cidade_a, cidade_b, distancia)`: guardamos sempre o menor id em `cidade_a`, então
  “Viçosa–Coimbra” e “Coimbra–Viçosa” são a mesma linha. A chave primária `(cidade_a, cidade_b)`
  impede estradas duplicadas e `ON DELETE CASCADE` apaga as estradas de uma cidade removida.

**Em memória (para o Dijkstra):** uma lista de adjacência em dicionário,
`grafo[id] = [(id_vizinha, km), ...]`. O grafo é remontado a partir do banco a cada consulta,
por isso remoções aparecem imediatamente nas rotas.

---

## Como o Dijkstra funciona (grafo.py)

1. Todas as cidades começam com distância **∞**, menos a origem, que começa com **0**.
2. Uma **fila de prioridade** (`heapq`) entrega sempre a cidade não visitada com menor distância.
3. Essa cidade é **fechada**: como não há distâncias negativas, nenhum caminho futuro chega
   nela por menos.
4. Para cada vizinha, testa-se se passar pela cidade atual dá uma distância menor
   (**relaxamento**). Se der, atualiza a distância e anota quem veio antes (`anterior`).
5. Repete até fechar o destino ou a fila acabar. Se o destino continuar com ∞, **não existe rota**.
6. O caminho é reconstruído do destino para a origem seguindo `anterior`, e depois invertido.

Se um caminho diferente chega a uma cidade com **exatamente a mesma distância**, o sistema
mantém o primeiro e marca que há empate; a interface avisa que existe outra rota mínima.

A aba **Calcular rota** tem o expander **“Passo a passo do Dijkstra”**, que mostra cada
iteração (cidade fechada e distâncias melhoradas). Use-o na apresentação.

Complexidade: O((V + E) log V), com V cidades e E estradas.

---

## Dados iniciais (distâncias fictícias)

| Estrada | km | | Estrada | km |
|---|---|---|---|---|
| Viçosa – Coimbra | 25 | | Viçosa – Paula Cândido | 30 |
| Coimbra – Ervália | 25 | | Paula Cândido – Coimbra | 20 |
| Viçosa – Ervália | 60 | | Paula Cândido – Ervália | 35 |
| Viçosa – Teixeiras | 20 | | Cajuri – Paula Cândido | 40 |
| Teixeiras – São Miguel do Anta | 30 | | Coimbra – Teixeiras | 35 |
| Viçosa – Cajuri | 25 | | Teixeiras – Cajuri | 15 |
| Cajuri – São Miguel do Anta | 25 | | Porto Firme – Presidente Bernardes | 18 |

Situações exigidas no item 5 e onde aparecem:

| Situação | Exemplo |
|---|---|
| Ligação direta | Viçosa → Teixeiras: 20 km direto |
| Rota por cidades intermediárias | Viçosa → Ervália: direta tem 60 km, mas por Coimbra são 50 km |
| Duas rotas com a mesma distância | Viçosa → São Miguel do Anta: por Teixeiras ou por Cajuri, 50 km |
| Não existe rota | Porto Firme e Presidente Bernardes só se ligam entre si |
| Remover estrada muda a rota | Sem Coimbra–Ervália, Viçosa → Ervália passa a 60 km (direta) |
| Remover cidade muda as possibilidades | Sem Teixeiras, Viçosa → São Miguel do Anta só tem o caminho por Cajuri |

---

## Roteiro de demonstração dos 10 testes

Comece clicando em **Restaurar dados iniciais** na barra lateral.

| Teste | Onde | O que fazer | Resultado esperado |
|---|---|---|---|
| 1 | Calcular rota | Viçosa → Viçosa | Distância 0 km |
| 2 | Calcular rota | Viçosa → Teixeiras | Viçosa → Teixeiras, 20 km |
| 3 | Calcular rota | Viçosa → Ervália | Viçosa → Coimbra → Ervália, 50 km |
| 4 | Calcular rota | Viçosa → São Miguel do Anta | 50 km + aviso de rota empatada |
| 5 | Calcular rota | Viçosa → Porto Firme | “Não existe rota disponível” |
| 6 | Estradas → Calcular rota | Remover Coimbra–Ervália; depois Viçosa → Ervália | Viçosa → Ervália, 60 km |
| 7 | Cidades → Calcular rota | Remover Teixeiras; depois Viçosa → São Miguel do Anta | 4 estradas removidas; rota por Cajuri, 50 km, sem empate |
| 8 | Calcular rota | Viçosa → Belo Horizonte | “A cidade “Belo Horizonte” não está cadastrada.” |
| 9 | Estradas | Cadastrar Viçosa – Porto Firme com −15 km | Cadastro rejeitado |
| 10 | Estradas | Cadastrar Coimbra – Viçosa com 30 km | “Já existe estrada entre Coimbra e Viçosa” |

Dica: depois de uma remoção, a última rota calculada é refeita sozinha com o grafo atualizado.

---

## Uso de inteligência artificial (modelo para o relatório – item 7)

> Preencham com o que realmente aconteceu no grupo.

- **Ferramenta:** Claude (Anthropic).
- **Etapas em que foi usada:** escolha da linguagem e das bibliotecas, geração da estrutura
  inicial do código (banco, grafo, interface e testes) e orientação para configurar o ambiente.
- **O que foi aproveitado e o que o grupo alterou:** _(descrever)_
- **Como o grupo verificou o código:** execução de `python testes.py`; demonstração manual dos
  10 testes na interface; acompanhamento do “Passo a passo do Dijkstra” e comparação com o
  cálculo feito à mão no papel; _(complementar)_.
