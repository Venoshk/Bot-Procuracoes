from logs.logs import Logs
from time import sleep
import random
from utils.captchaHandler import yesCaptchaHandler

class LoginProcuracao():

    @staticmethod
    def exitsECACSafely(sb):
        try:
            Logs.log_warning('-----------tentando sair com segurança-----------')
            sleep(2)
            #sb.driver.switch_to.default_content()
            #sb.find_element(By.XPATH, '//*[@id="sairSeguranca"]').click()
            sb.cdp.get('https://cav.receita.fazenda.gov.br/autenticacao/Login/Logout')
            sleep(5)
            Logs.log_warning(
                "-----------SAINDO COM SEGURANÇA, DESATIVANDO WEBDRIVER-----------")
        except Exception as e:
            Logs.log_fail("-----------ERRO AO SAIR COM SEGURANÇA DO ECAC-----------")
            Logs.log_fail(e)

    @staticmethod
    def initiateWebDriver(sb, downloadsPath):
        try:
            Logs.log_step("-----------INICIALIZANDO WEBDRIVER-----------")
            sb.execute_cdp_cmd("Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath" : downloadsPath
            })
            sb.disconnect()
            sb.activate_cdp_mode("https://servicos.receitafederal.gov.br/servico/autorizacoes/minhas-autorizacoes")


            Logs.log_step("-----------WEBDRIVER INICIALIZADO-----------")

            return sb
        except Exception as e:
            Logs.log_fail('WEBDRIVER NÃO PÔDE SER INICIALIZADO')
            Logs.log_fail(e)
        
    def clickEntrarComGovBr(driver):
        btn_xpath = '//*[@id="frmLogin"]/p/input[2]'
        if driver.is_element_visible(btn_xpath, by="xpath"):
            driver.click(btn_xpath, by="xpath")
            driver.sleep(2)

    #Verificar Telas
    def isGovBrIntermediatePage(driver):
        return driver.is_text_visible("Autenticação")


    @staticmethod
    def loginECAC(driver):
        try:
            driver.cdp.click_if_visible('/html/body/div[2]/div/div[2]/div/form/div[2]/p[2]/input')
            Logs.log_step("-----------BOTÃO DE LOGIN COM CERTIFICADO CLICADO-----------")
        except Exception as e:
            Logs.log_fail("-----------ERRO AO CLICAR NO BOTÃO DE LOGIN COM CERTIFICADO-----------")
            raise Exception(f"Erro ao clicar no botão de login: {e}")

        sleep(5)
        driver.cdp.click_if_visible('//*[@id="login-certificate"]')
        Logs.log_step("-----------CLICANDO BOTÃO CERTIFICADO-----------")
        driver.cdp.sleep(random.uniform(2,3))

        # yesCaptchaHandler(driver)
        driver.cdp.sleep(random.uniform(2,3))

        max_tries = 0
        success = False

        while max_tries < 5 and not success:
            try:
                driver.cdp.find_element('//*[@id="botao-nova-autorizacao"]')
               
                Logs.log_sucess("-----------LOGIN REALIZADO COM SUCESSO-----------")
                success = True
                
                if driver.is_element_visible("//body[@class='neterror']"):
                    raise Exception("Erro de rede detectado após login.")

            except Exception as e:
                max_tries += 1
                sleep(3)
                Logs.log_fail(f"Tentativa {max_tries} - Erro ao verificar login com certificado: {e}")
                driver.activate_cdp_mode('https://cav.receita.fazenda.gov.br/autenticacao/login')
                driver.cdp.sleep(random.uniform(3, 5))
                try:
                    driver.cdp.click_if_visible('/html/body/div[2]/div/div[2]/div/form/div[2]/p[2]/input')
                    driver.cdp.sleep(random.uniform(3, 5))
                    driver.cdp.click_if_visible('//*[@id="login-certificate"]')
                    driver.cdp.sleep(random.uniform(10, 12))
                    # yesCaptchaHandler(driver)
                except Exception as inner_e:
                        Logs.log_fail(f"Erro ao tentar refazer login: {inner_e}")
                    

        if not success:
            raise Exception("Falha crítica: Não foi possível realizar o login após 5 tentativas.")
    