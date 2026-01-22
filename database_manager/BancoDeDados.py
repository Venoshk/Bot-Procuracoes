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

    def salvar_procuracao(self, dados):
        cnpj_limpo = self.limpar_cnpj(dados['CNPJ'])
        data_formatada = self.converter_data(dados['Validade'])
        
        conexao = None # Inicializa para evitar o erro no finally

        try:
            # CONEXÃO COM POSTGRES
            conexao = psycopg2.connect(self.dsn)
            cursor = conexao.cursor()


            sql = """
                INSERT INTO procuracoes_recebidas 
                (razao_social, cnpj, validade, situacao, data_extracao)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (cnpj, validade) 
                DO UPDATE SET
                    situacao = EXCLUDED.situacao,
                    data_extracao = CURRENT_TIMESTAMP;
            """
            
            # No psycopg2 usamos %s ao invés de :nome
            cursor.execute(sql, (
                dados['Razão Social'],
                cnpj_limpo,
                data_formatada,
                dados['Situação']
            ))
            
            conexao.commit()
            print(f"[Postgres] Salvo/Atualizado: {dados['Razão Social']}")

        except Exception as e:
            print(f"[Erro Postgres] Falha ao salvar {dados.get('CNPJ')}: {e}")
            if conexao:
                conexao.rollback()
            
        finally:
            if conexao:
                conexao.close()