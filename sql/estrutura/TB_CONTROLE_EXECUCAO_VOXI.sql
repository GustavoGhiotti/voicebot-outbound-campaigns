/* =============================================================================
   TB_CONTROLE_EXECUCAO_VOXI — controle diário de produção do Envio Ativo
   Servidor: 10.0.0.66   Banco: LOGS_ROBOS   Schema: dbo

   É o que permite agendar o robô de hora em hora sem enviar a mesma carteira
   duas vezes no dia. Uma linha por carteira por dia.

   Chave do dia: DATA_REF + ID_CEDENTE + CEDENTE (UNIQUE). O ID_CEDENTE (o
   SFTP) não é único — carteiras do mesmo grupo o compartilham (ex.: Mu,
   Xiclub e Eta são o cedente 3) — por isso o CEDENTE entra na chave,
   para cada parte ser registrada em separado e uma não bloquear a outra.
   Escrita somente em produção, DEPOIS do upload confirmado no SFTP e da
   gravação na DAILY_VOXI.
============================================================================= */

USE [LOGS_ROBOS];
GO

SET ANSI_NULLS ON;
GO
SET QUOTED_IDENTIFIER ON;
GO

CREATE TABLE [dbo].[TB_CONTROLE_EXECUCAO_VOXI](
    [ID_EXECUCAO]    [bigint] IDENTITY(1,1) NOT NULL,
    [DATA_REF]       [date]            NOT NULL,
    [ID_CEDENTE]     [int]             NOT NULL,   -- cedente/SFTP (bate com TB_CARTEIRA_VOXI; não é único)
    [CEDENTE]        [varchar](100)    NOT NULL,   -- nome da carteira (parte do SFTP)
    [STATUS]         [varchar](20)     NOT NULL,
    [QTD_CLIENTES]   [int]             NOT NULL,
    [ARQUIVOS]       [varchar](max)        NULL,
    [DT_HR_EXECUCAO] [datetime2](0)    NOT NULL,
 CONSTRAINT [PK_TB_CONTROLE_EXECUCAO_VOXI] PRIMARY KEY CLUSTERED
(
    [ID_EXECUCAO] ASC
) ON [PRIMARY],
 CONSTRAINT [UQ_TB_CONTROLE_EXECUCAO_VOXI_DATA_CEDENTE] UNIQUE NONCLUSTERED
(
    [DATA_REF]   ASC,
    [ID_CEDENTE] ASC,
    [CEDENTE]    ASC
) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY];
GO

ALTER TABLE [dbo].[TB_CONTROLE_EXECUCAO_VOXI]
    ADD CONSTRAINT [DF_TB_CONTROLE_EXECUCAO_VOXI_DT_HR]
    DEFAULT (sysdatetime()) FOR [DT_HR_EXECUCAO];
GO

ALTER TABLE [dbo].[TB_CONTROLE_EXECUCAO_VOXI] WITH CHECK
    ADD CONSTRAINT [CK_TB_CONTROLE_EXECUCAO_VOXI_STATUS]
    CHECK (([STATUS] = 'CONCLUIDO'));
GO

ALTER TABLE [dbo].[TB_CONTROLE_EXECUCAO_VOXI]
    CHECK CONSTRAINT [CK_TB_CONTROLE_EXECUCAO_VOXI_STATUS];
GO
