
TRUNCATE dim_operadoras;
TRUNCATE fato_despesas RESTART IDENTITY;
TRUNCATE agg_despesas_uf;



INSERT INTO dim_operadoras (registro_ans, cnpj, razao_social, modalidade, uf)
SELECT
  TRIM(registro_operadora) AS registro_ans,
  NULLIF(REGEXP_REPLACE(cnpj, '[^0-9]', '', 'g'), '') AS cnpj,
  NULLIF(TRIM(razao_social), '') AS razao_social,
  NULLIF(TRIM(modalidade), '') AS modalidade,
  NULLIF(TRIM(uf), '') AS uf
FROM stg_operadoras
WHERE registro_operadora IS NOT NULL
  AND TRIM(registro_operadora) <> '';


INSERT INTO fato_despesas (registro_ans, ano, trimestre, valor_despesas)
SELECT
  NULLIF(TRIM(registroans), '') AS registro_ans,
  NULLIF(ano, '')::INT AS ano,
  NULLIF(trimestre, '')::INT AS trimestre,
  NULLIF(valordespesas, '')::NUMERIC(18,2) AS valor_despesas
FROM stg_consolidado
WHERE NULLIF(ano, '') IS NOT NULL
  AND NULLIF(trimestre, '') IS NOT NULL
  AND NULLIF(valordespesas, '') IS NOT NULL;


INSERT INTO agg_despesas_uf (razao_social, uf, total_despesas, media_trimestre, desvio_padrao, qtd_linhas)
SELECT
  NULLIF(TRIM(razaosocial), '') AS razao_social,
  NULLIF(TRIM(uf), '') AS uf,
  NULLIF(total_despesas, '')::NUMERIC(18,2) AS total_despesas,
  NULLIF(media_trimestre, '')::NUMERIC(18,2) AS media_trimestre,
  NULLIF(desvio_padrao, '')::NUMERIC(18,2) AS desvio_padrao,
  NULLIF(qtd_linhas, '')::INT AS qtd_linhas
FROM stg_agregado;


\echo '--- CHECK TRANSFORM ---'
SELECT COUNT(*) AS n_dim  FROM dim_operadoras;
SELECT COUNT(*) AS n_fato FROM fato_despesas;
SELECT COUNT(*) AS n_agg  FROM agg_despesas_uf;
\echo '--- FIM CHECK ---'
