# 02 — Documentação Técnica

> **Fases 3 e 4 do fluxo.** Se você é novo no projeto, este documento sozinho deve bastar
> para clonar, instalar, configurar e rodar. Se em algum ponto você precisou perguntar algo,
> o documento está incompleto — corrija-o.

---

## 1. Visão geral

A VOXI é a discadora usada pela operação de cobrança do Grupo Acme. Todo dia útil ela
precisa receber duas coisas: a **lista de clientes que devem ser acionados hoje** (envio
ativo) e a **remessa bruta que o cedente enviou** (base cadastral). Antes deste projeto, as
duas coisas eram feitas na mão, com risco de discar a mesma pessoa dias seguidos, de mandar
base do dia anterior ou de esquecer uma carteira.

Este robô automatiza os dois processos. No **envio ativo**, ele executa uma consulta por
carteira no `DB_REPORT`, monta um CSV por cedente no formato que a VOXI espera
(`TELEFONE;CPF_CNPJ;NOME;CREDOR`), publica no SFTP e só então grava a quarentena na
`DAILY_VOXI` — o que impede o mesmo cliente de ser acionado de novo por 4 ou 8 dias. No
**envio de remessas**, ele lê o FTP/SFTP de cada cedente, descompacta o que vier zipado e
republica no SFTP da VOXI com nome padronizado.

Três travas sustentam a operação: nada é processado se a `DM.TB_CARTEIRA` não estiver
atualizada com a data de hoje; nada é gravado na quarentena antes do upload dar certo; e uma
carteira já concluída no dia é ignorada nas rodadas seguintes. Isso permite agendar o robô de
hora em hora sem risco de duplicidade.

**O que este projeto NÃO faz:** não define a régua de cobrança (quem é elegível está nas
queries em `sql/carteiras/`, mantidas pelo time de dados); não disca; não trata retorno da
VOXI; não gera relatório gerencial. A PI participa das remessas de forma diferente: em vez
de baixar de um SFTP, roda uma procedure e o result set vira o CSV (ver seção 6).

---

## 2. Stack e dependências

| Camada | Tecnologia | Versão | Por que foi escolhida |
|---|---|---|---|
| Linguagem | Python | 3.12 | Padrão dos robôs do Grupo Acme; `dataclasses` com `slots` e tipagem nativa |
| Banco de dados | SQL Server | 2019 | Onde já vivem `DB_REPORT`, `DB_PLANEJAMENTO` e `LOGS_ROBOS` |
| Driver ODBC | ODBC Driver 17 for SQL Server | 17 | Já instalado e homologado nos servidores de robô |
| Biblioteca — banco | `pyodbc` | 5.2.0 | Acesso direto ao SQL Server, mesmo padrão do `RoboCargas`; sem ORM porque as consultas são SQL puro mantido por terceiros |
| Biblioteca — transferência | `paramiko` | 4.0.0 | Cliente SSH/SFTP ativo e mantido, e também fala com os SFTPs dos cedentes |
| Biblioteca — configuração | `python-dotenv` | 1.1.0 | Carrega o `.env` local e o `.env` do `RoboCargas` sem código próprio de parsing |
| FTP | `ftplib` (padrão) | — | Só o Mu usa FTP simples; não justifica dependência externa |
| ZIP | `zipfile` (padrão) | — | Remessas do TETA e do BETA chegam zipadas |
| Testes | `unittest` (padrão) | — | Já vem com o Python; evita instalar pytest no servidor de produção |
| Serviço externo | SFTP da VOXI | — | Canal de integração definido pela discadora |
| Serviço externo | FTP/SFTP dos cedentes | — | Origem das remessas; credenciais vêm do `RoboCargas` |
| Agendamento | Agendador de Tarefas do Windows | — | Padrão dos robôs; dispara os `.bat` de `starts/` |

Versões fixadas em [requirements.txt](../requirements.txt). As bibliotecas indiretas
(`cryptography`, `bcrypt`, `PyNaCl`) vêm como dependência do `paramiko` e não são declaradas.

---

## 3. Pré-requisitos

- Windows Server ou Windows 11 com **Python 3.12+**
- **ODBC Driver 17 for SQL Server** instalado
- Acesso de rede (VPN ou rede interna) a:
  - `10.0.0.71` — SQL Server e compartilhamento SMB `\\10.0.0.71\d\Automacao\VOXI`
  - `10.0.0.66` — SQL Server `LOGS_ROBOS` e `DB_DESENVOLVIMENTO`
  - host do SFTP da VOXI (porta 22)
- Usuário do SQL Server com:
  - leitura em `DB_SFTP.dbo.TB_CARTEIRA_VOXI` (cadastro das carteiras)
  - `EXECUTE` nas procedures cadastradas, em cada servidor/banco que a tabela apontar
  - leitura em `DB_REPORT.DM.TB_CARTEIRA` (validação da carga)
  - escrita em `DB_PLANEJAMENTO.dbo.DAILY_VOXI` e em
    `LOGS_ROBOS.dbo.TB_CONTROLE_EXECUCAO_VOXI`
- Credenciais do SFTP da VOXI (senha **ou** arquivo de chave RSA)
- **Somente para o fluxo de remessas:** a pasta `C:\Robos\RoboCargas` presente na máquina,
  com o `.env` e a subpasta `senhas` (chaves privadas dos cedentes)

---

## 4. Instalação

```powershell
# 1. Clonar
git clone https://github.com/Acme-Dev/Automacao_Voxi.git
cd Automacao_Voxi

# 2. Configurar variáveis de ambiente
Copy-Item .env.example .env
# edite o .env com os valores reais (ver seção 5)

# 3. Criar o ambiente virtual e instalar as dependências
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 4. Validar sem escrever em lugar nenhum
.\.venv\Scripts\python.exe -m scripts.executar_voxi --dry-run --debug

# 5. Rodar os testes
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

O passo 4 consulta o banco de verdade e gera os CSVs, mas **não** envia ao SFTP e **não**
grava na `DAILY_VOXI`. É a forma segura de validar a instalação.

---

## 5. Variáveis de ambiente

### Envio Ativo (fluxo principal)

| Variável | Descrição | Obrigatória | Padrão / Exemplo |
|---|---|---|---|
| `DB_HOST` | Servidor SQL de origem dos clientes | **Sim** | `10.0.0.71` |
| `DB_NAME` | Banco de origem | Não | `DB_REPORT` |
| `DB_USER` | Usuário do SQL Server | **Sim** | — |
| `DB_PASSWORD` | Senha do SQL Server | **Sim** | — |
| `DB_DRIVER` | Driver ODBC | Não | `ODBC Driver 17 for SQL Server` |
| `LOGS_DB_HOST` | Servidor do controle diário de execução | Não | `10.0.0.66` |
| `LOGS_DB_NAME` | Banco do controle diário | Não | `LOGS_ROBOS` |
| `CADASTRO_DB_HOST` | Servidor do cadastro `TB_CARTEIRA_VOXI` | Não | `10.0.0.66` |
| `CADASTRO_DB_NAME` | Banco do cadastro | Não | `DB_SFTP` |
| `SFTP_HOST` | Host do SFTP da VOXI | **Sim** | — |
| `SFTP_PORT` | Porta do SFTP | Não | `22` |
| `SFTP_USER` | Usuário do SFTP | **Sim** | — |
| `SFTP_PASSWORD` | Senha do SFTP | Condicional | usar esta **ou** `SFTP_KEY_FILE` |
| `SFTP_KEY_FILE` | Caminho da chave privada RSA | Condicional | usar esta **ou** `SFTP_PASSWORD` |
| `SFTP_REMOTE_DIR` | Diretório raiz no SFTP | Não | `/entrada` |
| `VOXI_OUTPUT_DIR` | Onde os CSVs são gravados | Não | `\\10.0.0.71\d\Automacao\VOXI` |

### Envio de Remessas (fluxo secundário)

| Variável | Descrição | Obrigatória | Padrão |
|---|---|---|---|
| `ROBO_CARGAS_ROOT` | Raiz do RoboCargas (`.env` complementar e pasta `senhas`) | Não | `C:\Robos\RoboCargas` |
| `CARGAS_DB_HOST` | Servidor com o cadastro `Carga.TB_CONEXAO_SFTP` | Não | `DB_66`, senão `10.0.0.66` |
| `CARGAS_DB_NAME` | Banco do cadastro de conexões | Não | `DB_DESENVOLVIMENTO` |
| `CARGAS_DB_USER` | Usuário desse banco | Não | cai para `DB_USER` |
| `CARGAS_DB_PASSWORD` | Senha desse banco | Não | cai para `DB_SENHA`, senão `DB_PASSWORD` |
| `CARGAS_DB_DRIVER` | Driver ODBC desse banco | Não | `SQL Server` |

> **Atenção:** o `settings.py` carrega **dois** arquivos `.env` — primeiro o do projeto,
> depois o de `ROBO_CARGAS_ROOT`. O segundo **não sobrescreve** valores já definidos.

> **Obsoleto:** as variáveis `VOXI_CARTEIRA_ZETA`, `VOXI_CARTEIRA_TETA`, `VOXI_CARTEIRA_BETA`,
> `VOXI_CARTEIRA_MU`, `VOXI_CARTEIRA_IMOB` e `VOXI_CARTEIRA_NU` ainda aparecem em
> `.env` antigos, mas **não são lidas por nenhum código**. A validação da carga passou a ser
> feita pelo `ID_CEDENTE` da linha em `TB_CARTEIRA_VOXI`. Pode apagá-las.

---

## 6. Como usar

### Envio Ativo

```powershell
# Todas as carteiras (o que o agendamento executa)
.\.venv\Scripts\python.exe -m scripts.executar_voxi

# Uma carteira específica
.\.venv\Scripts\python.exe -m scripts.executar_voxi --carteira zeta

# Simulação: consulta e gera CSV, sem SFTP e sem DAILY_VOXI
.\.venv\Scripts\python.exe -m scripts.executar_voxi --dry-run

# Envia ao SFTP mas não grava a quarentena
.\.venv\Scripts\python.exe -m scripts.executar_voxi --sem-registro

# Ignora a trava de carga desatualizada (exige --carteira específica)
.\.venv\Scripts\python.exe -m scripts.executar_voxi --carteira zeta --ignorar-validacao-carga
```

Não existe mais um módulo Python nem um `.bat` por carteira. O start único
`starts\start_voxi.bat` roda todas as carteiras; passando um código
(`start_voxi.bat zeta`) ele chama `-m scripts.executar_voxi --carteira <id_cedente|nome>`, e o valor
aceito é qualquer `ID_CEDENTE` ou `CEDENTE` cadastrado e ativo em `TB_CARTEIRA_VOXI`.

### Envio de Remessas

```powershell
python -m scripts.executar_remessas --dry-run
python -m scripts.executar_remessas --carteira beta
python -m scripts.executar_remessas
```

### Argumentos da linha de comando

| Argumento | Efeito |
|---|---|
| `--carteira <id_cedente\|nome>` | Processa a carteira cujo `ID_CEDENTE` ou nome do cedente for informado. Um `ID_CEDENTE` compartilhado sobe todas as partes (`3` → Mu+Xiclub+Eta); um nome sobe só aquela. Padrão: `todas`. Validado contra `TB_CARTEIRA_VOXI` na execução |
| `--dry-run` | Consulta e gera o CSV, mas não envia ao SFTP nem grava na `DAILY_VOXI` |
| `--sem-registro` | Envia ao SFTP, mas não grava na `DAILY_VOXI` |
| `--ignorar-validacao-carga` | Pula a validação de `DT_ATUALIZACAO` da DM. Exige `--carteira` específica |
| `--debug` | Log em nível DEBUG, com amostras de dados mascaradas |

### Códigos de saída

| Código | Significado |
|---|---|
| `0` | Rodada concluída sem falhas (carteiras pendentes ou já concluídas não são falha) |
| `1` | Pelo menos uma carteira falhou, ou houve erro geral na execução |

### Cadastro de carteiras — `DB_SFTP.dbo.TB_CARTEIRA_VOXI`

A lista de carteiras **não fica mais no código**. Ela é lida desta tabela no início de cada
execução. DDL e carga inicial em
[`sql/estrutura/TB_CARTEIRA_VOXI.sql`](../sql/estrutura/TB_CARTEIRA_VOXI.sql).

| Coluna | Para quê |
|---|---|
| `CEDENTE` (PK) | Identidade da carteira: nome que vai no arquivo (o robô grava sempre em MAIÚSCULO) e nos logs. Aceito em `--carteira` |
| `ID_CEDENTE` | Cedente/SFTP que valida a carga da DM. **Não é único**: carteiras do mesmo SFTP têm o mesmo id (ex.: Mu, Xiclub e Eta = 3). Também aceito em `--carteira` — e aí sobe todas as partes daquele id |
| `SERVIDOR`, `BANCO`, `SCHEMA_PROC`, `NOME_PROC` | Onde está a procedure da carteira |
| `ATIVO` | `0` tira a carteira da execução sem apagar a linha |
| `VALIDA_CARGA` | `0` = o robô **não** confere a carga na `DM.TB_CARTEIRA` para esta carteira (usado por ZETA e PI, que não aparecem naquela consulta). A carteira é processada normalmente |

> A ordem de processamento é alfabética por `CEDENTE` — não há prioridade de envio. Não existem
> mais as colunas `CODIGO`, `GRUPO`, `FILTRO_DM`, `ORDEM` nem `OBSERVACAO` (ver D-20 e D-21).

### Como incluir uma carteira nova

1. Criar a procedure no servidor/banco desejado, cumprindo o contrato de colunas abaixo.
2. Inserir uma linha em `TB_CARTEIRA_VOXI` apontando para ela.

Nenhum passo exige alterar código Python, criar `.bat` nem publicar versão nova: o start único
já processa toda carteira ativa, e `start_voxi.bat <id_cedente|nome>` reprocessa a nova isoladamente.

### Contrato que a procedure precisa cumprir

- Chamada **sem parâmetros** (`EXEC [BANCO].[SCHEMA].[PROC]`).
- Limite de casos, dias de quarentena e regra de telefone ficam **dentro da procedure**.
- Deve devolver um result set com, no mínimo, estas colunas:

```sql
TELEFONE, CPF_CNPJ, NOME, CREDOR, ID_CLIENTE, ATRASO, SALDO_DEVEDOR
```

- Result sets intermediários são ignorados: o robô procura o primeiro que tenha todas as
  colunas acima. Colunas extras são aceitas. Maiúsculas/minúsculas não importam.
- A procedure **não** deve inserir na `DAILY_VOXI`. Quem grava a quarentena é o robô, e só
  depois do upload confirmado.
- Recomenda-se `SET NOCOUNT ON;` na primeira linha.

### Carteiras cadastradas hoje

| `CEDENTE` | `ID_CEDENTE` | Arquivo gerado |
|---|---|---|
| `ZETA` | `71` | `ZETA_AAAAMMDD.csv` |
| `TETA SWAT` | `84` | `TETA_SWAT_AAAAMMDD.csv` |
| `TETA CONSUMER` | `77` | `TETA_CONSUMER_AAAAMMDD.csv` |
| `BANCO BETA` | `81` | `BANCO_BETA_AAAAMMDD.csv` |
| `MU` | `3` | `MU_AAAAMMDD.csv` |
| `XICLUB` | `3` | `XICLUB_AAAAMMDD.csv` |
| `ETA` | `3` | `ETA_AAAAMMDD.csv` |
| `BANCO TETA IMOBILIARIO` | `99` | `BANCO_TETA_IMOBILIARIO_AAAAMMDD.csv` |
| `NU` | `14` *(confirmar)* | `NU_AAAAMMDD.csv` |
| `PI` | `60` | `PI_AAAAMMDD.csv` |
| `RHO` | `43` | `RHO_AAAAMMDD.csv` |

`MU`, `XICLUB` e `ETA` compartilham o cedente `3` (mesmo SFTP): 3 procedures e 3
arquivos, uma validação de carga só. A validação é sempre pelo `ID_CEDENTE` na `DM.TB_CARTEIRA`;
falta confirmar o id da NU (ver P-06). O limite e a quarentena de cada carteira vivem dentro
da respectiva procedure — não são visíveis a partir do Python nem da tabela.

### Saídas produzidas

| Saída | Caminho | Formato |
|---|---|---|
| CSV local | `<VOXI_OUTPUT_DIR>\AAAA\MM\DD\<CEDENTE>_AAAAMMDD.csv` | UTF-8 sem BOM, separador `;`, cabeçalho `TELEFONE;CPF_CNPJ;NOME;CREDOR` |
| CSV no SFTP | `<SFTP_REMOTE_DIR>/ENVIOS_ATIVOS/AAAA/MM/DD/` | idem |
| Remessa no SFTP | `<SFTP_REMOTE_DIR>/REMESSA/AAAA/MM/DD/remessa_<carteira>[_<tipo>]_AAAAMMDD.<ext>` | conteúdo original do cedente |
| Log | `logs\voxi_AAAAMMDD.log` e `logs\remessas_AAAAMMDD.log` | texto; CPF e telefone mascarados |

---

## 7. Estrutura de pastas do projeto

```text
Envio Ativo VOXI/
├── requirements.txt            dependências com versão fixada
├── .env.example                modelo de configuração (versionado, sem valores)
├── PROJETO.md                  manifesto do padrão + identidade e decisões
├── README.md                   visão rápida
├── docs/                       documentação do padrão (fases 1, 3, 4, 6 e 7)
├── scripts/                    entradas dos dois fluxos (executar_voxi, executar_remessas)
├── starts/                     start_voxi.bat (envio ativo) e start_remessas.bat
├── sql/
│   ├── estrutura/              DDL de TB_CARTEIRA_VOXI e TB_CONTROLE_EXECUCAO_VOXI
│   └── carteiras/              queries legadas — referência para escrever as procedures
├── tests/                      testes automatizados (unittest)
├── logs/                       logs diários (ignorado pelo Git)
└── src/
    ├── domain/
    │   ├── models/             CarteiraVoxi, ClienteVoxi, OrigemRemessa
    │   └── interfaces/         contratos: repositório de clientes e publicador
    ├── application/
    │   ├── use_cases/          ProcessarVoxi — a regra do fluxo principal
    │   └── services/           geração de CSV e extração de ZIP
    ├── infrastructure/
    │   ├── config/             leitura do .env e catálogo de carteiras
    │   ├── databases/          conexão pyodbc e validação da DM
    │   ├── repositories/       consultas, quarentena e controle de execução
    │   └── sftp/               publicação e leitura via SFTP/FTP
    ├── runners/                orquestração e CLI dos dois fluxos
    └── shared/                 configuração de logging
```

A dependência aponta sempre para dentro: `runners` → `application` → `domain`.
`infrastructure` implementa as interfaces de `domain` e nunca é importada por ele.

---

## 8. Como rodar em produção / deploy

Não há build. O deploy é copiar o repositório para o servidor de robôs e configurar o
Agendador de Tarefas do Windows apontando para `starts\start_voxi.bat`.

**Configuração do agendamento:**

- Início às **08:00**
- Repetir a cada **1 hora**, até **12:00**
- Marcar **"Não iniciar uma nova instância"** se a anterior ainda estiver em execução

A repetição existe porque a carga da `DM.TB_CARTEIRA` não chega no mesmo horário todo dia. Em
cada rodada, o robô trata cada carteira de forma independente:

| Situação da carteira | Ação |
|---|---|
| Já concluída hoje no controle | ignorada |
| DM ainda desatualizada | fica pendente para a próxima rodada |
| DM atualizada e não concluída | gera, envia e registra |
| Consulta retornou 0 clientes | não é marcada como concluída; tenta de novo na próxima rodada |
| Falhou | registrada no log; as outras carteiras seguem |

O fluxo de remessas é agendado separadamente por `starts\start_remessas.bat`.

### Debug pelo VS Code

`Ctrl+Shift+D` → **Run and Debug**, com seis configurações prontas em `.vscode/launch.json`:

| Configuração | Fluxo | Gera arquivo | Envia SFTP | Grava DAILY_VOXI |
|---|---|:---:|:---:|:---:|
| `1. TESTE SMB` | ativo | sim | não | não |
| `2. TESTE SFTP` | ativo | sim | **sim** | não |
| `3. PRODUÇÃO` | ativo | sim | **sim** | **sim** |
| `3B. PRODUCAO - ignora validacao da carga` | ativo | sim | **sim** | **sim** |
| `4. REMESSAS - localizar sem enviar` | remessas | — | não | — |
| `5. REMESSAS PRODUCAO - localizar e enviar` | remessas | — | **sim** | — |

As opções 2, 3, 3B e 5 fazem ações externas reais. A 3B exige uma carteira específica e mantém
todas as outras proteções, inclusive o bloqueio por carteira já concluída.

---

## 9. Manutenção e contato

- **Responsável:** Gustavo Ghiotti — Desenvolvimento, Grupo Acme
- **Repositório:** https://github.com/Acme-Dev/Automacao_Voxi
- **Jira:** projeto `KAN`

### Troubleshooting

| Sintoma no log | Causa provável | O que fazer |
|---|---|---|
| `Variável obrigatória ausente: X` | `.env` incompleto ou não copiado | Comparar com o `.env.example` |
| `Processamento bloqueado: a DM.TB_CARTEIRA não está atualizada` | Carga do dia ainda não rodou | Aguardar a próxima rodada. Se for urgente e a base for confiável, usar `--ignorar-validacao-carga` com uma carteira específica |
| `Processamento bloqueado: ... cedente N (data=...)` | O `ID_CEDENTE` da carteira não está atualizado hoje na DM (ou o id cadastrado está errado) | Conferir o `ID_CEDENTE` da linha em `TB_CARTEIRA_VOXI` e a `DM.TB_CARTEIRA` do cedente |
| `Nenhuma carteira ativa encontrada em dbo.TB_CARTEIRA_VOXI` | Tabela vazia ou tudo com `ATIVO = 0` | Conferir o cadastro no `.66` / `DB_SFTP` |
| `Carteira 'X' não está cadastrada e ativa` | `--carteira` com id/nome que não existe ou está inativo | A mensagem lista os ids e nomes disponíveis |
| `SERVIDOR / BANCO / SCHEMA_PROC / NOME_PROC inválido` | Linha do cadastro com caractere fora do permitido | Corrigir a linha; a validação existe para impedir injeção de SQL no `EXEC` |
| `ID_CEDENTE é obrigatório` | Linha cadastrada sem `ID_CEDENTE` | Preencher o `ID_CEDENTE` real do cedente na DM |
| `não devolveu nenhum result set com o contrato esperado` | A procedure não retorna as 7 colunas exigidas | Revisar o `SELECT` final da procedure (ver "Contrato" na seção 6) |
| `Invalid object name` / `Could not find stored procedure` | Nome cadastrado não corresponde à procedure existente | Conferir `BANCO`, `SCHEMA_PROC` e `NOME_PROC` na tabela |
| `Tamanho divergente após upload` | Conexão caiu no meio do envio | Reexecutar; nada foi gravado na `DAILY_VOXI` |
| `Publicador SFTP não foi configurado` | `--dry-run` combinado com envio | Não usar `--dry-run` para envio real |
| `consulta não retornou clientes` | Régua da carteira não achou ninguém elegível | Esperado quando a base está em quarentena; conferir com o time de dados se persistir |
| `carteira já concluída hoje` | Rodada anterior já enviou | Comportamento correto. Para reenviar, ajustar `TB_CONTROLE_EXECUCAO_VOXI` |
| Falha ao gravar o CSV | Compartilhamento `\\10.0.0.71` fora do ar | Verificar a rede e o acesso do usuário do serviço |

---

**Critério de pronto (Fase 4):** um dev novo clona, instala e roda o projeto usando apenas
este documento, sem precisar perguntar nada.
