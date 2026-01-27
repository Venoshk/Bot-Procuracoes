import os
import random
import sys
import time
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logs.logs import Logs
from .driver_login import LoginProcuracao
from .driver_procuracoes import Procuracoes
from seleniumbase import SB



ano_processamento = 2020
eh_procuracao = False
# download_path = os.path.join(os.getcwd(), "downloads", "pgdas", cnpj)


def isAuthPage(driver):
    return ('/autenticacao' in driver.get_current_url() or
            'sso.acesso.gov.br' in driver.get_current_url())


class EcacBaixaAndUpload():

    @staticmethod
    def getAndProcuracoes():
        download_dir = os.path.abspath(os.path.join('downloads/procuracao'))
        os.makedirs(download_dir, exist_ok=True)

        with SB(uc=True, headed=True, headless2=False, incognito=True, external_pdf=True, maximize=True) as sb:

            driver = LoginProcuracao.initiateWebDriver(sb, download_dir)

            if LoginProcuracao.isGovBrIntermediatePage(driver):
                LoginProcuracao.clickEntrarComGovBr(driver)
                LoginProcuracao.loginECAC(driver)
                driver.wait_for_element_visible("body", timeout=60)
            else:
                 LoginProcuracao.loginECAC(driver)

            try:
                Procuracoes.tabelaRecebidas(driver)

                time.sleep(10)

            except Exception as e:
                Logs.log_fail(f"Erro ao extrair JSON: {e}")
            
            finally:
                LoginProcuracao.exitsECACSafely(driver)



            
                    

