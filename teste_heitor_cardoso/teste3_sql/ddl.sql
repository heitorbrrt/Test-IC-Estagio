-- LIMPEZA 
DROP TABLE IF EXISTS stg_consolidado;
DROP TABLE IF EXISTS stg_agregado;
DROP TABLE IF EXISTS stg_operadoras;

DROP TABLE IF EXISTS fato_despesas;
DROP TABLE IF EXISTS dim_operadoras;
DROP TABLE IF EXISTS agg_despesas_uf;

-- Tudo TEXT pra não travar importação por sujeira no CSV
CREATE TABLE stg_consolidado (
  registroans   TEXT,
  cnpj          TEXT,
  razaosocial   TEXT,
  trimestre     TEXT,
  ano           TEXT,
  valordespesas TEXT
);

CREATE TABLE stg_agregado (
  razaosocial     TEXT,
  uf              TEXT,
  total_despesas  TEXT,
  media_trimestre TEXT,
  desvio_padrao   TEXT,
  qtd_linhas      TEXT
);

CREATE TABLE stg_operadoras (
  registro_operadora        TEXT,
  cnpj                      TEXT,
  razao_social              TEXT,
  nome_fantasia             TEXT,
  modalidade                TEXT,
  logradouro                TEXT,
  numero                    TEXT,
  complemento               TEXT,
  bairro                    TEXT,
  cidade                    TEXT,
  uf                        TEXT,
  cep                       TEXT,
  ddd                       TEXT,
  telefone                  TEXT,
  fax                       TEXT,
  endereco_eletronico       TEXT,
  representante             TEXT,
  cargo_representante       TEXT,
  regiao_de_comercializacao TEXT,
  data_registro_ans         TEXT
);

-- Opção B: normalizado (dim + fato + agregado)
-- DIM: operadoras
CREATE TABLE dim_operadoras (
  registro_ans VARCHAR(32) PRIMARY KEY,
  cnpj         CHAR(14),
  razao_social TEXT,
  modalidade   TEXT,
  uf           CHAR(2)
);

-- FATO: despesas por período (trimestre)
CREATE TABLE fato_despesas (
  id            BIGSERIAL PRIMARY KEY,
  registro_ans  VARCHAR(32),
  ano           INT NOT NULL,
  trimestre     INT NOT NULL,
  valor_despesas NUMERIC(18,2) NOT NULL
);

-- AGREGADO: por UF e razão social (resultado do teste 2.3)
CREATE TABLE agg_despesas_uf (
  razao_social    TEXT,
  uf              CHAR(2),
  total_despesas  NUMERIC(18,2),
  media_trimestre NUMERIC(18,2),
  desvio_padrao   NUMERIC(18,2),
  qtd_linhas      INT
);


CREATE INDEX idx_fato_periodo   ON fato_despesas (ano, trimestre);
CREATE INDEX idx_fato_registro  ON fato_despesas (registro_ans);
CREATE INDEX idx_dim_uf         ON dim_operadoras (uf);
CREATE INDEX idx_agg_uf         ON agg_despesas_uf (uf);
CREATE INDEX idx_agg_total      ON agg_despesas_uf (total_despesas);
