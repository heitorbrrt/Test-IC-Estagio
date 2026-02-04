

\echo '===================='
\echo 'QUERY 1'
\echo '===================='

-- 5 operadoras com maior crescimento percentual entre o 1º e o último trimestre analisado
WITH periodos AS (
  SELECT MIN(ano*10 + trimestre) AS p_ini,
         MAX(ano*10 + trimestre) AS p_fim
  FROM fato_despesas
),
base AS (
  SELECT
    registro_ans,
    SUM(CASE WHEN (ano*10 + trimestre) = (SELECT p_ini FROM periodos) THEN valor_despesas END) AS v_ini,
    SUM(CASE WHEN (ano*10 + trimestre) = (SELECT p_fim FROM periodos) THEN valor_despesas END) AS v_fim
  FROM fato_despesas
  GROUP BY registro_ans
),
calc AS (
  SELECT
    registro_ans,
    v_ini,
    v_fim,
    CASE
      WHEN v_ini IS NULL OR v_ini = 0 OR v_fim IS NULL THEN NULL
      ELSE ((v_fim - v_ini) / v_ini) * 100
    END AS crescimento_pct
  FROM base
)
SELECT
  c.registro_ans,
  d.razao_social,
  d.uf,
  c.v_ini,
  c.v_fim,
  c.crescimento_pct
FROM calc c
LEFT JOIN dim_operadoras d ON d.registro_ans = c.registro_ans
WHERE c.crescimento_pct IS NOT NULL
ORDER BY c.crescimento_pct DESC
LIMIT 5;


\echo '===================='
\echo 'QUERY 2'
\echo '===================='

-- Distribuição por UF: top 5 UFs por total + média de despesas por operadora dentro de cada UF
WITH por_operadora AS (
  SELECT
    d.uf,
    f.registro_ans,
    SUM(f.valor_despesas) AS total_operadora
  FROM fato_despesas f
  JOIN dim_operadoras d ON d.registro_ans = f.registro_ans
  GROUP BY d.uf, f.registro_ans
),
por_uf AS (
  SELECT
    uf,
    SUM(total_operadora) AS total_uf,
    AVG(total_operadora) AS media_por_operadora
  FROM por_operadora
  GROUP BY uf
)
SELECT
  uf,
  total_uf,
  media_por_operadora
FROM por_uf
ORDER BY total_uf DESC
LIMIT 5;


\echo '===================='
\echo 'QUERY 3'
\echo '===================='

-- Quantas operadoras ficaram acima da média geral em pelo menos 2 dos 3 trimestres analisados
WITH media_periodo AS (
  SELECT
    ano,
    trimestre,
    AVG(valor_despesas) AS media_geral
  FROM fato_despesas
  GROUP BY ano, trimestre
),
operadora_periodo AS (
  SELECT
    registro_ans,
    ano,
    trimestre,
    SUM(valor_despesas) AS total_operadora
  FROM fato_despesas
  GROUP BY registro_ans, ano, trimestre
),
comparacao AS (
  SELECT
    o.registro_ans,
    o.ano,
    o.trimestre,
    CASE WHEN o.total_operadora > m.media_geral THEN 1 ELSE 0 END AS acima
  FROM operadora_periodo o
  JOIN media_periodo m
    ON m.ano = o.ano AND m.trimestre = o.trimestre
)
SELECT
  COUNT(*) AS qtd_operadoras
FROM (
  SELECT registro_ans
  FROM comparacao
  GROUP BY registro_ans
  HAVING SUM(acima) >= 2
) x;
