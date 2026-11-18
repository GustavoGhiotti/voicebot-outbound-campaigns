# 03 — Plano de Testes

> **Fase 6 do fluxo.** Cada caso listado abaixo tem um teste automatizado correspondente em
> `tests/`. Os IDs `CT-xx` aparecem no cabeçalho de cada arquivo de teste.

---

## 1. Estratégia

Este é um robô de automação: o valor dele está em **não errar em silêncio**. Por isso os
testes se concentram nas regras cujo defeito só apareceria em produção, quando o estrago já
está feito — cliente quarentenado sem ter sido acionado, base do dia anterior enviada, ou a
mesma carteira enviada duas vezes.

Com a migração para cadastro em banco e stored procedures (agosto/2026), entrou um risco
novo: a configuração saiu do repositório e passou a ser editável por quem tem acesso ao SQL
Server. O cadastro deixou de ser revisado por *code review*. Por isso o repositório que lê a
tabela ganhou testes de validação — linha malformada precisa falhar com mensagem clara, e
não virar um `EXEC` inesperado.

- **Testes unitários:** formato do arquivo, argumentos da CLI, seleção por id e nome, e
  nomes de remessa.
- **Testes de integração (com dobras):** o fluxo `ProcessarVoxi` de ponta a ponta, a leitura
  do cadastro, a execução da procedure, a trava da DM e o controle de execução — usando fakes
  no lugar de SQL Server e SFTP.
- **Testes E2E:** não automatizados. O caminho real (cadastro → procedure → SMB → SFTP →
  `DAILY_VOXI`) é verificado na homologação, com evidências — ver `04-HOMOLOGACAO.md`.

**Nenhum teste toca em SQL Server, SMB ou SFTP real.** A suíte roda offline, em qualquer
máquina, sem `.env` configurado. As dobras estão em `tests/dobras.py`.

**Cobertura mínima acordada:** 100% das regras de negócio que o Python decide — geração do
arquivo, ordem de publicação × quarentena, leitura e validação do cadastro, contrato da
procedure, trava da DM, controle diário e argumentos da CLI. O que **não** entra nessa conta
está na seção 4.

---

## 2. Como rodar os testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Sem o `-v` a saída é resumida. Para um arquivo só:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_clientes_repository -v
```

---

## 3. Casos de teste

### Contrato do arquivo entregue à VOXI — `tests/test_csv_service.py`

| ID | O que testa | Entrada | Resultado esperado | Tipo | Status |
|---|---|---|---|---|---|
| CT-01 | Arquivo vai para a pasta do dia | 1 cliente, data 18/08/2026 | Gravado em `2026/08/18/` | Unitário | ✅ |
| CT-02 | Nome do arquivo | cedente `TETA SWAT` | `TETA_SWAT_20260818.csv` | Unitário | ✅ |
| CT-03 | Cabeçalho e separador | 1 cliente | `TELEFONE;CPF_CNPJ;NOME;CREDOR` e linha com `;` | Unitário | ✅ |
| CT-04 | Codificação e quebra de linha | nome com acento | UTF-8 **sem BOM**, sem `CRLF` | Unitário | ✅ |
| CT-05 | Um único arquivo pelo cedente | 3 clientes, cedente `MU` | 1 arquivo `MU_...csv` | Unitário | ✅ |
| CT-06 | Nenhum cliente | lista vazia | Nenhum arquivo gerado | Unitário | ✅ |
| CT-07 | Cedente com acento e símbolo | `BANCO TETA - IMOBILIÁRIO` | `BANCO_TETA_IMOBILI_RIO_20260818.csv` | Unitário | ✅ |
| CT-08 | Vazamento de dado sensível no arquivo | cliente completo | Só as 4 colunas; sem saldo nem `ID_CLIENTE` | Unitário | ✅ |

### Regra de negócio do fluxo principal — `tests/test_processar_voxi.py`

| ID | O que testa | Pré-condição | Resultado esperado | Tipo | Status |
|---|---|---|---|---|---|
| CT-09 | Caminho feliz | 2 clientes, SFTP ok | Gera, publica e grava a quarentena | Integração | ✅ |
| CT-10 | `--dry-run` | sem publisher | Gera o CSV; **não** publica e **não** grava | Integração | ✅ |
| CT-11 | `--sem-registro` | SFTP ok | Publica; **não** grava a quarentena | Integração | ✅ |
| **CT-12** | **Falha no upload** | SFTP recusa | Erro propagado e **quarentena não gravada** | Integração | ✅ |
| CT-13 | Procedure sem resultado | 0 clientes | Nada publicado, nada gravado, resultado `0` | Integração | ✅ |
| CT-14 | Envio pedido sem publisher | `enviar_sftp` sem publisher | `RuntimeError` **antes** de gravar | Integração | ✅ |
| CT-15 | Publicação de um arquivo pelo cedente | 3 clientes | 1 arquivo publicado e 3 clientes gravados | Integração | ✅ |

> **CT-12 é o caso mais importante da suíte.** Se ele quebrar, clientes passam a ser
> quarentenados sem terem sido acionados — e ficam dias fora da régua por engano.

### Cadastro `TB_CARTEIRA_VOXI` — `tests/test_carteiras_repository.py`

| ID | O que testa | Resultado esperado | Tipo | Status |
|---|---|---|---|---|
| CT-16 | Linha do cadastro vira carteira | Todos os 6 campos lidos corretamente | Integração | ✅ |
| CT-17 | Ordem de processamento | Preserva a ordem das linhas (query usa `ORDER BY CEDENTE`) | Integração | ✅ |
| CT-18 | Cedente sempre em maiúsculo | `CEDENTE` cadastrado em minúsculo chega em MAIÚSCULO | Integração | ✅ |
| CT-18b | `VALIDA_CARGA` lido do cadastro | `0` vira `False` (ZETA/PI não conferem carga); `1` vira `True` | Integração | ✅ |
| CT-19 | Espaço em branco no cadastro | `CEDENTE` chega sem espaços e em maiúsculo | Integração | ✅ |
| CT-20 | Filtro de ativas | A query traz só `ATIVO = 1`, `ORDER BY CEDENTE` | Integração | ✅ |
| CT-21 | Cadastro vazio | `RuntimeError` dizendo que não há carteira ativa | Integração | ✅ |
| CT-22 | `CEDENTE` duplicado | `RuntimeError` nomeando o cedente repetido | Integração | ✅ |
| CT-22b | `ID_CEDENTE` compartilhado | Aceito — Mu, Xiclub e Eta sobem os 3 no cedente 3 | Integração | ✅ |
| CT-23 | Sem `ID_CEDENTE` | Recusado — não haveria como validar a carga | Integração | ✅ |
| **CT-24** | **`NOME_PROC` com injeção de SQL** | Recusado antes de chegar ao `EXEC` | Integração | ✅ |
| CT-25 | `BANCO` e `SCHEMA_PROC` com injeção | Recusados | Integração | ✅ |
| CT-26 | `SERVIDOR` válido | Aceita IP, host, FQDN, instância nomeada e porta | Integração | ✅ |
| CT-27 | `SERVIDOR` com injeção | Recusado | Integração | ✅ |
| CT-28 | `CEDENTE` vazio | Recusado | Integração | ✅ |
| CT-29 | Nome qualificado da procedure | `[BANCO].[SCHEMA].[PROC]` | Unitário | ✅ |
| CT-30 | Origem legível para log | `servidor/banco.schema.proc` | Unitário | ✅ |

> **CT-24 a CT-27 existem porque o cadastro saiu do repositório.** O nome da procedure é
> interpolado na query de `EXEC`, então quem escreve na tabela poderia injetar SQL. A
> validação por regex é a barreira.

### Execução da procedure — `tests/test_clientes_repository.py`

| ID | O que testa | Resultado esperado | Tipo | Status |
|---|---|---|---|---|
| CT-31 | Comando montado | `EXEC [DB_PLANEJAMENTO].[dbo].[PRC_VOXI_ZETA];` | Integração | ✅ |
| CT-32 | Procedure sem parâmetros | Nenhum parâmetro enviado, conforme o contrato | Integração | ✅ |
| CT-33 | Conversão da linha | Vira `ClienteVoxi` com tipos corretos (`Decimal` no saldo) | Integração | ✅ |
| CT-34 | Uma conexão por carteira | 2 carteiras → 2 conexões abertas | Integração | ✅ |
| CT-35 | Procedure sem clientes | Lista vazia, sem erro | Integração | ✅ |
| CT-36 | Result sets sem retorno | `SELECT ... INTO #TEMP` é pulado | Integração | ✅ |
| CT-37 | Result set com outras colunas | Pulado; segue procurando | Integração | ✅ |
| CT-38 | Colunas extras no retorno | Aceitas | Integração | ✅ |
| CT-39 | Colunas em minúsculo | Aceitas | Integração | ✅ |
| CT-40 | Procedure fora do contrato | `RuntimeError` nomeando a procedure e as colunas exigidas | Integração | ✅ |
| CT-41 | Procedure sem nenhum retorno | `RuntimeError` | Integração | ✅ |
| **CT-42** | **Conexão da quarentena** | `DAILY_VOXI` é gravada na conexão fixa, não na da procedure | Integração | ✅ |
| CT-43 | Gravação da quarentena | `INSERT` na `DB_PLANEJAMENTO.dbo.DAILY_VOXI` com todos os clientes | Integração | ✅ |

### Trava de base desatualizada — `tests/test_validador_atualizacao.py`

| ID | O que testa | Entrada | Resultado esperado | Tipo | Status |
|---|---|---|---|---|---|
| CT-44 | Cedente por ID atualizado | cedente 60 de hoje | Passa | Integração | ✅ |
| CT-45 | Cedente por ID desatualizado | cedente 60 de ontem | `RuntimeError` citando o cedente | Integração | ✅ |
| CT-46 | Cedente inexistente na DM | nenhuma linha | `RuntimeError` | Integração | ✅ |
| CT-47 | Um cedente atrasado entre vários | 1 de hoje, 1 de ontem | Bloqueia mesmo assim | Integração | ✅ |
| CT-48 | Lista de IDs vazia | `[]` | `ValueError` | Unitário | ✅ |

### Seleção de carteiras, CLI e remessas — `tests/test_runners.py`

| ID | O que testa | Resultado esperado | Tipo | Status |
|---|---|---|---|---|
| CT-53 | `--carteira todas` | Devolve o cadastro inteiro | Unitário | ✅ |
| CT-54 | Seleção por `ID_CEDENTE` | `"71"` devolve só a carteira do cedente 71 | Unitário | ✅ |
| CT-54b | `ID_CEDENTE` compartilhado | `"3"` sobe Mu e Xiclub juntos | Unitário | ✅ |
| CT-55 | Seleção por nome do cedente | `"xiclub"`/`"rho"` sobe só aquela parte, sem diferenciar maiúsculas | Unitário | ✅ |
| CT-57 | Id/nome fora do cadastro | `ValueError` listando os disponíveis | Unitário | ✅ |
| CT-58 | Carteira desativada | Some da seleção (`ATIVO = 0` não vem na consulta) | Unitário | ✅ |
| CT-59 | Padrões da CLI | `todas`, sem nenhuma flag ligada | Unitário | ✅ |
| CT-60 | Leitura das flags | `--dry-run` e `--debug` reconhecidas | Unitário | ✅ |
| CT-61 | Código novo na CLI | Aceito pelo `argparse`; quem valida é o cadastro | Unitário | ✅ |
| **CT-62** | **`--ignorar-validacao-carga` sem carteira** | Recusado — não dá para pular a trava em todas | Unitário | ✅ |
| CT-63 | `--ignorar-validacao-carga` com carteira | Aceito | Unitário | ✅ |
| CT-65 | Remessa do dia já enviada | Reconhecida, download dispensado | Unitário | ✅ |
| CT-66 | Remessa com tipo | `parcelas` não se confunde com `remessa` | Unitário | ✅ |
| CT-67 | Remessa numerada (Nu) | `remessa_nu_01_AAAAMMDD` reconhecida | Unitário | ✅ |
| CT-68 | Remessa de outro dia | Não conta como já enviada | Unitário | ✅ |
| CT-69 | Destino vazio | Não conta como já enviada | Unitário | ✅ |
| CT-70 | PI fora do catálogo SFTP | Não está em `CARTEIRAS` (vem por procedure, não por download) | Unitário | ✅ |
| CT-71 | Cadastro das remessas | Todo cedente tem ID, protocolo válido e padrão | Unitário | ✅ |

> **CT-54, CT-54b e CT-55 cobrem as formas de selecionar.** `--carteira` casa o `ID_CEDENTE`
> (número) ou o nome do cedente (sem diferenciar maiúsculas). Um `ID_CEDENTE` compartilhado sobe
> todas as partes daquele SFTP (`3` → Mu, Xiclub e Eta); um nome sobe só aquela.

### Controle de execução única no dia — `tests/test_controle_execucao.py`

| ID | O que testa | Resultado esperado | Tipo | Status |
|---|---|---|---|---|
| CT-72 | Carteira já concluída | `concluida()` devolve `True` — rodada seguinte ignora | Integração | ✅ |
| CT-73 | Carteira ainda não concluída | `concluida()` devolve `False` | Integração | ✅ |
| CT-74 | Registro da conclusão | `commit` feito, com data, carteira, quantidade e arquivo | Integração | ✅ |
| CT-75 | Vários arquivos na mesma carteira | Nomes unidos por `;` | Integração | ✅ |
| CT-76 | Conclusão sem arquivos | Coluna `ARQUIVOS` gravada como `NULL` | Integração | ✅ |

### Remessa da PI por procedure — `tests/test_pi_remessa.py`

| ID | O que testa | Resultado esperado | Tipo | Status |
|---|---|---|---|---|
| CT-77 | CSV com todas as colunas, sem tratamento | Result set da proc vira CSV `;`; `NULL` vira campo vazio, sem perder coluna | Integração | ✅ |
| CT-78 | Ignora result sets sem retorno | Pula comandos sem colunas e usa o primeiro com dados | Integração | ✅ |
| CT-79 | Proc sem nenhum result set | `RuntimeError` nomeando a procedure | Integração | ✅ |

> Legenda: ⬜ pendente · 🟨 em execução · ✅ passou · ❌ falhou

---

## 4. Casos de erro e borda

### Cobertos

| Situação | Onde |
|---|---|
| Entrada vazia / nula | CT-06, CT-13, CT-21, CT-35, CT-48, CT-69 |
| Dependência externa falhando | CT-12 (SFTP), CT-14 (publisher ausente), CT-40 e CT-41 (procedure) |
| Configuração malformada | CT-22, CT-23, CT-28 |
| Entrada maliciosa | CT-24, CT-25, CT-27 |
| Dado fora do esperado | CT-07, CT-37, CT-38, CT-39, CT-46 |
| Duplicidade / concorrência | CT-65 a CT-69 (remessa já enviada), CT-72 e CT-73 (execução única) |
| Uso incorreto da ferramenta | CT-57, CT-62 |

### **Não** cobertos por teste automatizado — validados na homologação

| Item | Por quê | Onde é validado |
|---|---|---|
| A régua de elegibilidade (limite, quarentena, telefone) | Vive dentro das procedures, mantidas pelo time de dados | CA-02, CA-04 e CA-07 |
| Conexão real com SQL Server, SMB e SFTP | Exige credencial e rede; não pode rodar em CI | CA-01, CA-05 e CA-06 |
| A procedure existir com o nome cadastrado | Só o servidor real responde isso | CA-02 e CA-16 |
| Handshake e retentativa do `paramiko` | Comportamento de biblioteca de terceiros | CA-05 |
| Extração de ZIP das remessas | Depende do arquivo real do cedente | CA-13 |
| Comportamento sob carga (11 carteiras × 1000 clientes) | Precisa do volume real | CA-06 |

---

## 5. Evidências

Execução em **18/08/2026**, Python 3.12.10, ambiente `.venv` local:

```text
> .\.venv\Scripts\python.exe -m unittest discover -s tests

........................................................................
----------------------------------------------------------------------
Ran 76 tests in 0.116s

OK
```

---

## 6. Resultado

- **Total de casos:** 76 · **Passaram:** 76 · **Falharam:** 0
- **Cobertura:** todas as regras de negócio decididas em Python estão cobertas. A régua das
  procedures e as integrações reais ficam para a homologação, conforme a seção 4.
- **Pendências conhecidas:**
  1. As 11 procedures ainda **não existem**. Enquanto não forem criadas e cadastradas, o robô
     falha em todas as carteiras. Ver ressalva RS-01 em `04-HOMOLOGACAO.md`.
  2. O comportamento antigo da RHO (limite fixo de 500 e quarentena D-3, divergentes das
     demais) precisa ser decidido ao escrever a `PRC_VOXI_PAG`.
  3. Não há medição formal de cobertura (`coverage.py` não é dependência do projeto, para não
     instalar nada além do necessário no servidor de produção).

---

**Critério de pronto (Fase 6):** casos principais e de erro cobertos, testes passando e
cobertura mínima atingida. **Atendido** — segue para a homologação.
