import sys
import os
import logging
from Driver.ecac_navigation import EcacBaixaAndUpload
from logs.loggingStderout import StreamToLogger
from logs.logs import Logs
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout = StreamToLogger(logging.getLogger(),logging.INFO)
sys.stderr = StreamToLogger(logging.getLogger(),logging.ERROR)

def processar_mensagem():
    EcacBaixaAndUpload.getAndProcuracoes()

def main():
    try:
        processar_mensagem()
    
    except Exception as e:
        Logs.log_fail(f"Erro ao processar : {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExecução interrompida pelo usuário.")