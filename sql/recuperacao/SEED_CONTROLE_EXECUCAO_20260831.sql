/* =============================================================================
   RECUPERAÇÃO MANUAL — TB_CONTROLE_EXECUCAO_VOXI
   Servidor: 10.0.0.66   Banco: LOGS_ROBOS   Schema: dbo
   Data ref: 2026-08-31

   Contexto: os registros de controle do dia foram apagados por engano. Este
   script reinsere as 9 carteiras ATIVAS como CONCLUIDO hoje, para o robô não
   reenviar as cargas que já saíram.

   - Chave do dia: DATA_REF + ID_CEDENTE + CEDENTE (UNIQUE).
   - Idempotente: só insere a linha que ainda não existe (não duplica).
   - QTD_CLIENTES = 500 (placeholder; os valores reais foram perdidos).
   - ARQUIVOS = padrão CEDENTE_AAAAMMDD.csv (nome real pode divergir).
============================================================================= */

USE [LOGS_ROBOS];
GO

SET XACT_ABORT ON;
BEGIN TRANSACTION;

DECLARE @DATA_REF date = '2026-08-31';

;WITH origem (ID_CEDENTE, CEDENTE, ARQUIVOS) AS (
    SELECT 71,  'ZETA',                 'ZETA_20260831.csv'
    UNION ALL SELECT 3,  'ETA',              'ETA_20260831.csv'
    UNION ALL SELECT 99, 'BANCO TETA IMOBILIARIO', 'BANCO TETA IMOBILIARIO_20260831.csv'
    UNION ALL SELECT 81, 'BANCO BETA',             'BANCO BETA_20260831.csv'
    UNION ALL SELECT 77, 'TETA CONSUMER',          'TETA CONSUMER_20260831.csv'
    UNION ALL SELECT 84, 'TETA SWAT',              'TETA SWAT_20260831.csv'
    UNION ALL SELECT 3,  'MU',             'MU_20260831.csv'
    UNION ALL SELECT 3,  'XICLUB',              'XICLUB_20260831.csv'
    UNION ALL SELECT 14, 'NU',                'NU_20260831.csv'
)
INSERT INTO dbo.TB_CONTROLE_EXECUCAO_VOXI
    (DATA_REF, ID_CEDENTE, CEDENTE, STATUS, QTD_CLIENTES, ARQUIVOS, DT_HR_EXECUCAO)
SELECT
    @DATA_REF, o.ID_CEDENTE, o.CEDENTE, 'CONCLUIDO', 500, o.ARQUIVOS, SYSDATETIME()
FROM origem AS o
WHERE NOT EXISTS (
    SELECT 1
    FROM dbo.TB_CONTROLE_EXECUCAO_VOXI AS t
    WHERE t.DATA_REF   = @DATA_REF
      AND t.ID_CEDENTE = o.ID_CEDENTE
      AND t.CEDENTE    = o.CEDENTE
);

COMMIT TRANSACTION;
GO

-- Conferência
SELECT DATA_REF, ID_CEDENTE, CEDENTE, STATUS, QTD_CLIENTES, ARQUIVOS, DT_HR_EXECUCAO
FROM dbo.TB_CONTROLE_EXECUCAO_VOXI
WHERE DATA_REF = '2026-08-31'
ORDER BY CEDENTE;
GO
