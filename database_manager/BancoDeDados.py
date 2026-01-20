from sqlalchemy import create_engine, text
from datetime import datetime
import re

class BancoDeDados:
    def __init__(self):
        self.connection_string = r"sqlite:///C:\Users\paulo.santos\backendTax\OperacionalJCPDjango\operacionalTaxall\db.sqlite3"
        self.engine = create_engine(self.connection_string)
        
    def limpar_cnpj(self, cnpj_sujo):
        # Remove tudo que não for dígito (pontos, traços, barras)
        return re.sub(r'\D', '', str(cnpj_sujo))

    def converter_data(self, data_str):
        # Converte '31/12/2026' para objeto date do Python
        try:
            return datetime.strptime(data_str, "%d/%m/%Y").date()
        except:
            return None

    def salvar_procuracao(self, dados):
        cnpj_limpo = self.limpar_cnpj(dados['CNPJ'])
        data_formatada = self.converter_data(dados['Validade'])
        
        # --- MUDANÇA 2: Sintaxe SQL do PostgreSQL (ON CONFLICT) ---
        # "ON CONFLICT (cnpj)" obriga que a coluna 'cnpj' seja chave única (UNIQUE) no banco
        # "EXCLUDED" refere-se ao valor novo que você tentou inserir
        sql = text("""
            INSERT INTO procuracoes_recebidas (razao_social, cnpj, validade, situacao, data_extracao)
            VALUES (:razao, :cnpj, :validade, :situacao, NOW())
            ON CONFLICT (cnpj) 
            DO UPDATE SET
                validade = EXCLUDED.validade,
                situacao = EXCLUDED.situacao,
                data_extracao = NOW();
        """)

        try:
            with self.engine.begin() as conn: # .begin() gerencia o commit automaticamente
                conn.execute(sql, {
                    "razao": dados['Razão Social'],
                    "cnpj": cnpj_limpo,
                    "validade": data_formatada,
                    "situacao": dados['Situação']
                })
                print(f"[Postgres] Salvo/Atualizado: {dados['Razão Social']}")
        except Exception as e:
            print(f"[Erro Postgres] Falha ao salvar {dados['CNPJ']}: {e}")   