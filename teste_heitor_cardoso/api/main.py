from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware


from database import get_db
import models

app = FastAPI(title="API Operadoras ANS")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# serve pra listar as operadoras com paginação + bucsa
@app.get("/api/operadoras")
def listar_operadoras(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    q: str | None = Query(None, description="Busca por razão social ou CNPJ (parcial)"),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * limit

    query_base = db.query(models.Operadora)

    if q:
        q = q.strip()
        query_base = query_base.filter(
            (models.Operadora.razao_social.ilike(f"%{q}%")) |
            (models.Operadora.cnpj.ilike(f"%{q}%"))
        )

    total = query_base.count()

    operadoras = (
        query_base
        .order_by(models.Operadora.razao_social.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "data": operadoras,
        "page": page,
        "limit": limit,
        "total": total
    }


# detalhar a operadora usando cpf de chave
@app.get("/api/operadoras/{cnpj}", summary="Detalhe da operadora (por CNPJ)")
def detalhe_operadora(cnpj: str, db: Session = Depends(get_db)):

    # normaliza: deixa só dígitos
    cnpj_digits = "".join([c for c in cnpj if c.isdigit()])

    op = db.query(models.Operadora).filter(models.Operadora.cnpj == cnpj_digits).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
    return op


# mostrar as despesas da operadora usando cpf de chave
@app.get("/api/operadoras/{cnpj}/despesas")
def despesas_operadora(cnpj: str, db: Session = Depends(get_db)):
    cnpj_digits = "".join([c for c in cnpj if c.isdigit()])

    op = db.query(models.Operadora).filter(models.Operadora.cnpj == cnpj_digits).first()
    if not op:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")

    despesas = (
        db.query(models.Despesa)
        .filter(models.Despesa.registro_ans == op.registro_ans)
        .order_by(models.Despesa.ano.asc(), models.Despesa.trimestre.asc())
        .all()
    )
    return despesas


# estatisticas
@app.get("/api/estatisticas")
def estatisticas(db: Session = Depends(get_db)):
    total = db.execute(text("SELECT COALESCE(SUM(valor_despesas), 0) FROM fato_despesas")).scalar()
    media = db.execute(text("SELECT COALESCE(AVG(valor_despesas), 0) FROM fato_despesas")).scalar()

    top5 = db.execute(text("""
        SELECT d.razao_social, SUM(f.valor_despesas) AS total
        FROM fato_despesas f
        JOIN dim_operadoras d ON d.registro_ans = f.registro_ans
        GROUP BY d.razao_social
        ORDER BY total DESC
        LIMIT 5
    """)).fetchall()

    return {
        "total_despesas": float(total),
        "media_despesas": float(media),
        "top_5_operadoras": [
            {"razao_social": r[0], "total": float(r[1])} for r in top5
        ]
    }
# distribuição de despesas por UF, para o grafico
@app.get("/api/ufs")
def despesas_por_uf(db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT
            uf,
            SUM(valor_despesas) AS total
        FROM fato_despesas f
        JOIN dim_operadoras d ON d.registro_ans = f.registro_ans
        GROUP BY uf
        ORDER BY total DESC
    """)).fetchall()

    return [
        {"uf": r[0], "total": float(r[1])}
        for r in rows
        if r[0] is not None
    ]
