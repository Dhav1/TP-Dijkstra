"""
Busca de municípios na API pública do IBGE (gratuita, não precisa de chave).

Usada só para ajudar no cadastro (nome oficial + código IBGE).
As distâncias continuam sendo informadas pelo grupo.
Se não houver internet, o programa continua funcionando com cadastro manual.
"""

from __future__ import annotations

import requests

URL = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"

UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
    "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]


class ErroIBGE(Exception):
    pass


def buscar_municipios(uf: str) -> list[dict]:
    """Devolve [{'codigo': <código do IBGE>, 'nome': 'Viçosa'}, ...] em ordem alfabética."""
    try:
        resposta = requests.get(URL.format(uf=uf), params={"orderBy": "nome"}, timeout=10)
        resposta.raise_for_status()
        dados = resposta.json()
    except requests.RequestException as erro:
        raise ErroIBGE(
            "Não foi possível acessar a API do IBGE. Verifique a internet ou cadastre a cidade manualmente."
        ) from erro

    return [{"codigo": m["id"], "nome": m["nome"]} for m in dados]
