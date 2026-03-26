import os
import re
import logging
from datetime import datetime
from contextlib import contextmanager

import psycopg2

logger = logging.getLogger(__name__)

CONEXAO_BANCO = os.getenv('URL_BANCO')

# Mapeamento fixo — evita SQL dinâmico com f-string
_FILTROS_REGIME = {
    "SIMPLES NACIONAL":     "exige_simples_nacional = TRUE",
    "LUCRO PRESUMIDO/REAL": "exige_lucro_presumido_real = TRUE",
}
_FILTRO_REGIME_PADRAO = "(exige_simples_nacional = TRUE OR exige_lucro_presumido_real = TRUE)"


class BancoDeDados:
    """Camada de acesso ao banco PostgreSQL.

    Cada método abre e fecha sua própria conexão de forma segura via
    context manager, garantindo que recursos sejam liberados mesmo em
    caso de exceção.
    """

    def __init__(self, dsn: str = CONEXAO_BANCO) -> None:
        if not dsn:
            raise ValueError("URL_BANCO não definida nas variáveis de ambiente.")
        self.dsn = dsn

    # =========================================================================
    # CONTEXT MANAGER INTERNO
    # =========================================================================

    @contextmanager
    def _conexao(self):
        """Abre uma conexão e cursor, garante commit/rollback e fechamento."""
        conn = psycopg2.connect(self.dsn)
        try:
            with conn.cursor() as cursor:
                yield conn, cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _limpar_cnpj(cnpj: str) -> str:
        return re.sub(r'\D', '', str(cnpj))

    @staticmethod
    def _converter_data(data_str: str) -> str | None:
        try:
            return datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    # =========================================================================
    # CONSULTAS
    # =========================================================================

    def procuracao_ja_processada(self, cnpj: str, validade: str) -> bool:
        """Retorna True se a procuração (CNPJ + validade) já existe no banco com poderes preenchidos."""
        cnpj_limpo     = self._limpar_cnpj(cnpj)
        data_formatada = self._converter_data(validade)

        sql = """
            SELECT 1 FROM procuracoes_recebidas
            WHERE cnpj = %s AND validade = %s AND poderes IS NOT NULL
            LIMIT 1;
        """
        try:
            with self._conexao() as (_, cursor):
                cursor.execute(sql, (cnpj_limpo, data_formatada))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error("Falha ao verificar procuração (CNPJ=%s): %s", cnpj, e)
            return False

    def buscar_regime_da_empresa(self, cnpj: str) -> str | None:
        """Retorna o regime tributário mais recente da empresa, ou None se não encontrado."""
        cnpj_limpo = self._limpar_cnpj(cnpj)

        sql = """
            SELECT regime FROM procuracoes_recebidas
            WHERE cnpj = %s AND regime IS NOT NULL AND regime NOT IN ('N/A', '', 'None')
            ORDER BY data_extracao DESC
            LIMIT 1;
        """
        try:
            with self._conexao() as (_, cursor):
                cursor.execute(sql, (cnpj_limpo,))
                resultado = cursor.fetchone()
                return resultado[0] if resultado else None
        except Exception as e:
            logger.error("Falha ao buscar regime (CNPJ=%s): %s", cnpj, e)
            return None

    def buscar_dados_cnpj(self, cnpj: str, validade: str) -> dict | None:
        """Retorna {'Regime': valor} se a procuração específica (CNPJ + validade) existir no banco."""
        cnpj_limpo     = self._limpar_cnpj(cnpj)
        data_formatada = self._converter_data(validade)

        sql = """
            SELECT regime FROM procuracoes_recebidas
            WHERE cnpj = %s AND validade = %s
              AND regime IS NOT NULL AND regime NOT IN ('N/A', '', 'None')
            LIMIT 1;
        """
        try:
            with self._conexao() as (_, cursor):
                cursor.execute(sql, (cnpj_limpo, data_formatada))
                resultado = cursor.fetchone()
                return {"Regime": resultado[0]} if resultado else None
        except Exception as e:
            logger.error("Falha ao buscar dados do CNPJ=%s: %s", cnpj, e)
            return None

    def buscar_checklist_por_regime(self, regime: str) -> list[str]:
        """Retorna a lista de códigos de autorização ativos para o regime informado."""
        regime_upper = regime.upper()
        filtro       = _FILTROS_REGIME.get(regime_upper, _FILTRO_REGIME_PADRAO)

        # Colunas são nomes fixos definidos em código — não há entrada do usuário na query
        sql = f"SELECT cod_autorizacao FROM servico_autorizacao WHERE {filtro} AND ativo = TRUE;"

        try:
            with self._conexao() as (_, cursor):
                cursor.execute(sql)
                return [linha[0] for linha in cursor.fetchall()]
        except Exception as e:
            logger.error("Falha ao buscar checklist para regime '%s': %s", regime, e)
            return []

    # =========================================================================
    # ESCRITA
    # =========================================================================

    def salvar_procuracao(self, dados: dict) -> None:
        """Insere ou atualiza uma procuração no banco (upsert por CNPJ + validade)."""
        cnpj_limpo     = self._limpar_cnpj(dados['CNPJ'])
        data_formatada = self._converter_data(dados['Validade'])

        sql = """
            INSERT INTO procuracoes_recebidas
                (razao_social, cnpj, regime, validade, situacao, data_extracao, poderes)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
            ON CONFLICT (cnpj, validade)
            DO UPDATE SET
                regime        = EXCLUDED.regime,
                situacao      = EXCLUDED.situacao,
                data_extracao = CURRENT_TIMESTAMP,
                poderes       = EXCLUDED.poderes;
        """
        try:
            with self._conexao() as (_, cursor):
                cursor.execute(sql, (
                    dados['Razão Social'],
                    cnpj_limpo,
                    dados.get('Regime'),
                    data_formatada,
                    dados['Situação'],
                    dados['Poderes'],
                ))
            logger.info("Salvo/Atualizado: %s | Regime: %s", dados['Razão Social'], dados.get('Regime', 'N/A'))
        except Exception as e:
            logger.error("Falha ao salvar procuração (CNPJ=%s): %s", dados.get('CNPJ'), e)
            raise