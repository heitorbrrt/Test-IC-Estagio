TRUNCATE TABLE stg_consolidado;
TRUNCATE TABLE stg_agregado;
TRUNCATE TABLE stg_operadoras;

-- IMPORTS
\copy stg_consolidado FROM 'data/processed/consolidado_despesas.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

\copy stg_agregado FROM 'data/processed/despesas_agregadas.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',', ENCODING 'UTF8');

\copy stg_operadoras FROM 'data/raw/operadoras/Relatorio_cadop.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8');

\echo '--- CHECK IMPORT ---'
SELECT COUNT(*) AS n_consolidado FROM stg_consolidado;
SELECT COUNT(*) AS n_agregado    FROM stg_agregado;
SELECT COUNT(*) AS n_operadoras  FROM stg_operadoras;
\echo '--- FIM CHECK ---'
