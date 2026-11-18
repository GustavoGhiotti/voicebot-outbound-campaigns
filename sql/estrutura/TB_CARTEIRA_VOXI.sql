/* =============================================================================
   TB_CARTEIRA_VOXI — cadastro das carteiras do Envio Ativo VOXI
   Servidor: 10.0.0.66   Banco: DB_SFTP   Schema: dbo

   Substitui o catálogo que ficava fixo em
   src/infrastructure/config/settings.py (função obter_carteiras).

   A partir daqui, incluir ou remover uma carteira é INSERT/UPDATE nesta
   tabela. Nenhuma alteração de código Python é necessária.

   Tabela enxuta e objetiva: o que importa é a ORIGEM da procedure e saber o
   CEDENTE a partir do ID_CEDENTE.

   Regras:
   - CEDENTE é a IDENTIDADE da carteira (PK): é único, é o nome que vai no
     arquivo (o robô grava sempre em MAIÚSCULO, mesmo que aqui esteja em
     minúsculo) e aparece nos logs. Ex.: CEDENTE 'ZETA' gera ZETA_AAAAMMDD.csv.
   - ID_CEDENTE é o cedente/SFTP usado para validar a carga na DM.TB_CARTEIRA.
     NÃO é único: carteiras que compartilham o mesmo SFTP têm o mesmo id.
     Ex.: MU, XICLUB e ETA são o cedente 3 (3 procedures, 3
     arquivos, 1 SFTP só). A carga do cedente 3 é validada uma vez por rodada.
   - Cada linha aponta para UMA procedure, que devolve o result set final no
     contrato:
         TELEFONE, CPF_CNPJ, NOME, CREDOR, ID_CLIENTE, ATRASO, SALDO_DEVEDOR
   - A procedure NÃO recebe parâmetros. Limite e quarentena ficam dentro dela.
   - O robô conecta em SERVIDOR/BANCO usando DB_USER e DB_PASSWORD do .env.
============================================================================= */

USE DB_SFTP;
GO

IF OBJECT_ID('dbo.TB_CARTEIRA_VOXI', 'U') IS NOT NULL
    DROP TABLE dbo.TB_CARTEIRA_VOXI;
GO

CREATE TABLE dbo.TB_CARTEIRA_VOXI
(
    CEDENTE         VARCHAR(100)        NOT NULL,   -- IDENTIDADE (PK): nome que vai no arquivo (MAIÚSCULO)
    ID_CEDENTE      INT                 NOT NULL,   -- cedente/SFTP p/ validar a carga na DM (NÃO é único)

    -- Origem da procedure ----------------------------------------------
    SERVIDOR        VARCHAR(100)        NOT NULL,   -- ex.: 10.0.0.71
    BANCO           VARCHAR(100)        NOT NULL,   -- ex.: DB_PLANEJAMENTO
    SCHEMA_PROC     VARCHAR(100)        NOT NULL,   -- ex.: dbo
    NOME_PROC       VARCHAR(200)        NOT NULL,   -- ex.: PRC_VOXI_ZETA

    ATIVO           BIT                 NOT NULL CONSTRAINT DF_CARTEIRA_VOXI_ATIVO DEFAULT (1),
    VALIDA_CARGA    BIT                 NOT NULL CONSTRAINT DF_CARTEIRA_VOXI_VALIDA_CARGA DEFAULT (1),  -- 0 = não confere a carga na DM (ex.: ZETA, PI)

    CONSTRAINT PK_TB_CARTEIRA_VOXI PRIMARY KEY CLUSTERED (CEDENTE)
);
GO

/* -----------------------------------------------------------------------
   Carga inicial.

   >>> BANCO, SCHEMA_PROC e NOME_PROC são a convenção atual das procedures.
   Ajuste se as procedures forem criadas em outro lugar.
   >>> NU: confirmar o ID_CEDENTE real na DM (14 é o id usado no fluxo de
   remessas; os demais bateram, mas confirme antes de produção).
----------------------------------------------------------------------- */

INSERT INTO dbo.TB_CARTEIRA_VOXI
    (CEDENTE, ID_CEDENTE, SERVIDOR, BANCO, SCHEMA_PROC, NOME_PROC)
VALUES
    ('ZETA',                 71, '10.0.0.71', 'DB_PLANEJAMENTO', 'dbo', 'PRC_VOXI_ZETA'),
    ('TETA SWAT',              84, '10.0.0.71', 'DB_PLANEJAMENTO', 'dbo', 'PRC_VOXI_TETA_SWAT'),
    ('TETA CONSUMER',          77, '10.0.0.71', 'DB_PLANEJAMENTO', 'dbo', 'PRC_VOXI_TETA_CONSUMER'),
    ('BANCO BETA',             81, '10.0.0.71', 'DB_PLANEJAMENTO', 'dbo', 'PRC_VOXI_BETA'),
    ('MU',              3, '10.0.0.71', 'DB_PLANEJAMENTO', 'dbo', 'PRC_VOXI_MU_MU'),
    ('XICLUB',               3, '10.0.0.71', 'DB_PLANEJAMENTO', 'dbo', 'PRC_VOXI_MU_XICLUB'),
    ('ETA',               3, '10.0.0.71', 'DB_PLANEJAMENTO', 'dbo', 'PRC_VOXI_MU_ETA'),
    ('BANCO TETA IMOBILIARIO', 99, '10.0.0.71', 'DB_PLANEJAMENTO', 'dbo', 'PRC_VOXI_IMOBILIARIO'),
    ('NU',                14, '10.0.0.71', 'DB_PLANEJAMENTO', 'dbo', 'PRC_VOXI_NU'),   -- >>> confirmar id
    ('PI',                60, '10.0.0.71', 'DB_PLANEJAMENTO', 'dbo', 'PRC_VOXI_PI'),
    ('RHO',               43, '10.0.0.71', 'DB_PLANEJAMENTO', 'dbo', 'PRC_VOXI_PAG');
GO

-- ZETA e PI não aparecem na consulta de carga da DM.TB_CARTEIRA:
-- não confere carga para elas (são processadas normalmente).
UPDATE dbo.TB_CARTEIRA_VOXI
SET VALIDA_CARGA = 0
WHERE CEDENTE IN ('ZETA', 'PI');
GO

/* -----------------------------------------------------------------------
   Conferência — lista o cadastro. Cedentes repetidos (ex.: 3) são esperados
   para carteiras do mesmo SFTP.
----------------------------------------------------------------------- */

SELECT
     CEDENTE
    ,ID_CEDENTE
    ,PROC_COMPLETA = CONCAT(SERVIDOR, ' . ', BANCO, '.', SCHEMA_PROC, '.', NOME_PROC)
    ,ATIVO
    ,VALIDA_CARGA
    ,PARTES_NO_MESMO_SFTP = COUNT(*) OVER (PARTITION BY ID_CEDENTE)
FROM dbo.TB_CARTEIRA_VOXI
ORDER BY CEDENTE;
GO
