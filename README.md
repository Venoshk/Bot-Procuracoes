# Bot de Procurações e-CAC

Automação em Python para acessar o portal e-CAC com certificado digital, extrair procurações recebidas, auditar poderes por regime tributário e gravar os resultados no PostgreSQL.

## Visão Geral

Este projeto executa um fluxo de ponta a ponta:

1. Abre navegador automatizado com SeleniumBase (modo CDP/UC).
2. Realiza login no e-CAC com certificado digital.
3. Navega até Minhas Autorizações e filtra procurações recebidas.
4. Itera CNPJ por CNPJ da tabela.
5. Detecta regime tributário pela BrasilAPI com fallback para histórico no banco.
6. Obtém checklist de códigos esperados por regime.
7. Tenta ler poderes via modal de visualização; se falhar, baixa PDF e extrai códigos.
8. Classifica se todos os poderes conferem, se é procuração ampla ou se faltam códigos.
9. Faz upsert no banco por chave composta CNPJ + validade.
10. Salva relatório de erros de classificação em JSON quando necessário.
11. Faz logout seguro do e-CAC.

## Estrutura do Projeto

- main.py: ponto de entrada da execução.
- Driver/ecac_navigation.py: orquestra inicialização, login, processamento e logout.
- Driver/driver_login.py: fluxo de autenticação no e-CAC.
- Driver/driver_procuracoes.py: extração, auditoria de poderes e integração com banco/API.
- database_manager/BancoDeDados.py: camada de acesso ao PostgreSQL (consultas e upsert).
- logs/logs.py: logs coloridos no console.
- logs/loggingStderout.py: redirecionamento de stdout/stderr para arquivo de log diário.
- utils/captchaHandler.py: suporte para hCaptcha (YesCaptcha), opcional no fluxo atual.
- utils/deleteFiles.py: limpeza de diretórios de download.
- test/teste_conexao.py: teste simples de conectividade com o banco.
- downloads/procuracao: destino dos PDFs temporários baixados durante a execução.

## Stack Técnica

- Python 3.10+
- SeleniumBase e Selenium
- BeautifulSoup4
- Requests
- PyPDF2
- psycopg2
- PostgreSQL

Dependências completas estão em requirements.txt.

## Pré-requisitos

1. Python instalado.
2. Certificado digital funcional na máquina que executa o robô.
3. Acesso de rede ao portal e-CAC e à URL do banco PostgreSQL.
4. URL_BANCO configurada com credenciais válidas.

## Configuração

Crie um arquivo .env na raiz do projeto com, no mínimo:

```env
URL_BANCO=postgresql://usuario:senha@host:5432/database
CAPTCHA_SOLVER_API_KEY=sua_chave_opcional
FOLDER_PATH=caminho_opcional_para_arquivos_de_captcha
```

Notas importantes:

1. A URL do banco deve usar postgresql:// e nao jdbc:postgresql://.
2. CAPTCHA_SOLVER_API_KEY só é necessário se o fluxo de captcha estiver ativo.
3. O código também cria/usa automaticamente o diretório downloads/procuracao.

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Execução

Para rodar o bot:

```bash
python main.py
```

Fluxo resumido em runtime:

1. Inicializa WebDriver em modo CDP.
2. Faz login no e-CAC.
3. Processa tabela de procurações recebidas.
4. Persiste no banco.
5. Encerra sessão com logout seguro.

## Regras de Negócio de Auditoria

O módulo de poderes aplica três classificações principais:

1. Todos os poderes confere
2. Todos os poderes confere (Procuração Ampla)
3. Faltam N códigos: codigo1 | codigo2 | ...

A classificação compara códigos encontrados no modal/PDF com os códigos esperados retornados da tabela de serviços por regime tributário.

## Banco de Dados

### Tabela principal

Tabela usada pelo fluxo: procuracoes_recebidas.

Campos relevantes utilizados no código:

- razao_social
- cnpj
- regime
- validade
- situacao
- data_extracao
- poderes

### Regra de unicidade e upsert

O projeto considera chave composta cnpj + validade para evitar duplicidade da mesma procuração.

Exemplo de índice/constraint esperado:

```sql
ALTER TABLE procuracoes_recebidas
ADD CONSTRAINT unique_cnpj_validade UNIQUE (cnpj, validade);
```

O salvamento usa INSERT ... ON CONFLICT (cnpj, validade) DO UPDATE.

### Tabela de checklist de serviços

A busca de códigos esperados é feita em servico_autorizacao, com filtros por regime e ativo = TRUE.

## Logs e Artefatos

Saídas do processo:

1. Console com logs coloridos e timestamp.
2. Arquivo de log diário em logs/logs/consumer_log_YYYY-MM-DD.log.
3. Arquivo erros_classificacao.json na raiz quando houver falhas de extração.
4. Arquivos temporários de download em downloads/procuracao.

## Teste de Conectividade com Banco

Para validar acesso ao banco:

```bash
python test/teste_conexao.py
```

Esse script tenta conectar via URL_BANCO e executar SELECT version().

## Troubleshooting

### Falha de conexão no banco

Possíveis causas:

1. URL_BANCO ausente ou inválida.
2. Credenciais incorretas.
3. Host/porta sem acesso de rede.

Ações:

1. Validar .env.
2. Executar python test/teste_conexao.py.
3. Confirmar liberação de IP/security group no provedor do banco.

### API de regime indisponível

Comportamento do sistema:

1. Tenta BrasilAPI até 3 vezes.
2. Em falha, busca regime histórico no banco.
3. Se ainda falhar, segue com fallback de regime.

### Modal/PDF não extraído

Comportamento:

1. Tenta modal.
2. Se modal falhar, tenta PDF.
3. Se ambos falharem, grava erro em erros_classificacao.json.

## Segurança e Boas Práticas

1. Não versionar .env nem credenciais.
2. Não versionar arquivos de log e downloads temporários.
3. Revisar políticas de acesso ao banco periodicamente.
4. Evitar execução paralela do bot contra a mesma base sem coordenação.

## Observações

1. O projeto atual não expõe API web neste repositório; é um executor de automação.
2. A automação depende da estabilidade do layout do e-CAC; mudanças de interface podem exigir ajustes de seletores.

