from pydantic import BaseModel
from typing import Optional, List

class OperadoraBase(BaseModel):
    registro_ans: str
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    modalidade: Optional[str] = None
    uf: Optional[str] = None

    class Config:
        from_attributes = True 

class DespesaBase(BaseModel):
    ano: int
    trimestre: int
    valor_despesas: float

    class Config:
        from_attributes = True


class Query1Crescimento(BaseModel):
    registro_ans: str
    razao_social: Optional[str] = None
    uf: Optional[str] = None
    v_ini: float
    v_fim: float
    crescimento_pct: float

class Query2DistribUF(BaseModel):
    uf: str
    total_uf: float
    media_por_operadora: float

class Query3AcimaMedia(BaseModel):
    qtd_operadoras: int
