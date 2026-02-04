import re
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests


URL_BASE = "https://dadosabertos.ans.gov.br/FTP/PDA/"
PASTA_DEMONSTRACOES = "demonstracoes_contabeis/"


def baixar_html(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def extrair_hrefs(html: str) -> list[str]:
    brutos = re.findall(r'href\s*=\s*["\']?([^"\' >]+)["\']?', html, flags=re.IGNORECASE)

    ignorar = {"../", "./"}
    vistos = set()
    saida = []
    for href in brutos:
        if href in ignorar:
            continue
        if href not in vistos:
            vistos.add(href)
            saida.append(href)
    return saida

def _to_float_ptbr(serie: pd.Series) -> pd.Series:
    return (
        serie
        .fillna("0")
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .astype(float)
    )


def listar_pastas(url: str) -> list[str]:
    html = baixar_html(url)
    hrefs = extrair_hrefs(html)

    pastas = []
    for h in hrefs:
        if h.endswith("/"):
            pastas.append(h)
        else:
            if "." not in h and not h.startswith("?") and not h.startswith("#"):
                pastas.append(h + "/")

    vistos = set()
    saida = []
    for p in pastas:
        if p not in vistos:
            vistos.add(p)
            saida.append(p)
    return saida


def listar_anos(url_demo: str) -> list[int]:
    pastas = listar_pastas(url_demo)
    anos = [int(p.strip("/")) for p in pastas if re.fullmatch(r"\d{4}/", p)]
    anos.sort()
    return anos

def _extrair_trimestre_de_nome(nome_zip: str) -> int | None:
    n = nome_zip.lower()

    m = re.search(r"([1-4])t\d{4}\.zip$", n)
    if m:
        return int(m.group(1))

    m = re.search(r"\d{4}-([1-4])t\.zip$", n)
    if m:
        return int(m.group(1))

    m = re.search(r"([1-4])[-_ ]*trimestre\.zip$", n)
    if m:
        return int(m.group(1))

    m = re.search(r"[_-]([1-4])[_-]trim", n)
    if m:
        return int(m.group(1))

    return None


def listar_zips_por_trimestre(url_demo: str, ano: int) -> dict[int, list[str]]:
    url_ano = urljoin(url_demo, f"{ano}/")
    html = baixar_html(url_ano)
    hrefs = extrair_hrefs(html)

    zips = [h for h in hrefs if h.lower().endswith(".zip")]

    por_tri: dict[int, list[str]] = {}
    for nome in zips:
        tri = _extrair_trimestre_de_nome(nome)
        if tri is None:
            continue
        por_tri.setdefault(tri, []).append(nome)

    # deixa os nomes ordenados
    for tri in por_tri:
        por_tri[tri].sort()

    return por_tri



def ultimos_3_trimestres(url_demo: str, anos: list[int]) -> list[tuple[int, int]]:
    # Eu escolho os 3 trimestres mais recentes com base em (ano, trimestre).
    selecionados: list[tuple[int, int]] = []

    for ano in sorted(anos, reverse=True):
        por_tri = listar_zips_por_trimestre(url_demo, ano)
        for tri in sorted(por_tri.keys(), reverse=True):
            selecionados.append((ano, tri))
            if len(selecionados) == 3:
                return selecionados

    return selecionados



def baixar(url: str, destino: Path) -> None:
    if destino.exists():
        print(f"  -> Já existe localmente: {destino.name}")
        return

    print(f"  -> Baixando: {destino.name}")
    destino.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(destino, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    print(f"  -> Download concluído: {destino.name}")



def extrair_zip(caminho_zip: Path, destino: Path) -> None:
    # Extrai cada ZIP em uma pasta própria 
    destino.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(caminho_zip, "r") as z:
        z.extractall(destino)


def listar_arquivos(pasta: Path) -> list[Path]:
    return [p for p in pasta.rglob("*") if p.is_file()]


def _tem_indicadores(texto: str) -> bool:
    t = texto.lower()
    return re.search(r"\bdespesas\s+com\s+(eventos|sinistros)", t) is not None


def parece_despesa(caminho: Path) -> bool:
    try:
        if caminho.suffix.lower() in (".csv", ".txt"):
            leitor = pd.read_csv(
                caminho,
                sep=None,
                engine="python",
                dtype=str,
                encoding="utf-8",
                on_bad_lines="skip",
                usecols=lambda c: str(c).strip().upper() == "DESCRICAO",
                chunksize=50000,
            )

            for chunk in leitor:
                serie = chunk.get("DESCRICAO")
                if serie is None:
                    return False

                texto = " ".join(serie.fillna("").astype(str).tolist()).lower()
                if ("evento" in texto) or ("sinistro" in texto):
                    return True

            return False

        # Se não é csv/txt não considera
        return False

    except Exception:
        return False




def filtrar_despesas(arquivos: list[Path]) -> list[Path]:
    return [a for a in arquivos if parece_despesa(a)]

def inspecionar_csv(caminho: Path) -> None:
    # inspeciona as colunas e algumas linhas pra entender o layout real antes de normalizar
    df = pd.read_csv(caminho, sep=None, engine="python", nrows=5, dtype=str, encoding="utf-8", on_bad_lines="skip")
    print("\n=== INSPEÇÃO:", caminho, "===")
    print("Colunas:", list(df.columns))
    print(df.head())

def normalizar_despesas(caminho: Path) -> list[dict]:
    # Essa função transforma o CSV contábil em linhas normalizadas
    nome = caminho.stem 
    trimestre = nome[0]
    ano = nome[-4:]

    df = pd.read_csv(
        caminho,
        sep=None,
        engine="python",
        dtype=str,
        encoding="utf-8",
        on_bad_lines="skip",
    )

    # filtra as linhas pra ficar só com contas ligadas a eventos/sinistros
    padrao = r"\bdespesas\s+com\s+(?:eventos|sinistros)(?:\s*[/\-]\s*(?:eventos|sinistros))?"
    df = df[df["DESCRICAO"].fillna("").str.contains(padrao, case=False, regex=True, na=False)]

    df["VL_SALDO_INICIAL"] = _to_float_ptbr(df["VL_SALDO_INICIAL"])
    df["VL_SALDO_FINAL"] = _to_float_ptbr(df["VL_SALDO_FINAL"])

    df["VALOR_PERIODO"] = df["VL_SALDO_FINAL"] - df["VL_SALDO_INICIAL"]
    df = df[df["VALOR_PERIODO"] > 0]

    linhas = []
    agrupado = df.groupby("REG_ANS")["VALOR_PERIODO"].sum().reset_index()

    for _, row in agrupado.iterrows():
        linhas.append({
            "RegistroANS": str(row["REG_ANS"]).strip(),
            "CNPJ": "",
            "RazaoSocial": "",
            "Trimestre": trimestre,
            "Ano": ano,
            "ValorDespesas": round(float(row["VALOR_PERIODO"]), 2),
        })
    print(df["DESCRICAO"].dropna().drop_duplicates().head(20).to_list())


    return linhas

