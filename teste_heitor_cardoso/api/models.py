from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Operadora(Base):
    __tablename__ = "dim_operadoras"

    registro_ans = Column(String, primary_key=True)
    cnpj = Column(String)
    razao_social = Column(String)
    modalidade = Column(String)
    uf = Column(String)

class Despesa(Base):
    __tablename__ = "fato_despesas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    registro_ans = Column(String)
    ano = Column(Integer)
    trimestre = Column(Integer)
    valor_despesas = Column(Numeric)
