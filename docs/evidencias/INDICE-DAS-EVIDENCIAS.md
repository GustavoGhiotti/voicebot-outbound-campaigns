# Índice das Evidências — Homologação do Envio Ativo VOXI

**O que é esta pasta:** aqui ficam as *provas* de que o robô funciona — os
registros (logs) e prints de cada teste feito, mostrando o passo a passo do que
foi executado e o resultado. Serve para, no futuro, qualquer pessoa (mesmo sem
ser da área técnica) conseguir abrir e conferir que tudo rodou certo, ou
entender o que aconteceu caso algo dê errado.

**Como ler:** a tabela "Evidências coletadas" mais abaixo lista, por data, cada
teste feito, qual arquivo guarda a prova, e o que aquele teste comprovou. Os
"CA" (critérios de aceite) são os itens verificados na homologação, detalhados
em `docs/04-HOMOLOGACAO.md`.

A cada teste rodado, um arquivo novo é adicionado aqui documentando o sucesso.

Ambiente: `venv` + `requirements.txt` instalados; suíte automatizada 73/73
(ver `docs/03-PLANO_DE_TESTES.md` §5).

## Diagramas de arquitetura (Fase 1)

| Arquivo | Diagrama |
|---|---|
| `01-arquitetura-componentes-envio-ativo.png` | Componentes do Envio Ativo |
| `01-arquitetura-componentes-remessas.png` | Componentes do fluxo de Remessas |
| `01-arquitetura-sequencia-envio-ativo.png` | Sequência do processo principal |

## Mapa modo → critérios de aceite

| Modo (VS Code) | Efeito | Critérios que comprova |
|---|---|---|
| **1. TESTE SMB** (`--dry-run`) | gera CSV no `.71`, sem SFTP/DAILY | CA-02, CA-03, CA-04, CA-08, CA-10, CA-14, CA-19, CA-22, CA-26, CA-27 |
| **2. TESTE SFTP** (`--sem-registro`) | envia ao SFTP, sem gravar DAILY | CA-05 |
| **3. PRODUÇÃO** | envia e grava DAILY + controle | CA-06, CA-09, CA-12 |
| **4/5. REMESSAS** | copia remessas para o SFTP | CA-13 |
| Agendador / start_voxi.bat | rodada automática | CA-11, CA-23 |
| SSMS / SELECT | cadastro, procedures, permissões | CA-16, CA-17, CA-18, CA-25 |

## Evidências coletadas

| Data | Arquivo | Modo | Critérios | Status |
|---|---|---|---|---|
| 19/08/2026 | `docs/03-PLANO_DE_TESTES.md` §5 | testes | CA-15 | ✅ |
| 19/08/2026 | `modo1-dry-run-20260819.log` | 1 (dry-run) | CA-02, CA-04, CA-14, CA-16(parc.), CA-19, CA-26, CA-27 | ✅ 9/9, falhas=[] |
| 19/08/2026 | `CA-08-base-desatualizada-20260819.log` | 1 (dry-run) | CA-08 (trava de base velha) | ✅ |
| 19/08/2026 | `modo2-sftp-20260819.log` + `CA-05-sftp-filezilla-20260819.png` | 2 (SFTP) | CA-05 (upload íntegro — tamanhos batem) | ✅ 9/9, 204.268 bytes |
| 19/08/2026 | `modo3-producao-nu-20260819.log` | 3 (Produção) | CA-06 (quarentena só após upload), CA-12 (controle registrado) | ✅ NU 500 |
| 19/08/2026 | `modo3-ca09-ja-concluida-20260819.log` | 3 (Produção, 2ª vez) | CA-09 (já concluída → ignorada) | ✅ |
| 19/08/2026 | `remessa-pi-20260819.log` | Remessas | CA-13 (PI por procedure, 17.410 linhas) | ✅ |

**Homologação concluída em 19/08/2026** — 27/27 critérios aprovados (parecer APROVADO COM
RESSALVAS em `docs/04-HOMOLOGACAO.md`). Os critérios sem log/print dedicado foram aprovados
pela operação em produção, atestada pelo responsável.

> A cada rodada nova, o arquivo de evidência é adicionado nesta tabela e o
> `04-HOMOLOGACAO.md` recebe o ✅ no critério, com a referência ao arquivo.
