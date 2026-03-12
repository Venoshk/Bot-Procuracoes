import os
import re
from datetime import datetime
import psycopg2  

CONEXAO_BANCO = os.getenv('URL_BANCO')

class BancoDeDados:
    
    def __init__(self):
        self.dsn = CONEXAO_BANCO 

    def limpar_cnpj(self, cnpj_sujo):
        return re.sub(r'\D', '', str(cnpj_sujo))

    def converter_data(self, data_str):
        try:
            dt = datetime.strptime(data_str, "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        except:
            return None

    def procuracao_ja_processada(self, cnpj, validade):
        """
        Pergunta 1: "Ei banco, eu já li ESSE documento exato antes?"
        Isso evita que o robô perca tempo abrindo modal ou baixando PDF repetido.
        """
        cnpj_limpo = self.limpar_cnpj(cnpj)
        data_formatada = self.converter_data(validade)
        conexao = None
        try:
            conexao = psycopg2.connect(self.dsn)
            cursor = conexao.cursor()
            sql = "SELECT 1 FROM procuracoes_recebidas WHERE cnpj = %s AND validade = %s AND poderes IS NOT NULL LIMIT 1;"
            cursor.execute(sql, (cnpj_limpo, data_formatada))
            return cursor.fetchone() is not None
        except Exception:
            return False
        finally:
            if conexao:
                cursor.close()
                conexao.close()

    def buscar_regime_da_empresa(self, cnpj):
        
        cnpj_limpo = self.limpar_cnpj(cnpj)
        conexao = None
        try:
            conexao = psycopg2.connect(self.dsn)
            cursor = conexao.cursor()
            sql = """
                SELECT regime FROM procuracoes_recebidas 
                WHERE cnpj = %s AND regime IS NOT NULL AND regime NOT IN ('N/A', '', 'None')
                ORDER BY data_extracao DESC LIMIT 1;
            """
            cursor.execute(sql, (cnpj_limpo,))
            resultado = cursor.fetchone()
            if resultado:
                return resultado[0]
            return None
        except Exception:
            return None
        finally:
            if conexao:
                cursor.close()
                conexao.close()

    def buscar_dados_cnpj(self, cnpj, validade):
        """
        Busca o regime apenas se essa procuração específica (CNPJ + Validade) já existir no banco.
        """
        cnpj_limpo = self.limpar_cnpj(cnpj)
        data_formatada = self.converter_data(validade)
        conexao = None
        
        try:
            conexao = psycopg2.connect(self.dsn)
            cursor = conexao.cursor()
            
            sql = """
                SELECT regime 
                FROM procuracoes_recebidas 
                WHERE cnpj = %s AND validade = %s
                  AND regime IS NOT NULL 
                  AND regime NOT IN ('N/A', '', 'None')
                LIMIT 1;
            """
            cursor.execute(sql, (cnpj_limpo, data_formatada))
            resultado = cursor.fetchone()
            
            if resultado:
                return {"Regime": resultado[0]}
                
            return None 
            
        except Exception as e:
            print(f"[Erro Postgres] Falha ao buscar CNPJ {cnpj}: {e}")
            return None
            
        finally:
            if conexao:
                cursor.close()
                conexao.close()


    def salvar_procuracao(self, dados):
        cnpj_limpo = self.limpar_cnpj(dados['CNPJ'])
        data_formatada = self.converter_data(dados['Validade'])
        
        conexao = None 

        try:
            conexao = psycopg2.connect(self.dsn)
            cursor = conexao.cursor()

            sql = """
                INSERT INTO procuracoes_recebidas 
                (razao_social, cnpj, regime, validade, situacao, data_extracao, poderes)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                ON CONFLICT (cnpj, validade) 
                DO UPDATE SET
                    regime = EXCLUDED.regime,
                    situacao = EXCLUDED.situacao,
                    data_extracao = CURRENT_TIMESTAMP,
                    poderes = EXCLUDED.poderes;
            """
            
            cursor.execute(sql, (
                dados['Razão Social'],
                cnpj_limpo,
                dados.get('Regime'),
                data_formatada,
                dados['Situação'],
                dados['Poderes']
            ))
            
            conexao.commit()
            print(f"[Postgres] Salvo/Atualizado: {dados['Razão Social']} | Regime: {dados.get('Regime', 'N/A')}")

        except Exception as e:
            print(f"[Erro Postgres] Falha ao salvar {dados.get('CNPJ')}: {e}")
            if conexao:
                conexao.rollback()
        
        finally:
            if conexao:
                cursor.close()
                conexao.close()