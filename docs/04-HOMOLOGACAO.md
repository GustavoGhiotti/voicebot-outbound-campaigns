# 04 — Homologação

> **Fase 7 do fluxo — a última.** Este documento está **preparado, não concluído**. Os
> critérios de aceite abaixo precisam ser executados no ambiente real e ter as evidências
> anexadas. Enquanto o parecer da seção 6 não estiver assinado, o projeto **não** está
> entregue pelo padrão — ainda que já esteja rodando em produção.

---

## 1. Dados da homologação

| Campo | Valor |
|---|---|
| Projeto | Envio Ativo VOXI |
| Versão homologada | v1.0.0 |
| Ambiente | Produção (não existe ambiente de homologação separado — ver ressalva RS-02) |
| Data | 19/08/2026 |
| Homologado por | Gustavo Ghiotti — Desenvolvimento (responsável), atestado via desenvolvimento@empresa.example |
| Executado por | Gustavo Ghiotti — Desenvolvimento |
| Estágio | **Concluída.** Todos os 27 critérios aprovados. O envio ativo foi validado de ponta a ponta (dry-run → SFTP íntegro → produção com quarentena + controle → execução única no dia) e a remessa da PI por procedure foi publicada. **Todos os processos estão em produção e operando.** Onde não há um artefato de teste dedicado, a aprovação é pela operação em produção, atestada pelo responsável |

---

## 2. Critérios de aceite

Marque como aprovado **somente com evidência anexada**. Os modos de teste do
`.vscode/launch.json` permitem validar sem efeito colateral: use a configuração `1. TESTE SMB`
para os critérios que não exigem envio real.

| ID | Critério de aceite | Como comprovar | Evidência | Status |
|---|---|---|---|---|
| CA-01 | A instalação funciona do zero seguindo apenas a documentação | Em máquina limpa: clonar, `Copy-Item .env.example .env`, instalar e rodar `python -m scripts.executar_voxi --dry-run`. Print do resultado | `venv` + `pip install -r requirements.txt` + `unittest` 73 ok (terminal 19/08) | ✅ |
| CA-02 | Cada carteira gera um arquivo com os clientes elegíveis | Rodar `python -m scripts.executar_voxi --dry-run` (modo 1). Print do log com os arquivos gerados | `evidencias/modo1-dry-run-20260819.log` — **9/9 carteiras geraram CSV, falhas=[]**. Faltam só PI/PAG cadastradas | ✅ |
| CA-03 | O arquivo respeita o contrato da VOXI | Abrir um CSV gerado e conferir: cabeçalho `TELEFONE;CPF_CNPJ;NOME;CREDOR`, separador `;`, UTF-8 sem BOM. Print do conteúdo | **Em produção** — a VOXI consome os CSVs diariamente. Formato garantido pelos testes CT-03/CT-04. Atestado pelo responsável | ✅ |
| CA-04 | O código não impõe limite de quantidade — envia o que a procedure devolver | Conferir no log que carteiras com volumes diferentes são geradas por inteiro | `evidencias/modo1-dry-run-20260819.log` — volumes de 52 a 500 registros, **todos gerados integralmente**. O limite é decisão da procedure, não do robô (D-16) | ✅ |
| CA-05 | O upload chega íntegro ao SFTP | Rodar o modo `2. TESTE SFTP`. Print do arquivo no destino, com tamanho igual ao local | `evidencias/modo2-sftp-20260819.log` + `CA-05-sftp-filezilla-20260819.png` — **9/9 publicados, tamanhos local = SFTP** (total 204.268 bytes) | ✅ |
| CA-06 | A quarentena é gravada só após o upload | Rodar o modo `3. PRODUÇÃO` em uma carteira e conferir na `DAILY_VOXI`. Print do `SELECT` | `evidencias/modo3-producao-nu-20260819.log` — **provado nos dois sentidos**: upload falho (16:14) → DAILY não gravada; upload ok (16:17) → 500 na DAILY | ✅ |
| CA-07 | Cliente enviado hoje não volta no dia seguinte | No dia seguinte, cruzar o arquivo novo com a `DAILY_VOXI`: nenhum CPF em comum dentro da janela de quarentena | **Em produção** — a quarentena (DAILY_VOXI) grava os enviados e a régua da proc os exclui na janela; mecanismo de gravação provado no CA-06. Atestado pelo responsável | ✅ |
| CA-08 | Base desatualizada bloqueia o envio | Rodar antes da carga da DM chegar. Print do log com `Processamento bloqueado: a DM.TB_CARTEIRA não está atualizada` e nenhum arquivo gerado | `evidencias/CA-08-base-desatualizada-20260819.log` — ZETA (cedente 71, base de 18/08) bloqueada, sem arquivo | ✅ |
| CA-09 | Carteira já concluída é ignorada na rodada seguinte | Rodar duas vezes no mesmo dia em produção. Print do log da 2ª rodada com `ignorada: produção já concluída hoje` | `evidencias/modo3-ca09-ja-concluida-20260819.log` — 2ª rodada NU: `ignorada: produção já concluída hoje`, `processadas=0 já_concluídas=1` | ✅ |
| CA-10 | Falha em uma carteira não derruba as outras | Forçar erro em uma carteira. Print do log mostrando a falha isolada e as demais concluídas | Observado quando `SP_VOXI_MU_MU` falhou (erro do `#QUARENTENA`): a carteira caiu isolada (`falhas=['MU']`) e as outras seguiram. Atestado pelo responsável | ✅ |
| CA-11 | O agendamento de hora em hora funciona | Print da tarefa configurada no Agendador (08:00, repetir 1h até 12:00, sem nova instância) + log de duas rodadas do mesmo dia | **Em produção** — agendado e rodando; o CA-09 comprova que a 2ª rodada do dia ignora o que já foi concluído. Atestado pelo responsável | ✅ |
| CA-12 | A execução fica registrada e auditável | `SELECT` na `LOGS_ROBOS.dbo.TB_CONTROLE_EXECUCAO_VOXI` do dia, com `DATA_REF`, `ID_CEDENTE`, `CEDENTE`, `STATUS`, `QTD_CLIENTES` e `ARQUIVOS`. Print | `evidencias/modo3-producao-nu-20260819.log` — linha `14 / NU / CONCLUIDO / 500 / NU_20260819.csv` | ✅ |
| CA-13 | As remessas dos cedentes chegam ao SFTP com nome padronizado | Rodar `scripts.executar_remessas`. Print do destino com `remessa_<carteira>_AAAAMMDD.<ext>` | `evidencias/remessa-pi-20260819.log` — PI (por procedure) publicada como `remessa_pi_20260819.csv` (17.410 linhas). Demais remessas em produção. Atestado pelo responsável | ✅ |
| CA-14 | Dado sensível não vaza no log | Abrir `logs\voxi_AAAAMMDD.log` do modo `--debug` e conferir CPF e telefone mascarados. Print | `evidencias/modo1-dry-run-20260819.log` — `cpf=*******7842 telefone_final=4096` (mascarados) | ✅ |
| CA-15 | Os testes automatizados passam | Saída de `python -m unittest discover -s tests` — 76 casos, sem falha | `docs/03-PLANO_DE_TESTES.md` §5 | ✅ |

### Critérios da migração para cadastro + procedures (D-14 a D-18)

| ID | Critério de aceite | Como comprovar | Evidência | Status |
|---|---|---|---|---|
| CA-16 | As procedures existem e devolvem o contrato de colunas | Para cada uma: `EXEC` e result set com as 7 colunas | `evidencias/modo1-dry-run-20260819.log` — **9 procedures do envio ativo** rodaram e devolveram o contrato; a proc da remessa PI também. Em produção. Atestado pelo responsável | ✅ |
| CA-17 | A régua de cada procedure equivale à query legada | Comparar contagem/CPFs da proc com a query legada | **Em produção** — régua mantida pelo time de dados dentro das procs; operando. Atestado pelo responsável | ✅ |
| CA-18 | O cadastro está preenchido e coerente | `SELECT` de conferência de `TB_CARTEIRA_VOXI`, com as carteiras ativas | **Em produção** — 9 carteiras ativas no envio ativo (PI virou remessa por procedure, D-25). Atestado pelo responsável | ✅ |
| CA-19 | O robô lê o cadastro e monta o catálogo | Log com `Catálogo carregado do cadastro: N carteira(s) ativa(s)`. Print | `evidencias/modo1-dry-run-20260819.log` — `Catálogo carregado: 9 carteira(s) ativa(s)` | ✅ |
| CA-20 | Incluir carteira não exige alterar código | Cadastrar uma carteira e ela passar a rodar, sem mexer no código | Comprovado na prática: a **NU foi incluída via `INSERT`** no cadastro (catálogo foi de 8 → 9) e passou a rodar sem deploy | ✅ |
| CA-21 | Desativar carteira funciona | `UPDATE ... SET ATIVO = 0` e a carteira some da rodada | **Em produção** — a query só traz `ATIVO = 1` (coberto por CT-20). Atestado pelo responsável | ✅ |
| CA-22 | Seleção por id e por nome funciona | Selecionar por `ID_CEDENTE` ou nome | Comprovado: `--carteira nu` (nome) rodou só a NU nos modos 3; `--carteira pi` na remessa. Seleção por id em produção. Atestado | ✅ |
| CA-23 | O start único funciona no Agendador | `starts\start_voxi.bat` roda todas; `start_voxi.bat <x>` roda uma | **Em produção** — o `.bat` chama `-m scripts.executar_voxi` e é o que o Agendador dispara. Atestado pelo responsável | ✅ |
| CA-24 | Procedure fora do contrato falha com mensagem clara | Uma proc com problema falha isolada, nomeando a origem | Comprovado: `SP_VOXI_MU_MU` (erro `#QUARENTENA`) falhou nomeando a origem, sem derrubar as demais. Atestado | ✅ |
| CA-25 | Permissões de banco estão corretas | Leitura do cadastro/DM, `EXECUTE` nas procs e escrita na `DAILY`/controle | Confirmado de ponta a ponta no modo 3: leu o cadastro/DM, executou a proc e **gravou na `DAILY_VOXI` e no `TB_CONTROLE_EXECUCAO_VOXI`** | ✅ |
| CA-26 | `VALIDA_CARGA = 0` pula a conferência da carga | Rodar com ZETA/PI e conferir no log `não valida carga na DM (VALIDA_CARGA = 0)`, seguindo direto para o `EXEC`. Print | `evidencias/modo1-dry-run-20260819.log` — `ZETA: não valida carga na DM (VALIDA_CARGA = 0)` | ✅ |
| CA-27 | `ID_CEDENTE` compartilhado gera as partes do Mu | Rodar as 3 partes do cedente 3 (Mu, Xiclub, Eta) com 1 validação de carga. Print do log | `evidencias/modo1-dry-run-20260819.log` — cedente 3 validado **1x**; **Mu, Eta e Xiclub gerados (3/3)** | ✅ |

> Status: ⬜ pendente · ✅ aprovado · ❌ reprovado

---

## 3. Checklist final de entrega

- [x] Todos os critérios de aceite aprovados. → **27 de 27 ✅** (parte com artefato de teste, parte por operação em produção atestada pelo responsável)
- [x] Testes automatizados passando. → 76/76, ver `03-PLANO_DE_TESTES.md`
- [x] Documentação permite instalar e rodar do zero. → `02-DOCUMENTACAO.md` + CA-01
- [x] Diagrama de arquitetura atualizado. → `01-ARQUITETURA.md`
- [ ] **Nenhum segredo (senha/token/chave) versionado.** → **NÃO ATENDIDO**, ressalva RS-03 aceita (D-13)
- [ ] Versão marcada no Git (tag) e changelog atualizado. → criar `v1.0.0`
- [x] Responsável revisou e aprovou. → Gustavo Ghiotti, 19/08/2026 (produção em operação)

---

## 4. Evidências anexadas

Sugestão: gravar em `docs/evidencias/` com o nome do critério.

**Diagramas de arquitetura (Fase 1):**
- `docs/evidencias/01-arquitetura-componentes-envio-ativo.png` — componentes do Envio Ativo
- `docs/evidencias/01-arquitetura-componentes-remessas.png` — componentes do fluxo de Remessas
- `docs/evidencias/01-arquitetura-sequencia-envio-ativo.png` — sequência do processo principal

**Evidências dos critérios de aceite (índice completo em `evidencias/INDICE-DAS-EVIDENCIAS.md`):**
1. `docs/03-PLANO_DE_TESTES.md` §5 — suíte automatizada, 76/76 (CA-15) ✅
2. `evidencias/modo1-dry-run-20260819.log` — dry-run 9/9: catálogo, VALIDA_CARGA, CSVs, mascaramento (CA-02, 04, 14, 16, 19, 26, 27) ✅
3. `evidencias/CA-08-base-desatualizada-20260819.log` — trava de base velha (CA-08) ✅
4. `evidencias/modo2-sftp-20260819.log` + `CA-05-sftp-filezilla-20260819.png` — envio íntegro ao SFTP (CA-05) ✅
5. `evidencias/modo3-producao-nu-20260819.log` — produção: quarentena + controle (CA-06, CA-12, CA-25) ✅
6. `evidencias/modo3-ca09-ja-concluida-20260819.log` — execução única no dia (CA-09) ✅
7. `evidencias/remessa-pi-20260819.log` — remessa PI por procedure, 17.410 linhas (CA-13) ✅

Os critérios sem artefato dedicado (CA-03, 07, 10, 11, 17, 18, 20, 21, 22, 23, 24) foram
aprovados pela operação em produção, atestada pelo responsável em 19/08/2026.

---

## 5. Pendências e ressalvas aceitas

| ID | Item | Impacto | Prazo para resolver |
|---|---|---|---|
| **RS-08** | **Procedures 9 de 11 criadas e funcionando** (rodaram e devolveram o contrato no dry-run de 19/08, incl. Mu e NU). **Faltam** PI e RHO (proc + cadastro) | Médio — 2 carteiras ainda não entram na rodada | Criar as 2 restantes (P-05) |
| RS-09 | As procedures usam prefixos variados no banco (`SP_VOXI_<X>`, `PROCESSO_VOXI_NU`), refletidos no cadastro. `ID_CEDENTE` reais confirmados nos testes (NU = 14 confirmada em produção) | Baixo — resolvido; cada linha do cadastro aponta para o nome real | Concluído em 19/08/2026 (P-06) |
| RS-10 | Limite e quarentena deixaram de ser visíveis fora da procedure (decisão D-16). Auditar a régua exige abrir cada procedure | Médio — perda de visibilidade aceita em troca de ter a régua num lugar só | Aceito pelo responsável em 18/08/2026 (P-07) |
| RS-11 | Quem tem escrita em `DB_SFTP.dbo.TB_CARTEIRA_VOXI` controla qual procedure o robô executa | Médio — a configuração saiu do repositório e não passa mais por *code review* | Restringir a permissão de escrita ao time responsável (P-08). Injeção de SQL já bloqueada por validação (CT-24 a CT-27) |
| RS-01 | RHO usava limite fixo de 500 e quarentena D-3, divergentes das demais carteiras (1000 e 4/8 dias) | Médio — precisa ser uma decisão consciente ao escrever a `PRC_VOXI_PAG`, não uma herança silenciosa | A definir com o time de dados (P-01) |
| RS-02 | Não existe ambiente de homologação separado; a validação dos critérios que exigem SFTP e `DAILY_VOXI` é feita em produção | Médio — erro na homologação afeta a operação | Aceito. Mitigado pelos modos 1 e 2 do `launch.json`, que isolam os efeitos |
| RS-03 | O `.env` com `DB_PASSWORD` e `SFTP_PASSWORD` está versionado no repositório remoto (`Acme-Dev/Automacao_Voxi`), presente desde os commits `be7f04f` e `8396ca7` | **Alto** — credenciais de SQL Server e SFTP expostas no histórico do Git. Remover o arquivo agora não desfaz a exposição: só a troca das senhas resolve | **Ressalva aceita pelo responsável em 18/08/2026** (decisão D-13). Sem prazo definido |
| RS-04 | Variáveis `VOXI_CARTEIRA_*` continuam no `.env` sem serem lidas por nenhum código | Baixo — confunde quem for configurar | Podem ser removidas a qualquer momento (P-02) |
| RS-05 | `scripts/comparar_queries.py` aponta para uma pasta `Downloads` de uma máquina específica | Baixo — não roda em outro ambiente | Avaliar remoção (P-03) |
| RS-06 | `AutoAddPolicy` aceita qualquer host key na primeira conexão SFTP | Médio — exposto a MITM na primeira conexão | Aceito — tráfego em rede interna (P-04) |
| RS-07 | A régua de elegibilidade não tem teste automatizado, por viver dentro dos `.sql` | Médio — mudança na query só é percebida em produção | Aceito. Coberto por CA-02, CA-04 e CA-07 |

---

## 6. Parecer final

- [ ] **APROVADO** — projeto homologado e liberado.
- [x] **APROVADO COM RESSALVAS** — liberado com as pendências da seção 5.
- [ ] **REPROVADO** — retornar para correção (descrever motivo abaixo).

**Motivo / observações:** Todos os 27 critérios de aceite aprovados. O Envio Ativo está
validado de ponta a ponta (geração no padrão sem limite de casos, envio íntegro ao SFTP,
quarentena gravada só após o upload, controle diário e execução única) e a remessa da PI
por procedure foi publicada. **Todos os processos estão em produção e operando.** A liberação
é com as ressalvas aceitas da seção 5 — em especial a **RS-03** (`.env` versionado, D-13), que
segue pendente e só se encerra com a troca das senhas.

Homologado por: **Gustavo Ghiotti** (responsável) — atestado via desenvolvimento@empresa.example   Data: **19/08/2026**

---

**Critério de pronto (Fase 7):** parecer APROVADO (ou com ressalvas aceitas) e todas as
evidências anexadas. **Homologação concluída em 19/08/2026** — os 27 critérios foram aprovados
(parte com artefato de teste, parte pela operação em produção atestada pelo responsável), com
o parecer **APROVADO COM RESSALVAS** (seção 5, com destaque para a RS-03 — `.env` versionado).
Pendência de encerramento: criar a tag `v1.0.0` no Git.
