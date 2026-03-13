---
# 🏛️ TaxHub - Módulo de Procurações (e-CAC)

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django_REST-092E20?style=for-the-badge&logo=django&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring_Boot-6DB33F?style=for-the-badge&logo=spring&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![AWS RDS](https://img.shields.io/badge/AWS%20RDS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

> **Automação inteligente e auditoria fiscal de procurações eletrônicas da Receita Federal.**

Este sistema é responsável por consultar, extrair, auditar e armazenar o histórico de procurações digitais diretamente do portal **e-CAC**. Ele resolve o gargalo operacional da gestão manual e a necessidade de Certificados Digitais Locais, integrando-se a uma infraestrutura de nuvem centralizada.

---

## 📋 Tabela de Conteúdos
1. [O que o Robô Faz?](#-o-que-o-robô-faz-funcionalidades-do-crawler)
2. [Arquitetura do Sistema](#-arquitetura-do-sistema)
3. [Stack Tecnológico](#-stack-tecnológico)
4. [Configuração (.env)](#-configuração-e-variáveis-de-ambiente)
5. [Banco de Dados e Regras](#-banco-de-dados-e-regras-de-negócio)
6. [Como Executar](#-como-executar)
7. [Troubleshooting](#-troubleshooting)

---

## 🤖 O que o Robô Faz? (Funcionalidades do Crawler)

O robô Python não faz apenas *web scraping* básico; ele atua como um auditor fiscal automatizado com as seguintes capacidades:

* **Navegação Autenticada:** Acessa o portal e-CAC de forma segura utilizando o Certificado Digital (A1/A3) da máquina local.
* **Inteligência Tributária:** Consulta a Brasil API para descobrir o regime tributário de cada CNPJ capturado (Simples Nacional, Lucro Presumido/Real) e calcula regras complexas, como a janela de 5 anos de exclusão do Simples (Regime Misto).
* **Leitura Multiformato:** Consegue extrair os "poderes outorgados" tanto de Modais HTML injetados na tela quanto pelo download e leitura de arquivos PDF (`PyPDF2`).
* **Auditoria de Checklists Dinâmicos:** Compara os poderes liberados pelo cliente com a matriz de exigências fiscais exata do regime da empresa, apontando especificamente quais permissões estão faltando.
* **Mecanismos de Performance e Resiliência:** Possui sistema *Anti-DDoS* com limite de requisições e *retries*, além de um gatilho de *Early Exit* (Saída Antecipada) que interrompe a varredura ao identificar procurações antigas já registradas no banco.

---

## 🏗 Arquitetura do Sistema

O projeto opera em um modelo **Híbrido (Local + Nuvem)** para contornar a restrição de hardware dos tokens de certificado digital, conectando-se a uma arquitetura robusta de backend e frontend.

```mermaid
flowchart LR
    subgraph Local [🏢 Ambiente On-Premise]
        direction TB
        Token[🔐 Certificado Digital]
        Crawler[🤖 Robô Python/Selenium]
        Token --> Crawler
    end

    subgraph Cloud [☁️ AWS Cloud]
        direction TB
        DB[(🗄️ AWS RDS PostgreSQL)]
        API[⚡ API Django DRF]
        Services[☕ Serviços Spring Boot]
        DB <--> API
        DB <--> Services
    end

    Crawler -- "Gravação Direta (psycopg2)" --> DB
    API -- "JSON" --> Frontend[💻 Painel React]
```

* **Crawler:** Executa em máquina local para viabilizar a assinatura digital no e-CAC.
* **Banco de Dados:** Centralizado na AWS para garantir acesso unificado.
* **APIs & Serviços:** Django REST gerencia endpoints gerais, enquanto rotinas auxiliares de download rodam via Spring Boot.

---

## 🛠 Stack Tecnológico

| Componente | Tecnologia | Detalhe |
| :--- | :--- | :--- |
| **Automação (Crawler)** | Python + Selenium + BS4 | Varredura do e-CAC, leitura de DOM e PDFs. |
| **API Principal** | Django REST Framework | Gerenciamento de rotas, JWT e regras de negócio. |
| **Serviços Específicos** | Java Spring Boot | Controle de filas e downloads pesados (DARF, DCTF). |
| **Frontend** | React | Interface de visualização para os usuários. |
| **Database** | PostgreSQL | Hospedado na AWS RDS (ambiente de produção). |
| **Driver SQL** | `psycopg2-binary` | Conexão veloz e direta para as rotinas do Crawler. |

---

## ⚙️ Configuração e Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto. O sistema utiliza `python-dotenv` para o carregamento seguro.

> ⚠️ **Importante:** Para scripts Python com `psycopg2`, a URL do banco **NÃO** deve conter prefixos como `jdbc:`. Use o formato padrão `postgresql://`.

```ini
# .env

# ✅ CORRETO (Para Python/Django/Psycopg2)
URL_BANCO=postgresql://usuario:senha@taxallhub.xyz.us-east-1.rds.amazonaws.com:5432/taxhub

# ❌ INCORRETO (Evite formatos de outras linguagens)
# URL_BANCO=jdbc:postgresql://...

# Configurações da API
DEBUG=True
SECRET_KEY=sua-chave-super-secreta
```

---

## 🗄️ Banco de Dados e Regras de Negócio

A tabela principal gerida pelo robô é a `procuracoes_recebidas` (ou `procuracoes_procuracao` no mapeamento do Django).

### Estrutura da Tabela

| Campo | Tipo | Notas |
| :--- | :--- | :--- |
| `cnpj` | `VARCHAR` | CNPJ do Outorgante (higienizado, apenas números). |
| `regime` | `VARCHAR` | Classificação tributária (ex: *Simples Nacional*, *Misto*). |
| `validade` | `DATE` | Data limite de vigência do documento. |
| `situacao` | `VARCHAR` | Status no e-CAC (ex: *Ativa*, *Cancelada*, *Vencida*). |
| `poderes` | `TEXT` | Resultado da auditoria ou lista de permissões. |
| `data_extracao` | `TIMESTAMP` | Auditoria de quando o robô validou a informação. |

### 🔒 Integridade de Dados (Upsert Inteligente)

Utilizamos uma constraint composta para manter o histórico de renovações de um mesmo CNPJ, impedindo a duplicação do mesmo documento.

**1. Constraint SQL:**
```sql
ALTER TABLE procuracoes_recebidas 
ADD CONSTRAINT unique_cnpj_validade UNIQUE (cnpj, validade);
```

**2. Script de Inserção (Python):**
O *Crawler* adota a estratégia `ON CONFLICT` para atualizar apenas o status e a data de checagem.
```python
sql = """
    INSERT INTO procuracoes_recebidas (razao_social, cnpj, regime, validade, situacao, data_extracao, poderes)
    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
    ON CONFLICT (cnpj, validade) 
    DO UPDATE SET
        regime = EXCLUDED.regime,
        situacao = EXCLUDED.situacao,
        data_extracao = CURRENT_TIMESTAMP,
        poderes = EXCLUDED.poderes;
"""
```

---

## 🚀 Como Executar

### Pré-requisitos
* Python 3.8+
* Acesso à internet liberado para a porta `5432` (Postgres) da AWS.
* Certificado Digital instalado na máquina de execução.

### Instalação das Dependências
```bash
pip install -r requirements.txt
```

### Rodando o Crawler
```bash
# Execução direta do script de raspagem
python scripts/crawler_ecac.py

# Caso utilize um comando customizado do Django
python manage.py importar_procuracoes
```

---

## 🔧 Troubleshooting

<details>
<summary><strong>🔴 Erro: "cannot access local variable 'conexao'"</strong></summary>

* **Causa:** A conexão com o banco falhou dentro do bloco `try` e a variável não foi instanciada antes do `finally`.
* **Correção:** Verifique se o IP da sua rede local está liberado no **Security Group da AWS RDS** e se a `URL_BANCO` está preenchida corretamente no `.env`.
</details>

<details>
<summary><strong>🔴 Erro: "duplicate key value violates unique constraint"</strong></summary>

* **Causa:** O script tentou inserir um dado já existente.
* **Correção:** Verifique se o código de banco de dados (`BancoDeDados.py`) está utilizando corretamente a cláusula `ON CONFLICT DO UPDATE`.
</details>

<details>
<summary><strong>🔴 Erro: fe_sendauth no password supplied</strong></summary>

* **Causa:** O Python não conseguiu ler as credenciais.
* **Correção:** Certifique-se de que a biblioteca `python-dotenv` está instalada e sendo chamada no início do arquivo (`load_dotenv()`).
</details>

---
