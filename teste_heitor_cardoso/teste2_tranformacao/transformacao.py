import re
import pandas as pd


def limpar_cnpj(valor: str) -> str:
    if valor is None:
        return ""
    return re.sub(r"\D", "", str(valor))


def cnpj_valido(cnpj: str) -> bool:
    # Eu implementei o DV do CNPJ aqui pra não depender de lib externa e ficar transparente no código.
    cnpj = limpar_cnpj(cnpj)
    if len(cnpj) != 14:
        return False
    if cnpj == cnpj[0] * 14:
        return False

    def calc_dv(base: str, pesos: list[int]) -> str:
        soma = sum(int(d) * p for d, p in zip(base, pesos))
        resto = soma % 11
        dv = "0" if resto < 2 else str(11 - resto)
        return dv

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1

    dv1 = calc_dv(cnpj[:12], pesos1)
    dv2 = calc_dv(cnpj[:12] + dv1, pesos2)

    return cnpj.endswith(dv1 + dv2)


def validar_consolidado(df: pd.DataFrame) -> pd.DataFrame:
    # Eu preferi criar colunas de validação (ao invés de sair apagando linhas),
    # porque isso facilita justificar e rastrear problemas no README.
    df = df.copy()

    df["CNPJ"] = df["CNPJ"].map(limpar_cnpj)
    df["cnpj_ok"] = df["CNPJ"].map(cnpj_valido)

    df["RazaoSocial"] = df["RazaoSocial"].fillna("").astype(str).str.strip()
    df["razao_ok"] = df["RazaoSocial"].ne("")

    df["ValorDespesas"] = pd.to_numeric(df["ValorDespesas"], errors="coerce")
    df["valor_ok"] = df["ValorDespesas"].fillna(0).gt(0)

    return df

def agregar_por_operadora_uf(df: pd.DataFrame) -> pd.DataFrame:
    # Eu agrego por RazaoSocial e UF porque o enunciado pede essa visão consolidada.
    # IMPORTANTE: primeiro eu consolido por trimestre pra evitar duplicações inflando soma/média/desvio.

    base = df.copy()
    base = base[base["valor_ok"]].copy()


    por_trimestre = (
        base.groupby(["RazaoSocial", "UF", "Ano", "Trimestre"], dropna=False, as_index=False)
        .agg(despesa_trimestre=("ValorDespesas", "sum"))
    )


    agregado = (
        por_trimestre.groupby(["RazaoSocial", "UF"], dropna=False, as_index=False)
        .agg(
            total_despesas=("despesa_trimestre", "sum"),
            media_trimestre=("despesa_trimestre", "mean"),
            desvio_padrao=("despesa_trimestre", "std"),
            qtd_linhas=("despesa_trimestre", "size"),
        )
    )

    agregado = agregado.sort_values("total_despesas", ascending=False)
    return agregado




def normalizar_cadastro_operadoras(df_cad: pd.DataFrame) -> pd.DataFrame:
    # padroniza nomes de colunas pra não depender do header exato do CSV da ANS.
    df = df_cad.copy()
    df.columns = [c.strip() for c in df.columns]

    mapeamento = {
        "CNPJ": "CNPJ",

        # registro da operadora na ANS
        "REGISTRO_OPERADORA": "RegistroANS",
        "Registro ANS": "RegistroANS",
        "RegistroANS": "RegistroANS",
        "REGISTRO_ANS": "RegistroANS",

        # razão social
        "Razao_Social": "RazaoSocial",
        "Razão Social": "RazaoSocial",
        "RAZAO_SOCIAL": "RazaoSocial",
        "RazaoSocial": "RazaoSocial",

        "Modalidade": "Modalidade",
        "UF": "UF",
    }

    colunas = {}
    for c in df.columns:
        if c in mapeamento:
            colunas[c] = mapeamento[c]

    df = df.rename(columns=colunas)

    if "RegistroANS" not in df.columns:
        raise RuntimeError("O cadastro de operadoras não tem coluna de RegistroANS (ou o nome veio diferente).")

    if "CNPJ" not in df.columns:
        raise RuntimeError("O cadastro de operadoras não tem coluna CNPJ (ou o nome veio diferente).")

    df["RegistroANS"] = df["RegistroANS"].astype(str).str.strip()
    df["CNPJ"] = df["CNPJ"].map(limpar_cnpj)

    if "RazaoSocial" in df.columns:
        df["RazaoSocial"] = df["RazaoSocial"].fillna("").astype(str).str.strip()

    if "UF" in df.columns:
        df["UF"] = df["UF"].fillna("").astype(str).str.strip()

    return df



def resolver_duplicados_cadastro(df_cad: pd.DataFrame) -> pd.DataFrame:
    # Se o cadastro tiver RegistroANS repetido, mantem um registro estável:
    campos = ["RegistroANS", "CNPJ", "Modalidade", "UF", "RazaoSocial"]
    campos_existentes = [c for c in campos if c in df_cad.columns]

    def primeiro_valido(serie: pd.Series) -> str:
        for v in serie.fillna("").astype(str):
            if v.strip():
                return v.strip()
        return ""

    agrupado = df_cad.groupby("RegistroANS", as_index=False)[campos_existentes].agg(primeiro_valido)
    return agrupado



def enriquecer_com_cadastro(df_consolidado_validado: pd.DataFrame, df_cad: pd.DataFrame) -> pd.DataFrame:
    df_cad = normalizar_cadastro_operadoras(df_cad)
    df_cad = resolver_duplicados_cadastro(df_cad)

    df = df_consolidado_validado.merge(df_cad, on="RegistroANS", how="left", suffixes=("", "_cad"))

    # preenche CNPJ e RazaoSocial do consolidado com o cadastro quando estiverem vazios.
    if "CNPJ_cad" in df.columns:
        df["CNPJ"] = df["CNPJ"].where(df["CNPJ"].astype(str).str.strip().ne(""), df["CNPJ_cad"])
        df = df.drop(columns=["CNPJ_cad"])

    if "RazaoSocial_cad" in df.columns:
        df["RazaoSocial"] = df["RazaoSocial"].where(df["RazaoSocial"].astype(str).str.strip().ne(""), df["RazaoSocial_cad"])
        df = df.drop(columns=["RazaoSocial_cad"])

    # Se não tem UF, é porque não casou com cadastro.
    df["sem_match_cadastro"] = df["UF"].isna() | df["UF"].fillna("").astype(str).str.strip().eq("")
    return df
