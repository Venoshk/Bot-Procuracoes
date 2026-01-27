
---
# 🏛️ TaxHub - Módulo de Procurações (e-CAC)

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![AWS RDS](https://img.shields.io/badge/AWS%20RDS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)

> **Automação inteligente para gestão de procurações eletrônicas da Receita Federal.**

Este sistema é responsável por consultar, extrair e armazenar o histórico de procurações digitais diretamente do portal **e-CAC**. Ele resolve o problema da necessidade de **Certificados Digitais Locais** integrando-se a uma infraestrutura de nuvem centralizada.

---

## 📋 Tabela de Conteúdos
1. [Arquitetura do Sistema](#-arquitetura-do-sistema)
2. [Stack Tecnológico](#-stack-tecnológico)
3. [Configuração (.env)](#-configuração-e-variáveis-de-ambiente)
4. [Banco de Dados e Regras](#-banco-de-dados-e-regras-de-negócio)
5. [Como Executar](#-como-executar)
6. [Troubleshooting](#-troubleshooting)

---

## 🏗 Arquitetura do Sistema

O projeto opera em um modelo **Híbrido (Local + Nuvem)** para contornar a restrição de hardware dos tokens de certificado digital.
```markdown

flowchart LR
    subgraph Local [🏢 Ambiente On-Premise (Escritório/Algar)]
        direction TB
        Token[🔐 Certificado Digital A1/A3]
        Crawler[🤖 Robô/Crawler Python]
        Token --> Crawler
    end

    subgraph Cloud [☁️ AWS Cloud]
        direction TB
        DB[(🗄️ AWS RDS PostgreSQL)]
        API[⚡ API Django REST]
        DB <--> API
    end

    Crawler -- "Gravação Direta (psycopg2)" --> DB
    API -- "JSON" --> Frontend[💻 Dashboard do Usuário]

```

* **Crawler:** Executa em máquina local (IP Fixo) para acessar o e-CAC via certificado.
* **Banco de Dados:** Centralizado na AWS para acesso global.

---

## 🛠 Stack Tecnológico

| Componente | Tecnologia | Detalhe |
| --- | --- | --- |
| **Linguagem** | Python 3.x | Core da automação e backend. |
| **Web Framework** | Django + DRF | API para consumo dos dados. |
| **Database** | PostgreSQL | Hospedado no Amazon RDS. |
| **Driver SQL** | `psycopg2-binary` | Conexão de alta performance p/ o Crawler. |
| **Automação** | Selenium / Requests | Navegação no portal e-CAC. |

---

## ⚙️ Configuração e Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto.

> ⚠️ **Importante:** Para scripts Python, a URL do banco **NÃO** deve conter o prefixo `jdbc:`. Use o formato padrão `libpq`.

```ini
# .env

# ✅ CORRETO (Para Python/Django/Psycopg2)
URL_BANCO=postgresql://usuario:senha@taxallhub.c54ciw48evvs.us-east-1.rds.amazonaws.com:5432/taxhub

# ❌ INCORRETO (Não use JDBC)
# URL_BANCO=jdbc:postgresql://...

# Configurações Gerais
DEBUG=True
SECRET_KEY=sua-chave-super-secreta

```

---

## 🗄️ Banco de Dados e Regras de Negócio

A tabela alvo é `procuracoes_recebidas` (ou `procuracoes_procuracao` no Django).

### Estrutura da Tabela

| Campo | Tipo | Notas |
| --- | --- | --- |
| `cnpj` | `VARCHAR` | CNPJ do Outorgante (apenas números). |
| `validade` | `DATE` | Data de expiração da procuração. |
| `situacao` | `VARCHAR` | Ex: *Ativa*, *Cancelada*, *Vencida*. |
| `data_extracao` | `TIMESTAMP` | Auditoria de quando o robô rodou. |

### 🔒 Integridade de Dados (Upsert)

Utilizamos uma **Constraint Composta** para permitir histórico de renovações, mas impedir duplicidade de dados idênticos.

**1. A Constraint SQL:**

```sql
ALTER TABLE procuracoes_recebidas 
ADD CONSTRAINT unique_cnpj_validade UNIQUE (cnpj, validade);

```

**2. O Script de Inserção (Python):**
O sistema usa a estratégia `ON CONFLICT` para atualizar status ou ignorar duplicatas.

```python
sql = """
    INSERT INTO procuracoes_recebidas (razao_social, cnpj, validade, situacao, data_extracao)
    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT (cnpj, validade) 
    DO UPDATE SET
        situacao = EXCLUDED.situacao,      -- Atualiza se o status mudou (ex: Cancelou)
        data_extracao = CURRENT_TIMESTAMP; -- Marca que conferimos hoje
"""

```

---

## 🚀 Como Executar

### Pré-requisitos

* Python 3.8+
* Acesso à internet liberado para a porta `5432` (Postgres) da AWS.
* Certificado Digital instalado na máquina.

### Instalação das Dependências

```bash
pip install -r requirements.txt
# Certifique-se de que psycopg2-binary está no requirements

```

### Rodando o Crawler

```bash
# Via comando Django
python manage.py importar_procuracoes

# OU via script direto
python scripts/crawler_ecac.py

```

---

## 🔧 Troubleshooting

<details>
<summary><strong>🔴 Erro: "cannot access local variable 'conexao'"</strong></summary>

* **Causa:** A conexão com o banco falhou dentro do `try` e a variável não foi iniciada.
* **Correção:** Verifique se o IP da sua máquina está liberado no **Security Group da AWS** e se a `URL_BANCO` está correta.

</details>

<details>
<summary><strong>🔴 Erro: "duplicate key value violates unique constraint"</strong></summary>

* **Causa:** O script tentou inserir um dado que já existe sem tratar o erro.
* **Correção:** Certifique-se de que sua query SQL usa a cláusula `ON CONFLICT DO UPDATE/NOTHING`.

</details>

<details>
<summary><strong>🔴 Erro: Protocolo inválido (JDBC)</strong></summary>

* **Causa:** Uso de `jdbc:postgresql://` no `.env`.
* **Correção:** Remova o `jdbc:`. O Python espera `postgresql://`.

</details>

---

Made with 💙 by **TaxHub Team**

```

```
