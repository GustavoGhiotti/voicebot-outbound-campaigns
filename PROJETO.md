# PROJETO — Manifesto do Padrão de Desenvolvimento

> **Arquivo base do Grupo Acme.** Copie este arquivo (e a pasta `docs/`) para a raiz de
> todo projeto novo. Ele descreve *como o projeto deve ser construído, documentado, testado
> e homologado*. Tanto uma pessoa quanto uma IA (como o Claude) devem ler este arquivo
> **antes de escrever qualquer código** e seguir o fluxo definido aqui.

---

## 0. Como usar este arquivo

1. Copie o kit padrão para a raiz do projeto (`PROJETO.md` + pasta `docs/`).
2. Preencha a seção **1. Identidade do Projeto** abaixo.
3. Siga o **fluxo de desenvolvimento** (seção 3), fase por fase, sem pular etapas.
4. Cada fase só é considerada concluída quando o seu **critério de pronto** for atendido.
5. Ao final, o projeto só é entregue depois de **homologado** (seção 4 e `docs/04-HOMOLOGACAO.md`).

> **Instrução para IA / assistente:** ao receber um projeto que contém este arquivo, leia-o
> por completo, confirme em qual fase o projeto está, e conduza o trabalho respeitando a
> ordem das fases e os critérios de pronto. Nunca comece pela implementação do código sem
> antes ter o diagrama (Fase 1) e a definição de estrutura e stack (Fases 2 e 3).

---

## 1. Identidade do Projeto

| Campo | Valor |
|---|---|
| **Nome do projeto** | Envio Ativo VOXI |
| **Tipo** | **Script/Automação** |
| **Responsável** | Gustavo Ghiotti — Desenvolvimento, Grupo Acme |
| **Data de início** | 29/07/2026 (primeiro commit, `KAN-257`) |
| **Objetivo (1 frase)** | Selecionar diariamente os clientes elegíveis de cada carteira, gerar um CSV por cedente e publicá-lo no SFTP da discadora VOXI, sem repetir cliente e sem enviar base desatualizada. |
| **Stakeholders** | Operação de Cobrança (consome os arquivos na VOXI) · Planejamento (mantém as queries de elegibilidade) _— confirmar_ |
| **Projeto no Jira (chave)** | `KAN` — 15 cards: KAN-257, 264 a 272, 276, 301, 302, 304, 317 |
| **Status atual** | **Todas as 7 fases concluídas** · Homologado com ressalvas em 19/08/2026 (parecer em `docs/04-HOMOLOGACAO.md`) · em produção |
| **Repositório** | https://github.com/Acme-Dev/Automacao_Voxi |
| **Versão atual** | v1.0.0 (a homologar — ver decisão D-11) |

> **Observação sobre o histórico.** O código foi construído antes da adoção do padrão
> (julho/agosto de 2026, 17 commits). As Fases 1 a 4, 6 e 7 foram preenchidas
> retroativamente a partir do código existente, em agosto de 2026.

---

## 2. Princípios

- **Nada sem diagrama.** Todo projeto começa desenhando a estrutura/fluxo antes do código.
- **Documentar enquanto se constrói**, não depois. A documentação faz parte do código.
- **Não existe "pronto" sem teste e sem homologação.** Funcionar na sua máquina não basta.
- **Padrão acima de preferência pessoal.** Um projeto do Grupo Acme deve ser reconhecível
  por qualquer pessoa da equipe.
- **Reversível e rastreável.** Tudo versionado no Git e ligado a um ticket do Jira.

---

## 3. Fluxo de Desenvolvimento (7 Fases)

O desenvolvimento segue **sempre** esta ordem. Cada fase tem um entregável e um critério de pronto.

### Fase 1 — Diagrama e Estrutura
**Objetivo:** entender o problema e desenhar a solução antes de codar.
**Entregável:** `docs/01-ARQUITETURA.md` com diagrama (Mermaid) da estrutura e do fluxo principal.
**Critério de pronto:** o diagrama mostra os componentes, como se comunicam e o fluxo de dados
de ponta a ponta; foi revisado com o responsável.

### Fase 2 — Estrutura do Código
**Objetivo:** definir a organização de pastas e arquivos.
**Entregável:** esqueleto de pastas criado no repositório, seguindo o padrão da seção 5.
**Critério de pronto:** a árvore de pastas existe e reflete o diagrama da Fase 1.

### Fase 3 — Definição de Stack e Dependências
**Objetivo:** decidir o que será utilizado (linguagem, frameworks, libs, serviços).
**Entregável:** seção "Stack" preenchida em `docs/02-DOCUMENTACAO.md` + arquivo de dependências
(`package.json`, `requirements.txt`, `.csproj`, etc.).
**Critério de pronto:** toda dependência tem uma justificativa de 1 linha; versões fixadas.

### Fase 4 — Documentação
**Objetivo:** documentar visão, como rodar e como usar, antes de a implementação avançar muito.
**Entregável:** `docs/02-DOCUMENTACAO.md` preenchido (visão geral, instalação, uso, contratos/endpoints).
**Critério de pronto:** um dev novo consegue clonar, instalar e rodar só lendo a documentação.

### Fase 5 — Código
**Objetivo:** implementar seguindo a estrutura e a documentação já definidas.
**Entregável:** código-fonte funcional na estrutura da Fase 2.
**Critério de pronto:** funcionalidades do objetivo implementadas; segue as convenções da seção 6;
sem código morto ou credenciais no repositório.

### Fase 6 — Testes
**Objetivo:** provar que o código faz o que deveria.
**Entregável:** testes automatizados + `docs/03-PLANO_DE_TESTES.md` preenchido.
**Critério de pronto:** casos principais e de erro cobertos; testes passando; cobertura mínima
acordada atingida.

### Fase 7 — Homologação
**Objetivo:** comprovar o funcionamento de forma verificável, com evidências.
**Entregável:** `docs/04-HOMOLOGACAO.md` preenchido, com checklist assinado e evidências (prints/logs).
**Critério de pronto:** todos os critérios de aceite marcados; evidências anexadas; aprovado pelo
responsável. **Só depois disso o projeto é considerado entregue.**

---

## 4. Definição de Pronto (Definition of Done)

Um projeto **só está pronto** quando **todos** os itens abaixo forem verdadeiros:

- [x] Diagrama de arquitetura existe e está atualizado. → `docs/01-ARQUITETURA.md`
- [x] Estrutura de pastas segue o padrão. → `tests/` criada em 18/08/2026
- [x] Stack e dependências documentadas e justificadas. → `docs/02-DOCUMENTACAO.md` §2; versões fixadas
- [x] Documentação permite rodar o projeto do zero. → `docs/02-DOCUMENTACAO.md` §4 + `.env.example`
- [x] Código segue as convenções. → sem credencial no código; pendências P-01 a P-04 registradas na seção 7
- [x] Testes automatizados passando. → 76 testes, `docs/03-PLANO_DE_TESTES.md`
- [x] Homologação concluída, com evidências e aprovação. → **APROVADO COM RESSALVAS em 19/08/2026**, `docs/04-HOMOLOGACAO.md`
- [ ] Ticket(s) do Jira no status concluído. → **a conferir** com o responsável
- [x] Histórico de decisões preenchido (toda troca/limitação registrada). → seção 7, D-01 a D-13
- [ ] **Nada sensível (senha, token, chave) versionado.** → **NÃO ATENDIDO.** `.env` com `DB_PASSWORD` e `SFTP_PASSWORD` está no repositório remoto. Ressalva aceita pelo responsável em 18/08/2026 (decisão D-13)

---

## 5. Padrão de Estrutura de Pastas

Estrutura mínima comum a **todos** os projetos:

```
projeto/
├── PROJETO.md              # este arquivo
├── README.md               # visão rápida e como rodar
├── docs/                   # documentação do padrão
│   ├── 01-ARQUITETURA.md
│   ├── 02-DOCUMENTACAO.md
│   ├── 03-PLANO_DE_TESTES.md
│   └── 04-HOMOLOGACAO.md
├── src/                    # código-fonte
├── tests/                  # testes automatizados
└── .gitignore
```

Variações por tipo de projeto estão detalhadas no `README.md` (seção "Estrutura por tipo").

---

## 6. Convenções

**Nomenclatura**
- Pastas e arquivos em `kebab-case` ou o padrão idiomático da linguagem (ex.: `PascalCase` para classes).
- Nada de nomes genéricos como `teste2`, `final`, `novo`.

**Git + Jira** (todo trabalho é rastreado por um ticket do Jira)
- Branch principal: `main`. **Toda branch de trabalho começa pela chave do ticket do Jira**,
  para o Jira linkar automaticamente o desenvolvimento ao card:
  `feature/KAN-0000-login`, `bugfix/KAN-0000-calculo-imposto`, `hotfix/KAN-0000-...`, `docs/KAN-0000-...`
  (a chave `KAN` é o padrão; se o projeto tiver outra chave no Jira, use a dele).
- **Todo commit começa com a chave do ticket**, assim o Jira mostra o commit dentro do card.
  Padrão (chave do ticket + Conventional Commits):
  `KAN-0000 feat: adiciona endpoint de login`, `KAN-0000 fix: corrige cálculo de imposto`,
  `KAN-0000 docs: atualiza README`.
- **Smart Commits do Jira** (opcional, muito útil): dá para comentar, apontar tempo e mover o
  card direto pela mensagem do commit —
  `KAN-0000 #comment ajuste na validação #time 2h #done`.
- **Pull Request:** o título também leva a chave do ticket (ex.: `KAN-0000 Adiciona login`) e o
  card do Jira deve ser referenciado na descrição. Só faça merge com o ticket no status correto.
- **Regra de ouro:** sem ticket do Jira, não abre branch nem faz commit — tudo tem que ficar
  visível e rastreável no card.

**Versionamento (SemVer)**
- `MAJOR.MINOR.PATCH` (ex.: `1.4.2`). Quebra de compatibilidade sobe MAJOR; nova função sobe MINOR;
  correção sobe PATCH.

**Segurança**
- Segredos em variáveis de ambiente (`.env`), **nunca** no código. `.env` sempre no `.gitignore`.
- Um `.env.example` documenta as variáveis necessárias, sem os valores reais.

---

## 7. Histórico de Decisões (obrigatório)

Registre **toda** decisão importante de arquitetura/tecnologia aqui, para não se perder o "porquê".
É **obrigatório registrar sempre que houver uma troca** — por exemplo, quando o projeto foi feito
e apresentou uma limitação (velocidade, desempenho, custo, etc.) e por isso uma tecnologia ou
abordagem foi substituída. Descreva **o que mudou, o motivo e o impacto** da mudança.

| # | Data | Decisão | Motivo / Limitação encontrada | O que substituiu | Impacto |
|---|---|---|---|---|---|
| D-01 | 29/07/2026 | Python 3.12 + `pyodbc` + `paramiko`, com `.env` e log em arquivo | Mesmo padrão já rodando em `C:\Robos\RoboCargas`; driver ODBC já homologado nos servidores | Processo manual de gerar e subir os arquivos | Envio diário deixou de depender de alguém executar à mão |
| D-02 | 29/07/2026 | Arquitetura em camadas (`domain`/`application`/`infrastructure`/`runners`) | Script único ficaria impossível de testar sem banco e SFTP reais | — | Permitiu, na Fase 6, testar todo o fluxo com dobras, sem infraestrutura |
| D-03 | 29/07/2026 | Uma query `.sql` por carteira, fora do Python | A régua de elegibilidade é mantida pelo time de dados, não pelo desenvolvimento | SQL embutido no código | Ajuste de régua não exige mexer em Python nem novo deploy |
| D-04 | 29/07/2026 | `INSERT` na `DAILY_VOXI` movido para **depois** do upload confirmado | As queries originais gravavam a quarentena antes de enviar; uma falha de SFTP "queimava" o cliente por 4 a 8 dias sem ele ter sido acionado | `INSERT` dentro da própria query | Falha de envio deixou de causar perda de base. Hoje é a regra coberta pelo CT-12 |
| D-05 | 29/07/2026 | Upload em `.part` + `rename` + conferência de tamanho | Risco de a VOXI ler um arquivo ainda incompleto | Upload direto | Eliminou o risco de processamento parcial do outro lado |
| D-06 | 29/07/2026 (KAN-257) | Validar `DT_ATUALIZACAO` da `DM.TB_CARTEIRA` antes de qualquer efeito | A carga da DM não chega em horário fixo; sem a trava o robô enviaria base do dia anterior | Confiar no horário do agendamento | Nenhum envio com base velha; a carteira fica pendente para a próxima rodada |
| D-07 | 29/07/2026 (KAN-257) | Controle diário em `LOGS_ROBOS.dbo.TB_CONTROLE_EXECUCAO_VOXI` | Com a trava do D-06 foi preciso agendar de hora em hora, o que reabriria o risco de envio duplicado | Execução única no dia por horário fixo | Permite rodar de 08:00 às 12:00 com segurança; carteira concluída é ignorada |
| D-08 | 06/08/2026 (KAN-301/302) | Troca de todas as queries de envio ativo, inclusão da RHO e fluxo de remessas lendo o FTP/SFTP do cedente com as credenciais do `RoboCargas` | Duplicar as senhas dos cedentes neste projeto criaria duas fontes de verdade | Cópia manual dos arquivos de remessa | Remessa passou a ser automática; PI ficou de fora por não ter esse fluxo |
| D-09 | 06/08/2026 (KAN-304) | Troca da query da RHO | A query anterior retornava poucos casos | Query antiga da RHO | Volume de acionamento da carteira normalizado |
| D-10 | KAN-317 (11/08/2026) | Limite subiu de 500 para **1000 por cedente**; carteira com 0 casos não é marcada como concluída | 500 casos não sustentavam a operação; e uma consulta vazia estava sendo registrada como concluída, impedindo nova tentativa no mesmo dia | Limite de 500 e registro incondicional | Dobrou o volume diário; consulta vazia volta a ser tentada na rodada seguinte |
| D-11 | 18/08/2026 | Adoção do Padrão Grupo Acme retroativamente; versão marcada como **v1.0.0** | O projeto já estava em produção sem diagrama, documentação, testes nem homologação | `PROJETO.md` e `docs/` em branco | Fases 1 a 6 concluídas: 53 testes automatizados criados, `.env.example` e documentação de instalação do zero |
| D-12 | 18/08/2026 | `paramiko` fixado em `4.0.0` | Estava como `>=4,<5`, o que permitia build diferente a cada instalação | Faixa aberta de versão | Instalação reprodutível, como exige a Fase 3 |
| D-13 | 18/08/2026 | **Manter o `.env` versionado**, sem reescrever o histórico do Git | Decisão do responsável em 18/08/2026, ciente de que `DB_PASSWORD` e `SFTP_PASSWORD` estão expostos no repositório remoto | — | **Item da Definição de Pronto não atendido.** Registrado como ressalva na seção 5 de `docs/04-HOMOLOGACAO.md` |
| D-14 | 18/08/2026 | **Queries `.sql` do repositório substituídas por stored procedures**, endereçadas por cadastro | A régua das carteiras foi trocada 3 vezes em 2 meses (KAN-301, KAN-304, KAN-317). Cada troca exigia editar arquivo no repositório, commitar e publicar no servidor — trabalho manual repetido para uma mudança que é do time de dados, não do desenvolvimento | `sql/carteiras/*.sql` executados com 4 parâmetros | Trocar a régua virou `ALTER PROCEDURE`, sem deploy. O robô pega a versão nova na rodada seguinte |
| D-15 | 18/08/2026 | **Catálogo de carteiras movido para `DB_SFTP.dbo.TB_CARTEIRA_VOXI`** (servidor `.66`), com `SERVIDOR`, `BANCO`, `SCHEMA_PROC`, `NOME_PROC`, `CREDOR`, `ID_CEDENTE` e `GRUPO` | Incluir uma carteira exigia 4 alterações de código: catálogo no `settings.py`, arquivo `.sql`, módulo em `scripts/` e `.bat` em `starts/` | Catálogo fixo em `src/infrastructure/config/settings.py` | Incluir carteira virou um `INSERT`. Foram removidos 12 módulos Python e o `comparar_queries.py`; os 11 `.bat` passaram a chamar `main.py --carteira <codigo>`, preservando o Agendador de Tarefas |
| D-16 | 18/08/2026 | **Procedure chamada sem parâmetro nenhum** | Decisão do responsável: limite e quarentena passam a viver dentro da procedure, junto do resto da régua | `@FILTRO_CARTEIRA`, `@CREDOR`, `@LIMITE`, `@DIAS_QUARENTENA` | Régua concentrada em um lugar só. Em troca, limite e quarentena deixaram de ser visíveis a partir do Python e da tabela — só lendo a procedure |
| D-17 | 18/08/2026 | Robô procura, entre os result sets da procedure, o **primeiro que cumpra o contrato de colunas** | Procedure costuma emitir result sets intermediários; assumir posição fixa quebraria em silêncio, entregando o arquivo errado | Ler o primeiro result set com retorno | Erro passa a ser explícito, nomeando a procedure e as colunas exigidas |
| D-18 | 18/08/2026 | Identificadores vindos do cadastro são **validados por regex** antes do `EXEC` | O nome da procedure é interpolado na query. Com o catálogo fora do repositório, ele deixou de passar por *code review* | Confiar no conteúdo da tabela | Fecha um caminho de injeção de SQL para quem tem escrita na tabela. Coberto por CT-24 a CT-27 |
| D-25 | 19/08/2026 | **Remessa da PI gerada por procedure**, e não por download de SFTP como as demais. Roda `EXEC DB_PLANEJAMENTO.[Raw].[BASE_VOXI_PI]` no `.71`; o result set inteiro vira `remessa_pi_AAAAMMDD.csv` (todas as colunas, sem tratamento; `;` + UTF-8) e é publicado na pasta `REMESSA` do SFTP VOXI. A proc fica **fixa no código** (não no cadastro) | A PI não tem arquivo de origem em SFTP; a base vem de uma consulta. É um caso único, diferente do envio ativo (que é cadastrado) e das demais remessas (que baixam arquivo) | PI fora do fluxo de remessas | Novo módulo `pi_remessa_repository.py` + ramo no `runners/remessas.py` (`--carteira pi`). Formato do CSV (`;`/UTF-8) a confirmar com a VOXI. Testes CT-77 a CT-79 |
| D-24 | 19/08/2026 | **Publicação no SFTP passa a sobrescrever o destino** (`posix_rename` com fallback para remover+renomear), no lugar do `sftp.rename` puro | Achado na homologação: reenviar a mesma carteira no mesmo dia estourava `OSError: Failure` no `rename`, porque o SFTP não sobrescreve destino existente. Em produção (rodada de hora em hora), um envio que sobe o arquivo mas falha antes de concluir travaria a carteira nas rodadas seguintes | `sftp.rename(temporario, remoto)` — falha se o destino já existe | Reenvio no mesmo dia funciona; a troca continua atômica no OpenSSH (sem janela de arquivo pela metade). `src/infrastructure/sftp/sftp_publisher.py` |
| D-23 | 19/08/2026 | **Coluna `VALIDA_CARGA` no cadastro** (BIT, default 1). Com `VALIDA_CARGA = 0`, o robô pula a validação da carga na `DM.TB_CARTEIRA` para aquela carteira e a processa direto. ZETA e PI entram com 0 | ZETA e PI não aparecem na consulta de carga da `DM.TB_CARTEIRA`; validá-las bloquearia a carteira todo dia. A exceção precisava viver no cadastro, não hard-coded no Python (princípio do D-15) | Validar todas as carteiras contra a DM | Exceção vira dado, não código. A validação da carga (`ValidadorAtualizacaoCarteira.validar_cedentes`) e a gravação na `DAILY_VOXI` (`registrar_processados`) seguem existindo — só a validação passa a ser condicional por carteira. Testes 72 → 73 |
| D-22 | 19/08/2026 | **Entrada do envio ativo em `scripts/executar_voxi.py`**, removendo o `main.py` da raiz. O envio ativo passa a ter um script de entrada simétrico ao `scripts/executar_remessas.py` do fluxo de remessas (`python -m scripts.executar_voxi`); o `__main__` vive no wrapper, não no runner | O `main.py` era um atalho de 3 linhas na raiz, e o envio ativo não tinha um `executar_*` em `scripts/` como o remessas — os dois fluxos ficavam assimétricos | `main.py` na raiz como ponto de entrada | `start_voxi.bat` e as 4 configs do `.vscode/launch.json` apontam para `scripts/executar_voxi.py`; documentação atualizada. Sem `main.py` na raiz |
| D-21 | 19/08/2026 | **Correção do D-20: a identidade é o `CEDENTE`, não o `ID_CEDENTE`.** `CEDENTE` (nome) vira a PK do cadastro; `ID_CEDENTE` continua obrigatório mas **deixa de ser único**. O controle diário passa a chavear por `DATA_REF` + `ID_CEDENTE` + `CEDENTE`, e a validação da carga na DM roda **uma vez por `ID_CEDENTE`** na rodada | Ao popular o cadastro, descobriu-se que MU, XICLUB e ETA são **3 carteiras (3 procedures, 3 arquivos) do mesmo SFTP/cedente = 3**. Com `ID_CEDENTE` como PK, as 3 colidiam (`Violação da PRIMARY KEY ... valor (3)`); e no controle, uma parte marcaria a outra como concluída | `ID_CEDENTE` como PK/identidade e chave única do controle (D-20) | Um `ID_CEDENTE` compartilhado é aceito; cada parte é rastreada pelo nome. `--carteira 3` sobe as 3 partes do Mu; `--carteira xiclub` sobe só ela. A carga do cedente 3 é validada uma vez, não 3. Testes 70 → 72 |
| D-20 | 19/08/2026 | **Enxugamento da `TB_CARTEIRA_VOXI` para o essencial**: `ID_CEDENTE`, `CEDENTE`, `SERVIDOR`, `BANCO`, `SCHEMA_PROC`, `NOME_PROC`, `ATIVO`. `ID_CEDENTE` vira a chave (PK/identidade) e a única forma de validar a carga; `CEDENTE` (normalizado em MAIÚSCULO) passa a nomear o arquivo. O controle diário passa a chavear por `ID_CEDENTE`, guardando o `CEDENTE` só para leitura | A tabela tinha coluna demais para um cadastro que é objetivo: bastam a origem da procedure e o cedente. `CODIGO` duplicava a identidade que o `ID_CEDENTE` já dá; `GRUPO` e `CREDOR` eram o mesmo conceito de nome; `FILTRO_DM` só existia para validar quem não tinha `ID_CEDENTE`; `ORDEM` não tem prioridade real (basta alfabética); `OBSERVACAO` não era usada | `CODIGO`, `GRUPO`, `FILTRO_DM`, `ORDEM`, `OBSERVACAO` e o surrogate `ID` | Cadastro mais simples de manter. Em troca: (a) a validação da carga é sempre por cedente — o método `validar()` por texto virou código morto e foi removido; (b) `--carteira` seleciona por `ID_CEDENTE` ou nome do cedente, e o grupo `mu` deixou de existir como seleção conjunta (cada cedente roda sozinho na rodada diária de qualquer forma); (c) o nome do arquivo passou a vir do cadastro, não da coluna `CREDOR` da procedure; (d) as 9 carteiras que validavam por `FILTRO_DM` precisam do `ID_CEDENTE` real da DM (ver P-06); (e) a `TB_CONTROLE_EXECUCAO_VOXI`, que já existia com a coluna `CARTEIRA`, foi migrada para `ID_CEDENTE` + `CEDENTE` (backup do conteúdo antigo + recriação no schema novo, em 19/08/2026). Testes 75 → 70 |
| D-19 | 18/08/2026 | **Consolidação em um único `.bat`**: `starts/start_voxi.bat` roda todas as carteiras e aceita um código como atalho (`start_voxi.bat zeta` = `main.py --carteira zeta`) | Depois do D-15, com o catálogo na tabela, os 11 `.bat` por carteira viraram redundantes: o start único já cobre todas, e a rodada por carteira é só um argumento. Manter 11 arquivos quase idênticos + um `start_todos.bat` duplicado era manutenção sem retorno | Os 11 `starts/start_<carteira>.bat` chamando `main.py --carteira <codigo>` + `start_todos.bat` (duplicado de `start_voxi.bat`) | Removidos os 11 `.bat` por carteira e o `start_todos.bat`; sobraram `start_voxi.bat` e `start_remessas.bat`. Também foram removidos o `scripts/executar_voxi.py`, que ficou órfão, e o mecanismo `carteira_padrao` do runner (1 teste a menos: 76 → 75). **Ação necessária:** reapontar a tarefa do Agendador de `start_todos.bat` para `start_voxi.bat` |

### Pendências técnicas identificadas na adoção do padrão

| # | Pendência | Onde | Situação |
|---|---|---|---|
| **P-05** | **As 11 stored procedures ainda não existem.** Enquanto não forem criadas e cadastradas, o robô falha em todas as carteiras | servidor de banco | **Aberta — bloqueia a produção.** Fonte para escrevê-las: `sql/carteiras/*.sql` |
| P-06 | O seed de `TB_CARTEIRA_VOXI` já traz os `ID_CEDENTE` reais (ZETA 71, TETA SWAT 84, TETA CONSUMER 77, BETA 81, Mu/Xiclub/Eta 3, IMOB 99, PI 60, RHO 43). Pendente: **confirmar o `ID_CEDENTE` da NU** (seed usa 14, o id do fluxo de remessas — confirmar na `DM.TB_CARTEIRA`). `BANCO`/`SCHEMA_PROC`/`NOME_PROC` seguem a convenção `PRC_VOXI_<X>`; ajustar se as procedures forem criadas em outro lugar | `sql/estrutura/TB_CARTEIRA_VOXI.sql` | Quase resolvida — só a NU a confirmar |
| P-07 | Limite e quarentena deixaram de ser visíveis fora da procedure (decisão D-16). Não há como auditar a régua sem abrir cada procedure | procedures | Aceita — consequência conhecida da decisão |
| P-01 | RHO usava limite fixo de 500 e quarentena D-3, divergentes das demais carteiras | `sql/carteiras/pag.sql` | Aberta — decidir ao escrever a `PRC_VOXI_PAG` |
| P-02 | Variáveis `VOXI_CARTEIRA_*` continuam no `.env` mas não são lidas por nenhum código | `.env` | Documentada como obsoleta; pode ser removida |
| ~~P-03~~ | `scripts/comparar_queries.py` apontava para uma pasta em `Downloads` e quebrou com a migração | — | **Resolvida** em 18/08/2026 — arquivo removido (recuperável pelo Git) |
| P-04 | `AutoAddPolicy` aceita qualquer host key na primeira conexão SFTP | `sftp_publisher.py`, `remessa_source.py` | Aceita — rede interna |
| P-08 | Escrita em `TB_CARTEIRA_VOXI` passa a definir qual procedure o robô executa | `DB_SFTP` no `.66` | Aberta — restringir a permissão de escrita ao time responsável |
| ~~P-09~~ | `scripts/executar_voxi.py` ficou órfão após a consolidação do `.bat` (D-19) | `scripts/executar_voxi.py` | **Resolvida** em 18/08/2026 — arquivo removido junto do mecanismo `carteira_padrao` do runner e do teste CT-64 (recuperável pelo Git) |

---

_Padrão Grupo Acme · v1.0 · mantido pela equipe de Desenvolvimento._
