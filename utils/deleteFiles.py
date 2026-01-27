import os
import shutil
from logs.logs import Logs

def deleteFiles(directoryPath):
    """
    Função blindada para limpar o diretório downloads
    """
    print(f"Tentando limpar o diretório: {directoryPath}") # Debug visual
    
    try:
        if not os.path.exists(directoryPath):
            Logs.log_fail(f"O diretório não existe ou caminho está errado: {directoryPath}")
            # Tenta criar se não existir para não quebrar, ou apenas retorna
            return

        # Lista tudo na pasta
        for item in os.listdir(directoryPath):
            item_path = os.path.join(directoryPath, item)
            
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path) # Deleta arquivo
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path) # Deleta pasta (CNPJ)
            except Exception as e:
                print(f'Falha ao deletar {item_path}. Razão: {e}')

        Logs.log_sucess(f"Limpeza concluída em: {directoryPath}")

    except Exception as e:
        Logs.log_fail(f"Erro crítico ao limpar pasta: {e}")