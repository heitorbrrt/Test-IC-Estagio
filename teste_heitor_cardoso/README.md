

Teste 1 – Integração com a API pública da ANS (teste1_api)

Objetivo
    Consumir os dados públicos da ANS via FTP, identificar automaticamente os últimos 3 trimestres disponíveis, processar os arquivos de despesas com eventos/sinistros e gerar um arquivo CSV consolidado compactado em ZIP.

----------------

Acesso à API de Dados Abertos da ANS

    O acesso é feito diretamente ao FTP público da ANS (https://dadosabertos.ans.gov.br/FTP/PDA/).
    A navegação pelas pastas é dinâmica, baseada na leitura do HTML e extração de hrefs, evitando dependência de uma estrutura fixa.
    A identificação dos anos disponíveis é feita a partir dos diretórios no formato YYYY/, permitindo adaptação automática a novos dados publicados.

----------------------

Identificação dos últimos 3 trimestres

    Os trimestres são identificados combinando (ano, trimestre).
    Para cada ano, os arquivos ZIP são analisados e o trimestre é inferido a partir do nome do arquivo usando expressões regulares.
    Os três trimestres mais recentes são selecionados de forma decrescente, independentemente de mudanças de nomenclatura.

Justificativa:
    Alguns trimestres possuem múltiplos arquivos e padrões de nome distintos. A inferência por regex evita hardcode e garante compatibilidade com variações históricas.

---------------------

Processamento dos arquivos ZIP

    Todos os arquivos ZIP dos trimestres selecionados são baixados.
    Cada ZIP é extraído automaticamente em um diretório próprio.
    Após a extração, todos os arquivos internos são listados para inspeção.

------------------

Identificação automática de arquivos de despesas

    Apenas arquivos CSV ou TXT são considerados.
    Os arquivos são lidos em chunks, analisando a coluna DESCRICAO.
    Um arquivo é classificado como elegível se contiver referências a “despesas com eventos” ou “sinistros”.

Justificativa:
    Nem todos os arquivos contábeis representam despesas assistenciais. A filtragem textual evita a inclusão de contas administrativas, tributárias ou não relacionadas.

-----------------------

Normalização de formatos e estruturas

    O separador de colunas é detectado automaticamente (sep=None).
    O encoding é tratado como UTF-8 com tolerância a linhas inválidas.
    Valores monetários no padrão brasileiro são convertidos explicitamente para float.
    O valor de despesas do período é calculado como:
    ValorDespesas = VL_SALDO_FINAL - VL_SALDO_INICIAL

**Justificativa:**
Os arquivos possuem estruturas variadas entre anos e trimestres. A detecção automática reduz falhas e dispensa tratamento manual por arquivo.

---------------------

Trade-off técnico: processamento em memória vs incremental

Escolha adotada: processamento incremental (chunked).
    Os arquivos são lidos em blocos (chunksize) ao invés de carregar tudo em memória.

Justificativa:
    O volume de dados pode variar significativamente entre trimestres. O processamento incremental reduz consumo de memória, melhora escalabilidade e evita falhas em ambientes com recursos limitados.

----------------------

Consolidação dos dados

    Os dados dos três trimestres são consolidados em um único DataFrame.
    A agregação é feita por `RegistroANS`, trimestre e ano.
    O arquivo final contém as colunas:

    CNPJ
    RazaoSocial
    Trimestre
    Ano
    ValorDespesas

---

Tratamento de inconsistências
CNPJs duplicados com razões sociais diferentes

    Nesta etapa, os demonstrativos não trazem CNPJ e razão social de forma confiável.
    Esses campos são mantidos vazios para evitar associações incorretas.
    O enriquecimento ocorre em etapa posterior (integração com cadastro de operadoras).

Valores zerados ou negativos

    Valores menores ou iguais a zero são descartados.
    Apenas despesas efetivas do período são consideradas.

Formatos inconsistentes de trimestre

    O trimestre é inferido a partir do nome do arquivo ZIP.
    Arquivos que não permitem inferência confiável são ignorados.

Justificativa:
    A prioridade foi garantir consistência numérica e evitar inferências incorretas. Casos ambíguos são descartados em vez de corrigidos arbitrariamente.

--------------------------

Saída gerada

    data/processed/consolidado_despesas.csv
    data/processed/consolidado_despesas.zip

-------------------

Como executar

1. Instalar dependências:

   pip install pandas requests


2. Executar o script principal:

   python main.py

3. O arquivo consolidado será gerado automaticamente na pasta data/processed/.

------------------------------------

Teste 2 - Teste de Transformação e Validação de Dados

Objetivo

    A partir do consolidado_despesas.csv, validar qualidade dos dados, enriquecer com o cadastro oficial de operadoras ativas (ANS) e gerar:
    consolidado_enriquecido.csv (granularidade por trimestre, com RegistroANS/Modalidade/UF)
    despesas_agregadas.csv (total, média por trimestre e desvio padrão por operadora/UF)
    Teste_Heitor_Cardoso.zip (compactação do agregado)

---------------------

Validações aplicadas no consolidado:

    CNPJ válido: cnpj_ok
    Valor numérico positivo: valor_ok
    Razão social não vazia: razao_ok

Tratamento escolhido para inconsistências:

    CNPJ inválido / ausente: não remove linhas; apenas marca cnpj_ok = False.
    Valores não numéricos / <= 0: converte com to_numeric(errors="coerce") e marca valor_ok.
    Razão social vazia: marca razao_ok.

Justificativa:

    As flags preservam o dado bruto para auditoria e evitam perda silenciosa de informação.
    As etapas que geram estatísticas (agregação) usam apenas valor_ok = True, evitando distorções.

---


Fonte: 
    Cadastro oficial de operadoras ativas (ANS), baixado automaticamente em data/raw/operadoras/.

Chave do join (decisão técnica):

    O enunciado sugere join por CNPJ, porém o consolidado_despesas.csv do Teste 1 não traz CNPJ preenchido, enquanto traz RegistroANS.
    Por isso, o enriquecimento foi feito por RegistroANS, e o CNPJ passa a ser preenchido a partir do cadastro.

Justificativa:

    RegistroANS é a chave presente e consistente entre demonstrativo contábil e cadastro; garante enriquecimento completo sem depender de CNPJ ausente no consolidado.

------------

Registros sem match no cadastro:

    Linhas sem correspondência são mantidas e marcadas com sem_match_cadastro = True (UF vazia/nula).

Justificativa:

    Mantém o histórico de despesas mesmo quando o cadastro não contém a operadora (cadastro pode mudar ao longo do tempo).

---------------

Duplicados no cadastro:

    Se houver múltiplas linhas com o mesmo RegistroANS, aplica deduplicação determinística (“primeiro valor não vazio” por coluna).

Justificativa:

    Evita duplicação de linhas no merge (o que inflaria despesas) e mantém uma regra estável e reprodutível.

----------------

Trade-off técnico (processamento do join):

    Estratégia escolhida: processamento em memória com pandas (merge + groupby).

Justificativa:

    O volume (3 trimestres + cadastro) é suficientemente pequeno para caber em memória com folga, e a implementação fica mais simples e legível.

-------------

Agregação com múltiplas estratégias

Requisito:

    Agrupar por `RazaoSocial` e `UF`
    Calcular `total_despesas`, `media_trimestre`, `desvio_padrao`

Escolha técnica:

    A agregação é feita em 2 etapas para evitar distorções:

  1. Consolida primeiro por (RazaoSocial, UF, Ano, Trimestre) somando ValorDespesas → gera despesa_trimestre
  2. Calcula total/média/desvio com base em despesa_trimestre

Justificativa:

    Sem a consolidação intermediária por trimestre, a média e o desvio padrão podem ficar incorretos se existirem múltiplas linhas por operadora dentro do mesmo trimestre (estatísticas seriam calculadas sobre linhas contábeis em vez de “1 valor por trimestre”).

-------------------

Ordenação (trade-off):

    Ordenação em memória (sort_values) por total_despesas(descendente).

Justificativa:

    O resultado agregado tem poucas centenas/milhares de linhas; ordenar em memória é suficiente e mantém simplicidade.

----------------------

Padronização de saída numérica:

    Antes de salvar, colunas numéricas do agregado são convertidas para número e exportadas com float_format="%.2f".

Justificativa:

    Evita mistura de texto/número no CSV que faz o Excel “formatar” alguns valores com separadores inconsistentes.

---------------------

Observação sobre “CNPJ duplicado com razões sociais diferentes”

O enunciado cita essa inconsistência na consolidação. No pipeline implementado:
No Teste 1 o campo CNPJ vem vazio (o demonstrativo contábil está identificado por RegistroANS).
O CNPJ e a RazaoSocial passam a existir de forma confiável apenas após o enriquecimento com o cadastro (Teste 2), usando RegistroANS como chave.

Por isso:

A inconsistência “mesmo CNPJ com razões sociais diferentes” não é tratada na consolidação inicial (Teste 1), pois não há CNPJ disponível para comparar.
Após o enriquecimento, RazaoSocial/CNPJ são herdados do cadastro oficial e a deduplicação é feita por RegistroANS, garantindo consistência do join e evitando multiplicação de linhas.

Como rodar

Pré-requisito: o Teste 1 já deve ter gerado data/processed/consolidado_despesas.csv.

Execute:

    python main.py

Arquivos gerados em data/processed/:

    consolidado_enriquecido.csv
    despesas_agregadas.csv
    Teste_Heitor_Cardoso.zip

----------------------------------------

Teste 3 — Banco de Dados e Análise (PostgreSQL)

Objetivo

    Carregar os 3 CSVs (consolidado, agregadas e cadastro de operadoras) no PostgreSQL de forma reprodutível, e deixar queries analíticas prontas para rodar.

-----------------



Normalização

Escolha: Opção B (tabelas normalizadas separadas)

    dim_operadoras: dados “de cadastro” (uma linha por operadora / Registro ANS)
    fato_despesas: valores por período (ano, trimestre) ligados à operadora
    agg_despesas_uf: tabela já agregada por Razão Social e UF

Justificativa:

    Volume: despesas são “muitas linhas” e operadoras são “poucas linhas”. Separar evita repetir dados da operadora em toda linha de despesa.
    Atualização: cadastro pode mudar sem precisar reescrever todas as despesas.
    Queries analíticas: ficam mais simples e o banco consegue indexar melhor.

-----------------------

Tipos de dados

Escolha:

    Dinheiro: NUMERIC(18,2) (em vez de FLOAT)
    Período (ano/trimestre): INT

Justificativa:

    NUMERIC evita erro de arredondamento do FLOAT.
    ano e trimestre como INT facilita ordenar e calcular “primeiro vs último período” sem depender de datas completas.

--------------------

Importação e tratamento de inconsistências

Escolha: importar primeiro em staging tudo como TEXTO (stg_*) e só depois converter.

Justificativa

    CSV real costuma vir com vazio, texto onde era número, e separadroes diferentes. Se eu tento criar as tabelas finais direto com tipo forte, o COPY quebra na primeira linha ruim.

Como foi tratado:

    NULL em campo obrigatório:

        na staging entra como texto vazio
        na transformação vira `NULL` com `NULLIF(coluna, '')`
        e só entra na tabela final se fizer sentido (ex: ano/trimestre válidos, valor convertível)
    
    Strings em campos numéricos:

        conversão com `CAST(...)`/`::numeric` depois de limpeza
        se não converter, vira `NULL` e não entra na tabela final (ou entra como 0 dependendo do campo — mas para despesa eu tratei como “não confiável”, então não entra)

    Datas/Períodos inconsistentes:

        como o período já vem separado em `Ano` e `Trimestre` nos CSVs, a regra foi: converter para INT e rejeitar o que não virar número.

-------------------

Query 1 — Top 5 crescimento percentual
    Como foi tratado o “operadora sem todos os trimestres”:

        A query pega o primeiro período existente no banco** e o último período existente no banco.
        Para cada operadora:

        se não existir valor no primeiro **ou** no último → ela não entra no ranking
        se o valor inicial for 0 → não calcula percentual (evita divisão por zero)

    Justificativa: crescimento percentual só faz sentido se eu tiver os dois pontos (início e fim) e um “início” > 0.

Query 2 — Top 5 UFs por total + média por operadora na UF

    A query faz em duas etapas:

    1. soma total por **operadora dentro da UF**
    2. depois calcula:
        total da UF (somando as operadoras)
        média por operadora (AVG dos totais por operadora)

Justificativa: se eu calculasse média direto em cima das linhas de despesas, ia distorcer (operadoras com mais linhas teriam mais “peso”).

Query 3 — Operadoras acima da média em pelo menos 2 dos 3 trimestres

    Estratégia escolhida: CTEs 

        1. calcula a média geral por período (ano+trimestre)
        2. soma por operadora no período
        3. marca 1/0 se ficou acima da média
        4. conta operadoras com soma >= 2

Justificativa: é simples de entender, manter e ajustar (e com índice de período/registro fica ok para esse volume).

--------------------------

Como rodar

sempre executar na mesma ordem e na pasta raiz do projeto:

1. Criar tabelas e índices

    psql -U postgres -d ans_teste -f .\teste3_sql\ddl.sql


2. Importar CSVs

    psql -U postgres -d ans_teste -f .\teste3_sql\import.sql

3. Transformar staging → tabelas finais

    psql -U postgres -d ans_teste -f .\teste3_sql\transform.sql


4. Rodar análises

psql -U postgres -d ans_teste -f .\teste3_sql\queries.sql


> Observação importante: os caminhos dos CSVs no import.sql precisam ser relativos ao local onde roda o comando (nesse caso, a partir da raiz do projeto).

-------------------------------

Teste 4 — API 

Objetivo

Disponibilzar uma API HTTP para consultar operadoras, detalhes por CNPJ, histórico de despesas e estatísticas gerais, consumindo os dados já carregados no PostgreSQL no Teste 3.


----------------

Rotas implementadas

    GET /api/operadoras

        Lista operadoras com paginação e busca.

        Parâmetros

        page (padrão: 1)
        limit (padrão: 10)
        q (opcional): busca parcial por razão social ou CNPJ

        Formato de resposta escolhido (trade-off 4.2.4)
        Opção B (dados + metadados):

        { "data": [...], "page": 1, "limit": 10, "total": 1110 }

Justificativa: facilita muito o frontend sem precisar de chamadas extras.

------------------

    GET /api/operadoras/{cnpj}

        Retorna os dados cadastrais da operadora.

        Decisão de chave

        A URL pede CNPJ (porque é o identificador comum pro usuário).
        Internamente, o relacionamento com despesas é via Registro ANS, porque a tabela de despesas (fato_despesas) está ligada pelo registro_ans.

        Então aqui:

        1. normaliza o CNPJ (fica só dígito),
        2. busca a operadora em `dim_operadoras`,
        3. retorna o cadastro.

-------------------------

    GET /api/operadoras/{cnpj}/despesas

Retorna o histórico de despesas da operadora (ordenado por ano/trimestre).

Explicação
    Converte CNPJ → encontra a operadora (em dim_operadoras) → pega registro_ans → busca em fato_despesas.

Justificativa
    Evita exigir que o usuário conheça registro_ans (que é mais “interno”), mas mantém a consistência com o banco.

---------------------------

    GET /api/estatisticas

    Retorna estatísticas agregadas:

        total_despesas (soma)
        media_despesas (média)
        top_5_operadoras (ranking por total)

-----------------------------------

Trade-offs técnicos (Backend)

Framework (4.2.1)

Escolha: FastAPI.
Justificativa: entrega rápida de API + documentação automática (/docs), validação clara de parâmetros (page/limit), e boa manutenção para rotas simples como as do teste.

Paginação (4.2.2)

    Escolha: Offset-based (offset = (page-1)*limit).
    Justificativa: volume desse teste é pequeno/médio (≈1110 operadoras), então offset é simples e suficiente. Cursor/keyset seria mais útil em volumes enormes e paginação “infinita” com muito tráfego.

Cache vs queries diretas (4.2.3)

    Escolha: **calcular na hora** (queries diretas no banco) para `/api/estatisticas`.
    Justificativa: base pequena e atualização pouco frequente no contexto do teste. Cache/precálculo só compensa quando dados mudam o tempo todo

Tipos e consistência de resposta

    Valores monetários vindos do banco retornam como float() no JSON para o frontend (prático pro consumo).
    Você normaliza CNPJ removendo pontuação na entrada pra aceitar 22.869.997/0001-53 e 22869997000153.

-------------------

Como testar rápido 

Depois de rodar o servidor, teste no navegador pelo Swagger:

1. GET /api/operadoras?page=1&limit=20`
2. GET /api/operadoras?q=22869997000153`
3. GET /api/operadoras/22869997000153`
4. GET /api/operadoras/22869997000153/despesas`
5. GET /api/estatisticas`

---------------------

Como rodar

1. Garanta que o PostgreSQL esteja rodando e que o banco ans_teste já foi populado.

2. Entre na pasta da API(onde está o main.py).

3. Ative o venv e instale dependências:

    venv\Scripts\activate
    pip install -r requirements.txt


4. Configure a conexão com o banco em database.py :

    Exemplo:
    postgresql://postgres:SENHA@localhost:5432/ans_teste

5. Suba o servidor

uvicorn main:app --reload

6. Abra no navegador:

    Documentação interativa: http://127.0.0.1:8000/docs

---------------------------------

Teste 4 — Frontend (Vue.js)

Objetivo

Criar uma interface web em Vue.js que consuma a API e entregue:

    tabela paginada de operadoras
    busca/filtro por razão social ou CNPJ
    página separada com gráfico de despesas por UF (Chart.js)
    página de detalhe da operadora com histórico de despesas

Estratégia de busca/filtro (Trade-off 4.3.1)

    Escolha: Busca no servidor (Opção A)
    A tabela consome GET /api/operadoras com q= (busca parcial) + page/limit.
  Justificativa: evita carregar todas as operadoras no browser e mantém a UI rápida mesmo se a base crescer (a API já entrega só o necessário por página).

Gerenciamento de estado (Trade-off 4.3.2)

Escolha: Props/estado local simples (Opção A)
    Cada página mantém seu próprio estado (data, page, limit, q, loading/erro).
    Justificativa: aplicação pequena, sem necessidade real de compartilhar estado global entre muitas telas.

Performance da tabela (Trade-off 4.3.3)

Escolha: Paginação no backend + renderização simples no frontend

    A tabela renderiza somente os itens da página atual.
    O usuário escolhe o “por página” (10/25/50/100).
    Justificativa: com paginação do lado do servidor, a tabela não “engasga” e mantém a experiência consistente.

Erros, loading e dados vazios (Trade-off 4.3.4)

    Loading: mensagens tipo “Carregando…” enquanto a requisição está em andamento.
    Erros de rede/API: mostra mensagem curta na tela (ex.: “Erro ao carregar operadoras.” / “Erro ao carregar dados do gráfico (UF).”) e loga o erro no console.
    Dados vazios: na tela de detalhe, se `despesas.length === 0`, mostra a mensagem “Essa operadora não tem despesas registradas...”.
    Justificativa: mensagens diretas e claras para o usuário final, sem expor detalhes internos.

Dependências / biblioteca do gráfico

    Chart.js foi usado por ser simples, popular e suficiente para o gráfico de barras por UF.
    O GraficoUF.vue consome GET /api/ufs e converte total_uf para número antes de montar o gráfico (evita problema de valores vindo como string).

Como rodar

1. Suba a API primeiro (precisa estar rodando em http://127.0.0.1:8000).
2. No diretório do frontend:

    npm install
    npm run dev
3. Abra o link que o Vite mostrar.


