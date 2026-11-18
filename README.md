# Envio Ativo VOXI

> **Versão de portfólio.** Código real de produção, anonimizado: nomes de empresa, clientes, pessoas, hosts, e-mails e credenciais foram trocados por valores fictícios (`Acme`, `Banco Alfa`, `10.0.0.x`, `empresa.example`). Toda configuração sensível vem do `.env` (modelo em `.env.example`). O código não aponta para nenhum sistema real.

Automação para selecionar clientes das carteiras VOXI, gerar um CSV por
carteira e enviar os arquivos para um SFTP.

> Projeto no **Padrão de Desenvolvimento do Grupo Acme**. Antes de mexer,
> leia o [PROJETO.md](PROJETO.md) e a pasta [docs/](docs/):
> [arquitetura](docs/01-ARQUITETURA.md) ·
> [documentação técnica](docs/02-DOCUMENTACAO.md) ·
> [plano de testes](docs/03-PLANO_DE_TESTES.md) ·
> [homologação](docs/04-HOMOLOGACAO.md).

## Estrutura

```text
scripts/                         entradas: executar_voxi e executar_remessas
src/
  application/
    services/                    geração dos arquivos
    use_cases/                   fluxo completo da automação
  domain/
    interfaces/                  contratos dos repositórios/publicadores
    models/                      dados do cliente VOXI
  infrastructure/
    config/                      leitura e validação do .env
    databases/                   conexão SQL Server
    repositories/                cadastro, procedures e DAILY_VOXI
    sftp/                        publicação no SFTP
  runners/                       montagem das dependências e CLI
  shared/                        logging compartilhado
sql/
  estrutura/                     DDL do cadastro TB_CARTEIRA_VOXI
  carteiras/                     queries legadas (referência p/ as procedures)
tests/                           testes automatizados
```

O robô entra por um único script — `scripts/executar_voxi.py`
(`python -m scripts.executar_voxi`), simétrico ao `scripts/executar_remessas.py`
do fluxo de remessas. Sem argumento, executa **todas** as carteiras ativas, uma
por vez.

Existe um único start: `starts\start_voxi.bat`. Sem argumento ele roda todas
as carteiras; com um código, reprocessa só aquela carteira
(`start_voxi.bat zeta` equivale a `-m scripts.executar_voxi --carteira zeta`) e
flags são repassadas direto (`start_voxi.bat --dry-run`). O outro `.bat` é
`start_remessas.bat`, do fluxo secundário.

## Fluxo

1. Consulta a `DM.TB_CARTEIRA` para ZETA e os mailings `RAW` definidos
   nas estratégias das demais carteiras.
2. Usa o telefone do mailing ou o enriquecimento telefônico quando a
   estratégia recebida exigir.
3. Respeita a quarentena registrada em
   `DB_PLANEJAMENTO.dbo.DAILY_VOXI`.
4. Gera um arquivo por carteira com exatamente:
   `TELEFONE;CPF_CNPJ;NOME;CREDOR`.
5. Envia para o diretório configurado no SFTP.
6. Somente após todos os uploads terem sucesso registra o lote na
   `DAILY_VOXI`.

## Carteiras

A lista de carteiras **não fica no código**. Ela é lida da tabela
`DB_SFTP.dbo.TB_CARTEIRA_VOXI` (servidor `10.0.0.66`) no início de cada
execução. Cada linha diz o servidor, banco, schema e nome da **stored
procedure** que devolve os clientes daquela carteira.

A identidade de cada carteira é o `CEDENTE` (nome), que vai no arquivo sempre
em MAIÚSCULO. O `ID_CEDENTE` é o cedente/SFTP que valida a carga e **pode se
repetir** entre carteiras do mesmo SFTP.

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

`MU`, `XICLUB` e `ETA` são o mesmo SFTP (cedente `3`): 3
procedures e 3 arquivos, uma validação de carga só. Para reprocessar, use
`--carteira <NOME>` (só aquela) ou `--carteira <ID_CEDENTE>` (todas as partes
daquele id).

### Incluir uma carteira nova

1. Criar a procedure cumprindo o contrato abaixo.
2. Inserir uma linha em `TB_CARTEIRA_VOXI` apontando para ela.

Nenhum passo exige alterar código Python nem criar `.bat`: o start único já
processa toda carteira ativa, e `start_voxi.bat <id_cedente|nome>` reprocessa
a nova carteira isoladamente.

### Contrato da procedure

- Chamada **sem parâmetros**: `EXEC [BANCO].[SCHEMA].[PROC]`.
- Limite de casos, dias de quarentena e regra de telefone ficam **dentro da
  procedure**. Alterar a régua é `ALTER PROCEDURE`, sem deploy.
- Precisa devolver um result set com, no mínimo:
  `TELEFONE, CPF_CNPJ, NOME, CREDOR, ID_CLIENTE, ATRASO, SALDO_DEVEDOR`.
- Result sets intermediários (`SELECT ... INTO #TEMP`) são ignorados.
- A procedure **não** deve inserir na `DAILY_VOXI`: quem grava a quarentena
  é o robô, e só depois do upload confirmado.

DDL e carga inicial em `sql/estrutura/TB_CARTEIRA_VOXI.sql`. As queries em
`sql/carteiras/` são a **referência legada** para escrever as procedures —
não são mais executadas pelo robô.

O projeto segue os padrões observados em `C:\Robos\RoboCargas`: `pyodbc`
para SQL Server, `paramiko` para SFTP, `.env` para configuração e log em
arquivo.

## Configuração

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Preencha o `.env`. As credenciais não ficam no código. Todas as variáveis
estão descritas em `.env.example` e na seção 5 de `docs/02-DOCUMENTACAO.md`.

> As variáveis `VOXI_CARTEIRA_*` são **obsoletas** e não são lidas por
> nenhum código. Hoje a validação da carga é feita pelo `ID_CEDENTE` da
> linha em `DB_SFTP.dbo.TB_CARTEIRA_VOXI`. Pode apagá-las do `.env`.

Antes do primeiro envio, valide sem escrever no banco nem no SFTP:

```powershell
.\.venv\Scripts\python.exe -m scripts.executar_voxi --dry-run
```

Para gerar logs detalhados:

```powershell
.\.venv\Scripts\python.exe -m scripts.executar_voxi --dry-run --debug
```

### Debug seguro pelo VS Code

Abra **Run and Debug** (`Ctrl+Shift+D`) e escolha uma das configurações:

- `1. TESTE SMB - grava no .71, sem SFTP e sem DAILY`: consulta o banco
  real e gera o CSV em
  `\\10.0.0.71\d\Automacao\VOXI\AAAA\MM\DD`, sem upload e sem registrar
  a quarentena;
- `2. TESTE SFTP - envia e não grava DAILY`: gera o CSV no compartilhamento
  `.71` e faz o upload real, mas não registra a quarentena;
- `3. PRODUÇÃO - envia SFTP e grava DAILY`: gera no `.71`, envia ao SFTP e,
  após o upload, registra os clientes na `DAILY_VOXI`.

As três opções permitem escolher uma carteira ou `todas`. A segunda e a
terceira realizam ações externas reais.

Para processar em produção uma carteira sem validar se a carga foi atualizada
hoje na `DB_REPORT.DM.TB_CARTEIRA`, use
`3B. PRODUCAO - ignora validacao da carga` e selecione uma carteira
específica. Essa opção faz o envio real e mantém as demais proteções,
inclusive o bloqueio se a carteira já estiver concluída no controle diário.
A seleção `todas` não é oferecida nesse modo.

O mesmo modo pode ser executado pelo terminal:

```powershell
python -m scripts.executar_voxi --carteira zeta --ignorar-validacao-carga
```

### Validação diária da DM

Antes de consultar clientes ou gerar qualquer arquivo real, o robô valida
os cedentes ativos da carteira em `DB_REPORT.DM.TB_CARTEIRA`. Todos precisam
ter `DT_ATUALIZACAO` igual à data atual. Se não houver cedente ativo ou se
algum estiver desatualizado, a execução é interrompida antes do SMB, SFTP e
da gravação na `DAILY_VOXI`. Essa trava também é aplicada aos modos 1 e 2.

Carteiras com `VALIDA_CARGA = 0` no cadastro **pulam** essa conferência (o
cedente delas não aparece na `DM.TB_CARTEIRA`) e são processadas direto — hoje
ZETA e PI. Um `ID_CEDENTE` compartilhado (ex.: Mu = 3) é validado
uma vez só na rodada.

### Agendamento e execução única diária

O `starts\start_voxi.bat` pode ser agendado de hora em hora. A execução
trata cada carteira separadamente:

- carteira ainda desatualizada: fica pendente para a próxima rodada;
- carteira atualizada e ainda não concluída: gera, envia e registra;
- carteira já concluída no dia: é ignorada;
- falha em uma carteira: é registrada no log sem impedir a tentativa das
  demais.

Após SFTP e `DAILY_VOXI` concluírem, a execução é registrada em:

```text
10.0.0.66 / LOGS_ROBOS.dbo.TB_CONTROLE_EXECUCAO_VOXI
```

A chave diária é formada por `DATA_REF` e `ID_CEDENTE` (o `CEDENTE` fica
gravado para leitura), com status `CONCLUIDO`, quantidade e nomes dos
arquivos. Esse controle é considerado
somente na produção. Os modos de teste SMB e SFTP continuam repetíveis. No
Agendador de Tarefas do Windows, configure início às 08:00, repetição a
cada 1 hora até 12:00 e escolha a opção para não iniciar uma nova instância
se a anterior ainda estiver em execução.

Para executar os testes automatizados:

```powershell
python -m unittest discover -s tests -v
```

Os diagnósticos também são gravados em `logs\voxi_AAAAMMDD.log`. CPFs e
telefones aparecem mascarados nas amostras do modo debug.

Para processar:

```powershell
.\.venv\Scripts\python.exe -m scripts.executar_voxi
```

### Execução por carteira

Não existe mais um módulo Python por carteira. Use a entrada geral com o
`ID_CEDENTE` ou o nome do cedente cadastrado:

```powershell
python -m scripts.executar_voxi --carteira zeta
python -m scripts.executar_voxi --carteira RHO
python -m scripts.executar_voxi --carteira 43
```

O start único faz exatamente isso: `starts\start_voxi.bat zeta` (ou o
`ID_CEDENTE`) roda só aquela carteira.

Para reprocessar apenas um cedente, use `-m scripts.executar_voxi --carteira <id_cedente|nome>`
ou `start_voxi.bat <id_cedente|nome>`. `python -m scripts.executar_voxi` (ou `start_voxi.bat`
sem argumento) continua executando todas as carteiras, uma procedure por vez.

Os arquivos ficam organizados em:

```text
\\10.0.0.71\d\Automacao\VOXI\AAAA\MM\DD
```

O nome padrão é `<CEDENTE>_AAAAMMDD.csv`, por exemplo
`ZETA_20260724.csv`. O conteúdo é codificado em UTF-8 sem BOM e separado
por `;`.

## Estratégias atuais

- Desde 18/08/2026 a régua de cada carteira vive **dentro da stored
  procedure**, não mais em arquivo `.sql` no repositório. Trocar a régua é
  `ALTER PROCEDURE`; não exige commit nem deploy.
- Como consequência, o limite de casos e os dias de quarentena não são
  visíveis a partir do Python nem da tabela de cadastro. Para auditar, é
  preciso abrir a procedure.
- Valores herdados das queries legadas: 4 dias de quarentena para ZETA,
  SWAT, TETA CONSUMER, IMOB, NU e PI; 8 dias para BETA, Mu,
  Xiclub e Eta; 3 dias e limite de 500 para RHO. Confirmar esses
  valores ao escrever cada procedure.
- O robô continua sendo o único responsável por inserir na `DAILY_VOXI`,
  sempre depois da publicação bem-sucedida no SFTP.

## Envio das remessas recebidas

Este processo consulta as credenciais e o `ORIGEM_CARGA` cadastrados em
`Carga.TB_CONEXAO_SFTP` pelo `C:\Robos\RoboCargas`. Ele lê diretamente o
FTP/SFTP de cada cedente e publica no SFTP VOXI, sem usar SMB.

O destino é `/home/usuario_sftp/REMESSA/AAAA/MM/DD`. O nome segue
`remessa_<carteira>_<AAAAMMDD><extensão>`; para carteiras com dois arquivos,
inclui também `remessa`, `telefone` ou `parcelas` para evitar colisão.

**PI é a exceção:** não vem de um SFTP de origem. Ela roda a procedure
`DB_PLANEJAMENTO.[Raw].[BASE_VOXI_PI]` no `.71` e o result set vira o CSV
(`remessa_pi_AAAAMMDD.csv`, todas as colunas, sem tratamento), publicado
na mesma pasta `REMESSA`. A proc fica fixa no código (a PI é diferente das
demais).

```powershell
python -m scripts.executar_remessas --dry-run
python -m scripts.executar_remessas --carteira pi --dry-run
python -m scripts.executar_remessas --carteira beta --dry-run
python -m scripts.executar_remessas
```

O agendamento pode chamar `starts\start_remessas.bat`. As chaves e o `.env`
são obtidos de `C:\Robos\RoboCargas`; `ROBO_CARGAS_ROOT` altera esse caminho.
