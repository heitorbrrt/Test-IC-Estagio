from pathlib import Path
from urllib.parse import urljoin
import pandas as pd
import zipfile

from ans_ftp import (
    URL_BASE,
    PASTA_DEMONSTRACOES,
    listar_anos,
    ultimos_3_trimestres,
    listar_zips_por_trimestre,
    baixar,
    extrair_zip,
    listar_arquivos,
    filtrar_despesas,
    normalizar_despesas,
)


if __name__ == "__main__":
    url_demo = urljoin(URL_BASE, PASTA_DEMONSTRACOES)

    anos = listar_anos(url_demo)
    if not anos:
        raise RuntimeError("Não encontrei anos dentro da pasta de demonstrações contábeis.")

    trimestres = ultimos_3_trimestres(url_demo, anos)
    print("Trimestres selecionados (ano, trimestre):", trimestres)


    pasta_raw = Path("../data/raw/demonstracoes_contabeis")
    pasta_ext = Path("../data/raw_extraido/demonstracoes_contabeis")

    for ano, tri in trimestres:
        por_tri = listar_zips_por_trimestre(url_demo, ano)
        zips_do_tri = por_tri.get(tri, [])

        for zip_nome in zips_do_tri:
            url_zip = urljoin(url_demo, f"{ano}/{zip_nome}")
            zip_local = pasta_raw / str(ano) / zip_nome

            print(f"Verificando download de: {zip_nome} (T{tri}/{ano})")
            baixar(url_zip, zip_local)

            destino = pasta_ext / str(ano) / zip_nome.replace(".zip", "")
            extrair_zip(zip_local, destino)

            arquivos_zip = listar_arquivos(destino)
            exts = sorted({a.suffix.lower() for a in arquivos_zip})
            print(f"[debug] {zip_nome} extraído: {len(arquivos_zip)} arquivos, extensões: {exts}")

    todos = listar_arquivos(pasta_ext)
    print("[debug] total de arquivos extraídos:", len(todos))




    arquivos = listar_arquivos(pasta_ext)
    candidatos = filtrar_despesas(arquivos)

    print("Total de arquivos que podem ser processados:", len(candidatos))
    linhas_consolidadas = []

    for c in candidatos:
        linhas = normalizar_despesas(c)
        linhas_consolidadas.extend(linhas)

    df_final = pd.DataFrame(linhas_consolidadas)
    colunas_saida = ["RegistroANS", "CNPJ", "RazaoSocial", "Trimestre", "Ano", "ValorDespesas"]


    df_final = df_final[colunas_saida]
    print("[debug] colunas no df_final:", list(df_final.columns))


    saida = Path("../data/processed/consolidado_despesas.csv")
    saida.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(saida, index=False, encoding="utf-8")
    zip_saida = Path("../data/processed/consolidado_despesas.zip")

    with zipfile.ZipFile(zip_saida, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(saida, arcname="consolidado_despesas.csv")

    print("Arquivo ZIP final gerado em:", zip_saida)


    print("CSV consolidado gerado em:", saida)
    print(df_final.head())

