from pathlib import Path
from urllib.parse import urljoin
import re

import pandas as pd
import requests


URL_BASE = "https://dadosabertos.ans.gov.br/FTP/PDA/"
PASTA_OPERADORAS = "operadoras_de_plano_de_saude_ativas/"


def baixar_arquivo(url: str, destino: Path) -> None:

    if destino.exists():
        return

    destino.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(destino, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def encontrar_csv_operadoras(url_pasta: str) -> str:
    html = requests.get(url_pasta, timeout=30).text
    hrefs = re.findall(r'href\s*=\s*["\']?([^"\' >]+)["\']?', html, flags=re.IGNORECASE)

    for h in hrefs:
        if h.lower().endswith(".csv"):
            return h

    raise RuntimeError("Não encontrei arquivo .csv na pasta de operadoras ativas.")


def carregar_cadastro_operadoras(pasta_raw: Path) -> pd.DataFrame:
    url_pasta = urljoin(URL_BASE, PASTA_OPERADORAS)
    nome_csv = encontrar_csv_operadoras(url_pasta)

    url_csv = urljoin(url_pasta, nome_csv)
    caminho_local = pasta_raw / nome_csv

    baixar_arquivo(url_csv, caminho_local)

    df = pd.read_csv(caminho_local, dtype=str, encoding="utf-8", sep=None, engine="python")
    return df
