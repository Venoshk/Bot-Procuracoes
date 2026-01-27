from logs.logs import Logs
import random
from time import sleep
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database_manager.BancoDeDados import BancoDeDados
from bs4 import BeautifulSoup

db_instance = BancoDeDados()

class Procuracoes:
    
    
    
    @staticmethod
    def tabelaRecebidas(driver):
        try:
            btn_xpath = "//button[.//span[normalize-space()='Recebidas']]"
            driver.scroll_to(btn_xpath, by="xpath")
            driver.click(btn_xpath, by="xpath")
            driver.sleep(3)
            Logs.log_step("-----------CLICANDO NA TABELA RECEBIDAS---------")
            
            sleep(3)
            
            Procuracoes.abrirFiltrosRecebidas(driver)
        except Exception as e:
            Logs.log_fail(f"Erro ao clicar na tabela Recebidas: {e}")
    
    @staticmethod
    def abrirFiltrosRecebidas(driver):
        try:
            btn_css = "#botao-mostrar-filtros-recebidas"
            driver.wait_for_element_visible(btn_css, timeout=10)
            driver.scroll_to(btn_css)
            driver.click(btn_css)
            driver.sleep(2)
            Logs.log_step("-----------FILTROS DE RECEBIDAS ABERTOS---------")
            
            sleep(3)
            
            Procuracoes.clicarFiltrarRecebidas(driver)
        except Exception as e:
            Logs.log_fail(f"Erro ao abrir filtros: {e}")

    @staticmethod
    def clicarFiltrarRecebidas(driver):
        try:
            btn_css = "#botao-filtrar-recebidas"
            driver.wait_for_element_visible(btn_css, timeout=10)
            driver.scroll_to(btn_css)
            driver.click(btn_css)
            # NÃO use sleep aqui, deixamos o listener esperar a rede
            Logs.log_step("-----------CLICANDO EM FILTRAR (RECEBIDAS)---------")
            
            sleep(3)
            
            Procuracoes.alterarQuantidade(driver)
            
            
            
        except Exception as e:
            Logs.log_fail(f"Erro ao clicar no botão Filtrar: {e}")
            
    
    @staticmethod
    def alterarQuantidade(driver):
        try:
           xpath = "//ngx-datatable//br-pagination-table//ng-select//span"
           driver.click(xpath)
           
           sleep(3)
           
           Procuracoes.extrair_dados_da_pagina(driver)
           
        except Exception as e:
            Logs.log_fail(f"Erro ao clicar no botao de altera quantidade {e}")
    
    @staticmethod
    def extrair_dados_da_pagina(driver):
        
        html_content = driver.get_page_source()
        soup = BeautifulSoup(html_content, 'html.parser')
        dados_capturados = []
        tabelas = soup.find_all('ngx-datatable')

        
        if len(tabelas) >= 2:
            segunda_tabela = tabelas[1]
            
            
            linhas = segunda_tabela.find_all('datatable-body-row')
            
            Logs.log_sucess(f"Encontradas {len(linhas)} linhas na segunda tabela.")
        else:
            Logs.log_fail(f"Atenção: Não foi encontrada uma segunda tabela. Total de tabelas: {len(tabelas)}")
            return dados_capturados
        

        for linha in linhas:
            try:
                
                celulas = linha.find_all('datatable-body-cell')
                
                if len(celulas) < 5:
                    continue

                
                tag_nome = celulas[1].find('span')
                nome = tag_nome.get('title') if tag_nome else "N/A"

                
                tag_cnpj = celulas[2].find('span')
                cnpj = tag_cnpj.get('title') if tag_cnpj else "N/A"

                
                tag_data = celulas[3].find('span')
                data_validade = tag_data.get('title') if tag_data else "N/A"

               
                tag_situacao = celulas[4].find('app-tag-situacao')
                situacao = tag_situacao.get_text(strip=True) if tag_situacao else "Desconhecido"

                item = {
                    "Razão Social": nome,
                    "CNPJ": cnpj,
                    "Validade": data_validade,
                    "Situação": situacao
                }
                
                db_instance.salvar_procuracao(item)
            except Exception as e:
                print(f"Erro ao processar uma linha: {e}")

        return Logs.log_sucess("As procurações foram salvas com suceeso no banco!")