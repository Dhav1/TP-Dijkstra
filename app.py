"""
Interface gráfica (Streamlit).

Para abrir:  streamlit run app.py

Como o Streamlit funciona: a cada clique, este arquivo inteiro é executado de novo,
de cima para baixo. Por isso a interface sempre mostra o que está no banco naquele
momento, e não é preciso "conectar" backend e frontend: aqui só chamamos as funções
de banco.py e grafo.py diretamente.
"""

import html
import os
import time

import matplotlib.pyplot as plt
import streamlit as st

import banco
import grafo
import ibge
from visualizacao import desenhar_grafo

st.set_page_config(page_title="Rotas entre cidades", page_icon="🛣️", layout="wide")

st.markdown(
    """
    <style>
    .placa {
        background: #00703C; color: #FFFFFF;
        border: 3px solid #FFFFFF; outline: 3px solid #00703C;
        border-radius: 10px; padding: 18px 24px; margin: 6px 3px 18px;
        font-family: "Helvetica Neue", Arial, sans-serif;
    }
    .placa .percurso { font-size: 1.35rem; font-weight: 700; line-height: 1.5; }
    .placa .total { font-size: 1rem; margin-top: 6px; opacity: .95; }
    </style>
    """,
    unsafe_allow_html=True,
)

banco.inicializar_banco()


# ---------------------------------------------------------------------------
# Barra lateral: ações gerais (tratadas primeiro, antes de desenhar as abas)
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("🛣️ Rotas entre cidades")
    st.caption("Menor caminho calculado com o algoritmo de Dijkstra.")
    resumo = st.container()  # preenchido no final, com os números já atualizados

    st.divider()
    if st.button("Restaurar dados iniciais", width="stretch",
                 help="Apaga tudo e volta às 9 cidades e 14 estradas originais."):
        banco.restaurar_dados_iniciais()
        st.session_state.pop("consulta", None)
        st.success("Dados iniciais restaurados.")

    if st.button("Encerrar programa", type="primary", width="stretch"):
        st.info("Programa encerrado. Pode fechar esta aba do navegador.")
        time.sleep(0.8)
        os._exit(0)  # item 4.8: encerra o servidor do Streamlit


st.title("Sistema de cálculo de rotas")
aba_rota, aba_cidades, aba_estradas, aba_lista = st.tabs(
    ["Calcular rota", "Cidades", "Estradas", "Cidades e conexões"]
)

# As abas de cadastro/remoção são processadas ANTES das abas de consulta,
# assim as consultas já enxergam o grafo atualizado na mesma execução.


# ---------------------------------------------------------------------------
# Aba: Cidades (4.1 cadastrar e 4.7 remover)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=24 * 3600, show_spinner="Buscando municípios no IBGE...")
def municipios_do_ibge(uf: str) -> list[dict]:
    return ibge.buscar_municipios(uf)


with aba_cidades:
    col_cadastro, col_ibge = st.columns(2, gap="large")

    with col_cadastro:
        st.subheader("Cadastrar cidade")
        with st.form("form_cidade", clear_on_submit=True):
            nome = st.text_input("Nome da cidade")
            if st.form_submit_button("Cadastrar cidade"):
                try:
                    novo_id = banco.cadastrar_cidade(nome)
                    st.success(f"Cidade “{nome.strip()}” cadastrada com o id {novo_id}.")
                except banco.ErroValidacao as erro:
                    st.error(str(erro))

    with col_ibge:
        st.subheader("Importar do IBGE")
        uf = st.selectbox("Estado", ibge.UFS, index=ibge.UFS.index("MG"))
        if st.button("Carregar municípios"):
            st.session_state["uf_ibge"] = uf

        if st.session_state.get("uf_ibge"):
            try:
                municipios = municipios_do_ibge(st.session_state["uf_ibge"])
            except ibge.ErroIBGE as erro:
                st.error(str(erro))
            else:
                nomes = {m["codigo"]: m["nome"] for m in municipios}
                codigo = st.selectbox(
                    f"Município ({st.session_state['uf_ibge']})",
                    options=list(nomes),
                    format_func=lambda c: nomes[c],
                    index=None,
                    placeholder="Digite para procurar",
                )
                if st.button("Cadastrar município", disabled=codigo is None):
                    try:
                        novo_id = banco.cadastrar_cidade(nomes[codigo], codigo_ibge=codigo)
                        st.success(f"“{nomes[codigo]}” cadastrada com o id {novo_id} "
                                   f"(código IBGE {codigo}).")
                    except banco.ErroValidacao as erro:
                        st.error(str(erro))

    st.divider()
    st.subheader("Remover cidade")
    st.caption("Remove a cidade e todas as estradas ligadas a ela.")
    with st.form("form_remover_cidade", clear_on_submit=True):
        alvo = st.text_input("Cidade (nome ou id)")
        if st.form_submit_button("Remover cidade"):
            try:
                nome_removido, qtd = banco.remover_cidade(alvo)
                st.success(f"{nome_removido} removida, junto com {qtd} estrada(s).")
            except banco.ErroValidacao as erro:
                st.error(str(erro))

    st.divider()
    st.subheader("Cidades cadastradas")
    cidades = banco.listar_cidades()
    if cidades:
        st.dataframe(
            [{"Id": c["id"], "Cidade": c["nome"], "Código IBGE": c["codigo_ibge"] or "—"}
             for c in cidades],
            hide_index=True, width="stretch",
        )
    else:
        st.info("Nenhuma cidade cadastrada. Use o formulário acima para começar.")


# ---------------------------------------------------------------------------
# Aba: Estradas (4.2 cadastrar e 4.6 remover)
# ---------------------------------------------------------------------------

with aba_estradas:
    col_cadastro, col_remocao = st.columns(2, gap="large")

    with col_cadastro:
        st.subheader("Cadastrar estrada")
        with st.form("form_estrada", clear_on_submit=True):
            cidade_a = st.text_input("Cidade A (nome ou id)")
            cidade_b = st.text_input("Cidade B (nome ou id)")
            # sem valor mínimo de propósito: a validação fica no banco.py (teste 9)
            km = st.number_input("Distância (km)", value=10, step=1)
            if st.form_submit_button("Cadastrar estrada"):
                try:
                    a, b, d = banco.cadastrar_estrada(cidade_a, cidade_b, km)
                    st.success(f"Estrada {a} – {b} ({d} km) cadastrada.")
                except banco.ErroValidacao as erro:
                    st.error(str(erro))

    with col_remocao:
        st.subheader("Remover estrada")
        with st.form("form_remover_estrada", clear_on_submit=True):
            cidade_a = st.text_input("Cidade A (nome ou id)", key="rem_a")
            cidade_b = st.text_input("Cidade B (nome ou id)", key="rem_b")
            if st.form_submit_button("Remover estrada"):
                try:
                    a, b, d = banco.remover_estrada(cidade_a, cidade_b)
                    st.success(f"Estrada {a} – {b} ({d} km) removida.")
                except banco.ErroValidacao as erro:
                    st.error(str(erro))

    st.divider()
    st.subheader("Estradas cadastradas")
    estradas = banco.listar_estradas()
    if estradas:
        st.dataframe(
            [{"Cidade A": e["nome_a"], "Cidade B": e["nome_b"], "Distância (km)": e["distancia"]}
             for e in estradas],
            hide_index=True, width="stretch",
        )
    else:
        st.info("Nenhuma estrada cadastrada.")


# A partir daqui o banco já está atualizado com o que foi feito nesta execução
cidades = banco.listar_cidades()
estradas = banco.listar_estradas()
nome_de = {c["id"]: c["nome"] for c in cidades}


# ---------------------------------------------------------------------------
# Aba: Calcular rota (4.4 menor rota e 4.5 existência de rota)
# ---------------------------------------------------------------------------

def formatar_km(valor) -> str:
    return f"{valor:g} km"


with aba_rota:
    st.caption("Digite o nome ou o id das cidades. A rota é recalculada sozinha "
               "sempre que uma estrada ou cidade é removida.")

    with st.form("form_rota"):
        col_o, col_d = st.columns(2)
        texto_origem = col_o.text_input("Origem", placeholder="Ex.: Viçosa")
        texto_destino = col_d.text_input("Destino", placeholder="Ex.: Ervália")
        if st.form_submit_button("Calcular rota", type="primary"):
            st.session_state["consulta"] = (texto_origem, texto_destino)

    with st.expander("Ver cidades disponíveis"):
        st.write(", ".join(f"{c['id']} – {c['nome']}" for c in cidades) or "Nenhuma.")

    resultado = None
    if "consulta" in st.session_state:
        texto_origem, texto_destino = st.session_state["consulta"]
        try:
            origem = banco.buscar_cidade(texto_origem)
            destino = banco.buscar_cidade(texto_destino)
        except banco.ErroValidacao as erro:  # teste 8
            st.error(str(erro))
        else:
            g = grafo.montar_grafo(cidades, estradas)
            resultado = grafo.menor_rota(g, origem["id"], destino["id"])

    if resultado and not resultado.existe_rota:  # teste 5
        st.warning(f"Não existe rota disponível entre {nome_de[resultado.origem]} "
                   f"e {nome_de[resultado.destino]}.")

    if resultado and resultado.existe_rota:
        nomes_caminho = [nome_de[i] for i in resultado.caminho]
        percurso = " → ".join(html.escape(n) for n in nomes_caminho)
        st.markdown(
            f'<div class="placa"><div class="percurso">{percurso}</div>'
            f'<div class="total">Distância total: {formatar_km(resultado.distancia)}</div></div>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Origem", nome_de[resultado.origem])
        m2.metric("Destino", nome_de[resultado.destino])
        m3.metric("Distância total", formatar_km(resultado.distancia))
        m4.metric("Cidades no caminho", len(resultado.caminho))

        if resultado.ha_empate:  # teste 4
            st.info("Existe pelo menos outra rota com a mesma distância mínima. "
                    "O sistema apresenta uma delas.")

        if len(resultado.caminho) > 1:
            km_estrada = {frozenset((e["id_a"], e["id_b"])): e["distancia"] for e in estradas}
            acumulado = 0
            trechos = []
            for de, para in zip(resultado.caminho, resultado.caminho[1:]):
                trecho = km_estrada[frozenset((de, para))]
                acumulado += trecho
                trechos.append({"De": nome_de[de], "Para": nome_de[para],
                                "Trecho (km)": trecho, "Acumulado (km)": acumulado})
            st.dataframe(trechos, hide_index=True, width="stretch")

    if resultado and resultado.passos:
        with st.expander("Passo a passo do Dijkstra"):
            st.caption("Em cada iteração, o algoritmo fecha a cidade com a menor distância "
                       "ainda não visitada e tenta melhorar a distância das vizinhas.")
            linhas = []
            for numero, passo in enumerate(resultado.passos, start=1):
                melhorias = "; ".join(
                    f"{nome_de[u['cidade']]}: "
                    f"{'∞' if u['antes'] == float('inf') else formatar_km(u['antes'])}"
                    f" → {formatar_km(u['depois'])}"
                    for u in passo["atualizacoes"]
                )
                linhas.append({
                    "Iteração": numero,
                    "Cidade fechada": nome_de[passo["cidade"]],
                    "Distância definitiva": formatar_km(passo["distancia"]),
                    "Distâncias melhoradas": melhorias or "—",
                })
            st.dataframe(linhas, hide_index=True, width="stretch")

    caminho = resultado.caminho if resultado and resultado.existe_rota else None
    figura = desenhar_grafo(cidades, estradas, caminho)
    st.pyplot(figura, width="stretch")
    plt.close(figura)


# ---------------------------------------------------------------------------
# Aba: Cidades e conexões (4.3 listar)
# ---------------------------------------------------------------------------

with aba_lista:
    if not cidades:
        st.info("Nenhuma cidade cadastrada.")
    else:
        conexoes = {c["id"]: [] for c in cidades}
        for e in estradas:
            conexoes[e["id_a"]].append(f"{e['nome_b']} ({e['distancia']} km)")
            conexoes[e["id_b"]].append(f"{e['nome_a']} ({e['distancia']} km)")

        st.dataframe(
            [{"Id": c["id"], "Cidade": c["nome"], "Estradas": len(conexoes[c["id"]]),
              "Conexões": ", ".join(sorted(conexoes[c["id"]])) or "Sem conexões"}
             for c in cidades],
            hide_index=True, width="stretch",
        )
        figura = desenhar_grafo(cidades, estradas)
        st.pyplot(figura, width="stretch")
        plt.close(figura)


# Resumo na barra lateral, com os números finais desta execução
with resumo:
    c1, c2 = st.columns(2)
    c1.metric("Cidades", len(cidades))
    c2.metric("Estradas", len(estradas))
