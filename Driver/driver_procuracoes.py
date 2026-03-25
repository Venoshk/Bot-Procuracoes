from logs.logs import Logs
from database_manager.BancoDeDados import BancoDeDados
from bs4 import BeautifulSoup
from datetime import datetime
import time
from time import sleep
import json
import sys
import os
import re
import glob
import unicodedata
import PyPDF2 
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

db_instance = BancoDeDados()

class Procuracoes:

    @staticmethod
    def consultar_regime_tributario(cnpj):
        """
        Verifica via Brasil API se a empresa é SN, LP/LR, ou se foi SN nos últimos 5 anos.
        Retorna o nome do regime.
        """
        cnpj_limpo = re.sub(r'\D', '', cnpj)
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"

        for tentativa in range(3):
            try:
                resposta = requests.get(url, timeout=10)
                
                if resposta.status_code == 200:
                    dados = resposta.json()
                    eh_simples = dados.get('opcao_pelo_simples')
                    data_exclusao = dados.get('data_exclusao_do_simples')

                    if eh_simples:
                        return "SIMPLES NACIONAL"
                    
                    if data_exclusao:
                        ano_exclusao = int(data_exclusao[:4])
                        ano_atual = datetime.now().year
                        if (ano_atual - ano_exclusao) <= 5:
                            return "MISTO"
                    
                    return "LUCRO PRESUMIDO/REAL"
                
                elif resposta.status_code == 429:
                    Logs.log_step(f" API sobrecarregada. Respirando antes da tentativa {tentativa + 2}...")
                    sleep(3) 
                    continue
                    
                else:
                    Logs.log_fail(f"API retornou status {resposta.status_code} para {cnpj}.")
                    return "FALHA NA API ou CNPJ INVÁLIDO"
                    
            except requests.exceptions.Timeout:
                Logs.log_fail(f" API demorou muito para responder (Tentativa {tentativa + 1}/3) para {cnpj}.")
                sleep(2)
                
            except Exception as e:
                Logs.log_fail(f"Erro de conexão (Tentativa {tentativa + 1}/3) para {cnpj}: {e}")
                sleep(2)
                
        Logs.log_fail(f"Desistindo do CNPJ {cnpj} após 3 tentativas. Usando Fallback MISTO.")
        return "ERRO API (Fallback para Misto)"

    @staticmethod
    def auditar_poderes(texto_completo_documento, codigos_encontrados, checklist_alvo_codigos):
        texto_minusculo = texto_completo_documento.lower()
        
        # Verifica se é uma procuração que dá poderes totais
        if "todos os serviços existentes e os que vierem a permitir autorização" in texto_minusculo or \
           "todos os serviços existentes e os que vierem a ser disponibilizados" in texto_minusculo:
            return "Todos os poderes confere (Procuração Ampla)"

        poderes_faltantes = []
        
        # Como as duas listas agora são números limpos ('00132'), a comparação é direta
        for codigo_esperado in checklist_alvo_codigos:
            if codigo_esperado not in codigos_encontrados:
                poderes_faltantes.append(codigo_esperado)

        if not poderes_faltantes:
            return "Todos os poderes confere"
        else:
            return f"Faltam {len(poderes_faltantes)} códigos: " + " | ".join(poderes_faltantes)

    @staticmethod
    def montar_item(nome, cnpj, data_validade, situacao, poderes, regime_detectado="N/A")-> dict:
        return {
            "Razão Social": nome,
            "CNPJ": cnpj,
            "Regime": regime_detectado,
            "Validade": data_validade,
            "Situação": situacao,
            "Poderes": poderes
        }
    
    @staticmethod
    def tabelaRecebidas(driver , download_dir):
        try:
            btn_xpath = "//button[.//span[normalize-space()='Recebidas']]"
            driver.scroll_to(btn_xpath, by="xpath")
            driver.click(btn_xpath, by="xpath")
            driver.sleep(3)
            Logs.log_step("-----------CLICANDO NA TABELA RECEBIDAS---------")
            
            sleep(3)
            
            Procuracoes.abrirFiltrosRecebidas(driver, download_dir)
        except Exception as e:
            Logs.log_fail(f"Erro ao clicar na tabela Recebidas: {e}")
    
    @staticmethod
    def abrirFiltrosRecebidas(driver, download_dir):
        try:
            btn_css = "#botao-mostrar-filtros-recebidas"
            driver.wait_for_element_visible(btn_css, timeout=10)
            driver.scroll_to(btn_css)
            driver.click(btn_css)
            driver.sleep(2)
            Logs.log_step("-----------FILTROS DE RECEBIDAS ABERTOS---------")
            
            sleep(3)
            
            Procuracoes.clicarFiltrarRecebidas(driver, download_dir)
        except Exception as e:
            Logs.log_fail(f"Erro ao abrir filtros: {e}")

    @staticmethod
    def clicarFiltrarRecebidas(driver, download_dir):
        try:
            btn_css = "#botao-filtrar-recebidas"
            driver.wait_for_element_visible(btn_css, timeout=10)
            driver.scroll_to(btn_css)
            driver.click(btn_css)
            Logs.log_step("-----------CLICANDO EM FILTRAR (RECEBIDAS)---------")
            
            sleep(3)
            
            Procuracoes.alterarQuantidade(driver, download_dir)
            
        except Exception as e:
            Logs.log_fail(f"Erro ao clicar no botão Filtrar: {e}")
            
    @staticmethod
    def alterarQuantidade(driver, download_dir):
        try:
           xpath = "//ngx-datatable//br-pagination-table//ng-select//span"
           driver.click(xpath)
           
           sleep(3)
           
           Procuracoes.extrair_dados_da_pagina(driver, download_dir)
           
        except Exception as e:
            Logs.log_fail(f"Erro ao clicar no botao de altera quantidade {e}")
    
    @staticmethod
    def extrair_dados_da_pagina(driver , download_dir):
        Procuracoes.limpar_pasta_downloads(download_dir)

        html_content = driver.get_page_source()
        soup = BeautifulSoup(html_content, 'html.parser')
        cnpjs_com_erro = []
        tabelas = soup.find_all('ngx-datatable')

        if len(tabelas) >= 2:
            segunda_tabela = tabelas[1]
            linhas = segunda_tabela.find_all('datatable-body-row')
            Logs.log_sucess(f"Encontradas {len(linhas)} linhas na segunda tabela.")
        else:
            Logs.log_fail(f"Atenção: Não foi encontrada uma segunda tabela.")
            return []
        
        contador_pulos_consecutivos = 0 
        for i, linha in enumerate(linhas):
            item = {}
            try:
                count = i + 1
                celulas = linha.find_all('datatable-body-cell')
                
                if len(celulas) < 5 : continue

                tag_nome = celulas[1].find('span')
                nome = tag_nome.get('title') if tag_nome else "N/A"
                
                tag_cnpj = celulas[2].find('span')
                cnpj = tag_cnpj.get('title') if tag_cnpj else "N/A"
                
                tag_data = celulas[3].find('span')
                data_validade = tag_data.get('title') if tag_data else "N/A"

                tag_situacao = celulas[4].find('app-tag-situacao')
                situacao = tag_situacao.get_text(strip=True) if tag_situacao else "Desconhecido"

                if db_instance.procuracao_ja_processada(cnpj, data_validade):
                    Logs.log_step(f"Procuração de {cnpj} com validade {data_validade} já processada. Pulando.")
                    contador_pulos_consecutivos += 1
                    if contador_pulos_consecutivos >= 10:
                        Logs.log_sucess("Pulei 10 procuracoes consecutivas. Encerrando para evitar bloqueio.")
                        break
                    continue

                # Pega o regime da API ou Banco e a lista de códigos alvo
                nome_regime, checklist_correto = Procuracoes.obter_regime_e_checklist(cnpj)
                Logs.log_step(f"Regime detectado para {cnpj}: {nome_regime}")

                xpath_dinamico = f"//datatable-body-row[contains(., '{cnpj}')]//app-action-button[@texto='Visualizar']//button"

                classificacao_poder = "Não Baixado"
                
                for tentativa in range(2):
                    try:
                        Procuracoes.limpar_pasta_downloads(download_dir)
                        classificacao_poder = None

                        if driver.is_element_visible(xpath_dinamico, by="xpath"):
                            driver.scroll_to(xpath_dinamico, by="xpath")
                            driver.js_click(xpath_dinamico, by="xpath")

                            dados_modal = Procuracoes.validar_modal(driver, checklist_correto)
                            if dados_modal:
                                classificacao_poder = dados_modal
                            else:
                                arquivo = Procuracoes.aguardar_download(timeout=15, download_dir=download_dir)
                                if arquivo:
                                    classificacao_poder = Procuracoes.ler_poderes_do_pdf(arquivo, checklist_correto)

                        if classificacao_poder:
                            break 
                            
                    except Exception as e_click:
                        Logs.log_fail(f"Erro na tentativa {tentativa + 1} para {cnpj}: {e_click}")
                        sleep(2)

                if not classificacao_poder:
                    classificacao_poder = "ERRO NA EXTRAÇÃO (Modal/PDF falhou)"
                    cnpjs_com_erro.append({"cnpj": cnpj, "erro": "Falha na extração", "data": str(datetime.now())})

                item = Procuracoes.montar_item(nome, cnpj, data_validade, situacao, classificacao_poder, nome_regime)
                db_instance.salvar_procuracao(item)
                Logs.log_sucess(f"Processando linha {count}/{len(linhas)} concluída: {cnpj} salvo!")

            except Exception as e:
                print(f"Erro crítico na linha {i}: {e}")
                cnpjs_com_erro.append({"cnpj": cnpj if 'cnpj' in locals() else "Unknown", "erro": str(e)})

        # --- Gera Relatório de Erros JSON ---
        if cnpjs_com_erro:
            arquivo_erros = "erros_classificacao.json"
            
            if os.path.exists(arquivo_erros):
                with open(arquivo_erros, 'r', encoding='utf-8') as f:
                    try:
                        lista_atual = json.load(f)
                    except:
                        lista_atual = []
            else:
                lista_atual = []
            
            lista_atual.extend(cnpjs_com_erro)
            
            with open(arquivo_erros, 'w', encoding='utf-8') as f:
                json.dump(lista_atual, f, indent=4, ensure_ascii=False)
            
            Logs.log_fail(f"Relatório de erros salvo em {arquivo_erros}")

        return Logs.log_sucess("Processamento concluído!")

    @staticmethod
    def limpar_pasta_downloads(download_dir):
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        files = glob.glob(os.path.join(download_dir, "*"))
        for f in files:
            try:
                os.remove(f)
            except:
                pass

    @staticmethod
    def aguardar_download(timeout=30, download_dir=None):
        fim_tempo = time.time() + timeout
        
        while time.time() < fim_tempo:
            arquivos = glob.glob(os.path.join(download_dir, "*"))
            arquivos_validos = [f for f in arquivos if not f.endswith('.crdownload') and not f.endswith('.tmp')]

            if arquivos_validos:
                return max(arquivos_validos, key=os.path.getctime)
            
            time.sleep(1)
        
        return None

    @staticmethod
    def ler_poderes_do_pdf(caminho_pdf, checklist_alvo_codigos):
        try:
            texto_completo = ""
            with open(caminho_pdf, 'rb') as arquivo:
                leitor_pdf = PyPDF2.PdfReader(arquivo)
                for pagina in leitor_pdf.pages:
                    texto_extraido = pagina.extract_text()
                    if texto_extraido:
                        texto_completo += texto_extraido + "\n"
            
            codigos_encontrados = []
            
            # Tenta achar códigos no formato "Cód.12345" ou "Cód. 12345" dentro do PDF
            padrao = r'Cód\.\s*(\d+)'
            matches = re.findall(padrao, texto_completo)
            if matches:
                codigos_encontrados.extend(matches)
                
            # Se a procuração for ampla, a gente sinaliza pro auditor
            if "todos os serviços existentes" in texto_completo.lower():
                codigos_encontrados.append("AMPLA")

            resultado_auditoria = Procuracoes.auditar_poderes(texto_completo, codigos_encontrados, checklist_alvo_codigos)
            return resultado_auditoria
            
        except Exception as e:
            return f"Erro ao ler PDF e auditar: {e}"
        
    @staticmethod
    def validar_modal(sb, checklist_alvo_codigos):
        modal_selector = "app-modal-visualizar"
        botao_fechar = "#botao-superior-fechar"

        if sb.is_element_visible(modal_selector):
            Logs.log_step("--- Modal detectado. Extraindo códigos... ---")
            
            resultado_auditoria = None 
            
            try:
                sleep(1) 
                
                html_modal = sb.get_attribute(modal_selector, "innerHTML")
                soup = BeautifulSoup(html_modal, 'html.parser')
                texto_completo = soup.get_text(" ").lower()
                
                codigos_extraidos = [] 
                
                lista_sistemas = soup.find('ol', class_='lista-sistemas')
                
                if lista_sistemas:
                    itens = lista_sistemas.find_all('li')
                    for item in itens:
                        span_codigo = item.find('span', class_='hint-codigo-sistema')
                        if span_codigo:
                            texto_codigo = span_codigo.get_text(strip=True)
                            match = re.search(r'\d+', texto_codigo)
                            if match:
                                numero_limpo = match.group(0)
                                codigos_extraidos.append(numero_limpo)
                
                if "todos os serviços existentes" in texto_completo:
                    codigos_extraidos.append("AMPLA")

                resultado_auditoria = Procuracoes.auditar_poderes(texto_completo, codigos_extraidos, checklist_alvo_codigos)
                
            except Exception as e_extract:
                Logs.log_fail(f"Erro na hora de ler os códigos do modal: {e_extract}")

            try:
                sb.js_click(botao_fechar)
                sb.wait_for_element_not_visible(modal_selector, timeout=5) 
            except Exception as e_close:
                Logs.log_fail(f"Aviso: O site demorou para fechar o modal: {e_close}")
                try:
                    sb.execute_script(f"var modal = document.querySelector('{modal_selector}'); if(modal) modal.remove();")
                    sb.execute_script("var backdrop = document.querySelector('.modal-backdrop'); if(backdrop) backdrop.remove();")
                    sleep(1)
                except Exception as e_force:
                    print(f"Não consegui fechar a janela à força: {e_force}")

            return resultado_auditoria
                
        return None
    
    @staticmethod
    def obter_regime_e_checklist(cnpj):
        Logs.log_step(f" Procuração detectada para {cnpj}. Consultando Brasil API...")
        sleep(1) 
        nome_regime = Procuracoes.consultar_regime_tributario(cnpj)
        
        if "ERRO" in nome_regime or "FALHA" in nome_regime:
            Logs.log_step(f"API indisponível. Buscando histórico no banco para {cnpj}...")
            try:
                regime_salvo = db_instance.buscar_regime_da_empresa(cnpj)
                if regime_salvo:
                    nome_regime = regime_salvo 
            except Exception as e:
                Logs.log_fail(f"Aviso: Falha ao checar o banco para {cnpj}: {e}")

        # Busca os códigos cadastrados no banco para o regime detectado
        checklist_correto = db_instance.buscar_checklist_por_regime(nome_regime)
        return nome_regime, checklist_correto