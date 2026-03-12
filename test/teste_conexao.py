import psycopg2
import os

DSN = os.getenv('URL_BANCO')

def testar_acesso():
    try:
        print("Tentando conectar ao RDS...")
        conn = psycopg2.connect(DSN)
        cursor = conn.cursor()
        
        # Executa um comando simples para ver se o banco responde
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        print("-" * 30)
        print("✅ CONEXÃO ESTABELECIDA COM SUCESSO!")
        print(f"Versão do Banco: {db_version[0]}")
        print("-" * 30)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print("-" * 30)
        print(f"❌ ERRO AO CONECTAR:")
        print(e)
        print("-" * 30)
        print("\nDica: Verifique se o seu IP está liberado no Security Group do RDS na AWS.")

if __name__ == "__main__":
    testar_acesso()