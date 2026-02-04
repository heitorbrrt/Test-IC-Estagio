from pathlib import Path
import zipfile

import pandas as pd

from operadoras import carregar_cadastro_operadoras
from transformacao import (
    validar_consolidado,
    enriquecer_com_cadastro,
    agregar_por_operadora_uf,
)

if __name__ == "__main__":

    entrada = Path("../data/processed/consolidado_despesas.csv")
    pasta_raw_operadoras = Path("../data/raw/operadoras")
    pasta_saida = Path("../data/processed")

    if not entrada.exists():
        raise RuntimeError("Não encontrei consolidado_despesas.csv em data/processed. Rode o Teste 1 primeiro.")

    pasta_saida.mkdir(parents=True, exist_ok=True)


    df_consolidado = pd.read_csv(entrada, dtype=str, encoding="utf-8")
    df_validado = validar_consolidado(df_consolidado)


    df_cadastro = carregar_cadastro_operadoras(pasta_raw_operadoras)

    print("Colunas do cadastro:", list(df_cadastro.columns))
    print(df_cadastro.head(3))


    df_enriquecido = enriquecer_com_cadastro(df_validado, df_cadastro)


    colunas_debug = [c for c in ["RegistroANS", "CNPJ", "RazaoSocial", "Modalidade", "UF", "sem_match_cadastro"] if c in df_enriquecido.columns]
    print("\nAmostra pós-join:")
    print(df_enriquecido[colunas_debug].head(10))
    print("Sem match no cadastro:", int(df_enriquecido["sem_match_cadastro"].sum()))


    df_agregado = agregar_por_operadora_uf(df_enriquecido)


    cols_num = ["total_despesas", "media_trimestre", "desvio_padrao"]
    for c in cols_num:
        if c in df_agregado.columns:
            df_agregado[c] = pd.to_numeric(df_agregado[c], errors="coerce").fillna(0)

    saida_agregado = pasta_saida / "despesas_agregadas.csv"
    df_agregado.to_csv(saida_agregado, index=False, encoding="utf-8", float_format="%.2f")

    zip_saida = pasta_saida / "Teste_Heitor_Cardoso.zip"
    with zipfile.ZipFile(zip_saida, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(saida_agregado, arcname="despesas_agregadas.csv")

    print("\nArquivo agregado gerado em:", saida_agregado)
    print("ZIP final gerado em:", zip_saida)


    colunas_saida = [
        "CNPJ",
        "RazaoSocial",
        "RegistroANS",
        "Modalidade",
        "UF",
        "Trimestre",
        "Ano",
        "ValorDespesas",
    ]

    faltando = [c for c in colunas_saida if c not in df_enriquecido.columns]
    if faltando:
        raise RuntimeError(f"Estão faltando colunas no df_enriquecido: {faltando}")

    df_final = df_enriquecido[colunas_saida].copy()


    df_final["ValorDespesas"] = pd.to_numeric(df_final["ValorDespesas"], errors="coerce").fillna(0)

    saida_enriquecido = pasta_saida / "consolidado_enriquecido.csv"
    df_final.to_csv(saida_enriquecido, index=False, encoding="utf-8", float_format="%.2f")

    print("\nArquivo final do Teste 2 gerado em:", saida_enriquecido)
    print(df_final.head(10))
