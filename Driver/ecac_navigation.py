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
    
    # === 1. CHECKLIST: APENAS LUCRO PRESUMIDO / REAL ===
    CHECKLIST_LP_LR = [
        "e-AssinaRFB", "eSocial - Download", "eSocial - Grupo Acesso WEB", "eSocial - Grupo Desligamento", 
        "eSocial - Grupo Especial", "eSocial - Grupo Preliminar", "eSocial - Grupo Rotinas", "eSocial - Grupo SST", 
        "eSocial - Processo Trabalhista", "Acessar o sistema DCTFWeb", "Acessar o Programa Especial de Regularização Tributária - PERT",
        "Acessar Programa Especial de Regularização Tributária - PERT - Débito Previdenciário", "Acessar PER/DCOMP WEB",
        "Aplicações PGFN - Parcelamento Simplificado", "Aplicações PGFN - Requerimento para exclusão da Lista de Devedores",
        "Assinatura da Escrituração Fiscal Digital - EFD ICMS IPI", "Atualização de Dados Bancários p/ Restituição e Ressarcimento",
        "Cadastro CNPJ - Consulta Situação do Pedido", "Caixa Postal - Mensagens", "Caixa Postal - Termo de Opção pelo Domicilio Tributário Eletrônico",
        "Compensação a pedido do Simples Nacional", "Comunicação para Compensação de Oficio", "Consulta Pendências - Inclusão no Cadin/Sisbacen pela RFB",
        "CHATRFB-Todos os serviços disponiveis no canal de atendimento", "Cópia de Declaração", "Declarações - DCTF (Acesso ao conteúdo da declaração, extrato e 2a via do recibo)",
        "Declarações - DIRF (Acesso ao conteúdo da declaração, extrato e 2a via do recibo)", "Desistência de Parcelamentos Anteriores",
        "Download da Escrituração Contábil Digital (SPED-ECD) utilizando o Receitanet Bx", "Download da Escrituração Fiscal Digital (SPED-EFD) utilizando o Receitanet Bx",
        "Download de EFD-PIS/Cofins através do ReceitaNetBX", "Emissão de DAS Avulso", "Entregar Arquivo de Dados - Obrigação Acessória",
        "Extrato Malha Fiscal Pessoa Juridica", "EFD-Reinf - Geral", "Intimação DCTF", "Isenções e Regimes Especiais", 
        "Notificações e Autos relativos  entrega de declarações", "Notificações em Auditoria de Compensação em GFIP", "Pagamento e Parcelamento Lei nº 12.996/2014",
        "Pagamentos - Comprovante de Arrecadação", "Pagamentos - Retificação de Documento de Arrecadação - Redarf Net",
        "Parcelamento - Solicitar e acompanhar", "Parcelamento de Débitos", "Parcelamento Simplificado Previdenciário", 
        "Parcelamento Simplificado Previdenciário DAU", "Pedido Eletrônico de Restituição (Simples e Simei)", "Processos Digitais e Requerimentos Web",
        "Programa de Regularização Tributária-Demais Débitos", "PER/DCOMP- Consulta Despacho Decisório", "PGF - Consulta Débitos inscritos a partir de 01/11/2012",
        "PGFN - Consulta Débitos inscritos a partir de 01/11/2012", "Retificação de GPS.", "Sief Cobrança - Intimações DCTF",
        "Sistema de Ajuste de Documentos de Arrecadação - SISTAD", "Situação Fiscal do Contribuinte", "Solicitar, acompanhar e emitir DAS de parcelamento",
        "SPED ECD - Central de Balanços.", "SPED-ECF (Escrituração Contábil Fiscal)", "Transmissão de Declarações/Arquivos, inclusive todos do CNPJ, com Assinatura Digital via Receitanet"
    ]

    # === 2. CHECKLIST: SIMPLES NACIONAL ===
    CHECKLIST_SN = [
        "eSocial - Download", "eSocial - Grupo Acesso WEB", "eSocial - Grupo Desligamento", "eSocial - Grupo Especial", 
        "eSocial - Grupo Preliminar", "eSocial - Grupo Rotinas", "eSocial - Grupo SST", "Acessar o sistema DCTFWeb",
        "Acessar o Programa Especial de Regularização Tributária - PERT", "Acessar Programa Especial de Regularização Tributária - PERT Débito Previdenciário",
        "Acessar PER/DCOMP WEB", "Aplicações PGFN - Parcelamento Simplificado", "Aplicações PGFN - Requerimento para exclusão da Lista de Devedores",
        "Assinatura da Escrituração Fiscal Digital EFD ICMS IPI", "Atualização de Dados Bancários p/ Restituição e Ressarcimento",
        "Cadastro CNPJ - Consulta Situação do Pedido", "Caixa Postal Mensagens", "Caixa Postal Termo de Opção pelo Domicilio Tributário Eletrônico",
        "Compensação a pedido do Simples Nacional", "Comunicação para Compensação de Oficio", "Consulta Ação Fiscal do Simples Nacional",
        "Consulta Pendências - Inclusão no Cadin/Sisbacen pela RFB", "Contribuinte Diferenciado e-MAC (Sistema de Comunicação Eletrônica)",
        "Contribuinte Diferenciado - Consulta Participação no Acompanhamento Diferenciado", "Contribuinte Diferenciado Pessoas de Contato",
        "CHATRFB-Todos os serviços disponíveis no canal de atendimento", "Cópia de Declaração", "Declarações - DCTF", "Declarações - DIRF",
        "Desistência de Parcelamentos Anteriores", "Download da Escrituração Contábil Digital (SPED-ECD)", "Download da Escrituração Fiscal Digital (SPED-EFD)",
        "Download de EFD-PIS/Cofins", "Download dos arquivos SPED Dados Agregados", "Emissão de DAS Avulso", "Entregar Arquivo de Dados Obrigação Acessória",
        "Extrato Malha Fiscal Pessoa Jurídica", "EFD-Reinf - Geral", "Isenções e Regimes Especiais", "Notificações e Autos relativos  entrega de declarações",
        "Notificações em Auditoria de Compensação em GFIP", "Paex Lei 13.988", "Pagamento e Parcelamento Lei nº 12.996/2014",
        "Pagamentos Retificação de Documento de Arrecadação - Redarf Net", "Parcelamento - Solicitar e acompanhar", "Parcelamento de Débitos",
        "Parcelamento de Débitos do Simples Nacional", "Parcelamento Especial Opções da Lei 11.941/2009", "Parcelamento Especial Simples Nacional",
        "Parcelamento Simplificado Previdenciário", "Parcelamento Simplificado Previdenciário DAU", "Parcelar dívidas do SN pela LC 193/2022 (RELP)",
        "Pedido Eletrônico de Restituição (Simples e Simei)", "Piloto da CBS na Reforma Tributária sobre o Consumo", "Processos Digitais e Requerimentos Web",
        "Programa de Regularização Tributária-Demais Débitos", "Programa Especial de Regularização Tributária - PERT-MEI", "PER/DCOMP- Consulta Despacho Decisório",
        "PER/DCOMP-Consulta Intimação", "PER/DCOMP-Consulta Processamento", "PGDAS-D a partir de 01/2018", "PGF Consulta Débitos",
        "PGFN- Consulta Débitos", "Retificação de GPS", "Sief Cobrança Intimações DCTF", "Simples Nacional - Acompanhamento Opção",
        "Simples Nacional Agendamento de Opção", "Simples Nacional Alerta Avisos", "Simples Nacional Consulta Débitos Sivex",
        "Simples Nacional Consulta Declaração Transmitida", "Simples Nacional - Emissão de DAS de Auto de Infração",
        "Sistema de Ajuste de Documentos de Arrecadação SISTAD", "Situação Fiscal do Contribuinte", "Solicitar, acompanhar e emitir DAS de parcelamento",
        "SPED ECD Central de Balanços", "Transmissão de Declarações/Arquivos"
    ]

    # === 3. CHECKLIST: MISTO (LP/LR que foi SN nos últimos 5 anos) ===
    CHECKLIST_MISTO = [
        "eSocial - Download", "eSocial - Grupo Acesso WEB", "eSocial - Grupo Desligamento", 
        "eSocial - Grupo Especial", "eSocial - Grupo Preliminar", "eSocial - Grupo Rotinas", 
        "eSocial - Grupo SST", "eSocial - Processo Trabalhista", "Acessar o sistema DCTFWeb", 
        "Acessar o Programa Especial de Regularização Tributária - PERT", 
        "Acessar Programa Especial de Regularização Tributária - PERT - Débito Previdenciário", 
        "Acessar PER/DCOMP WEB", "Aplicações PGFN - Parcelamento Simplificado", 
        "Aplicações PGFN - Requerimento para exclusão da Lista de Devedores", 
        "Assinatura da Escrituração Fiscal Digital - EFD ICMS IPI", 
        "Atualização de Dados Bancários p/ Restituição e Ressarcimento", 
        "Cadastro CNPJ - Consulta Situação do Pedido", "Caixa Postal - Mensagens", 
        "Caixa Postal - Termo de Opção pelo Domicilio Tributário Eletrônico", 
        "Compensação a pedido do Simples Nacional", "Comunicação para Compensação de Oficio", 
        "Consulta Ação Fiscal do Simples Nacional", "Consulta Pendências - Inclusão no Cadin/Sisbacen pela RFB", 
        "CHATRFB-Todos os serviços disponiveis no canal de atendimento", "Cópia de Declaração", 
        "Declarações - DCTF", "Declarações - DIRF", "Desistência de Parcelamentos Anteriores", 
        "Download da Escrituração Contábil Digital (SPED-ECD)", "Download da Escrituração Fiscal Digital (SPED-EFD)", 
        "Download de EFD-PIS/Cofins através do ReceitaNetBX", "Emissão de DAS Avulso", 
        "Entregar Arquivo de Dados - Obrigação Acessória", "Extrato Malha Fiscal Pessoa Juridica", 
        "EFD-Reinf - Geral", "Intimação DCTF", "Isenções e Regimes Especiais", 
        "Notificações e Autos relativos  entrega de declarações", "Notificações em Auditoria de Compensação em GFIP", 
        "Pagamento e Parcelamento Lei nº 12.996/2014", "Pagamentos - Comprovante de Arrecadação", 
        "Pagamentos - Retificação de Documento de Arrecadação - Redarf Net", 
        "Parcelamento - Solicitar e acompanhar", "Parcelamento de Débitos", 
        "Parcelamento de Débitos do Simples Nacional", "Parcelamento Especial - Opções da Lei 11.941/2009", 
        "Parcelamento Especial Simples Nacional", "Parcelamento Simplificado Previdenciário", 
        "Parcelamento Simplificado Previdenciário DAU", "Parcelar dívidas do SN pela LC 193/2022 (RELP)", 
        "Pedido Eletrônico de Restituição (Simples e Simei)", "Piloto de CBS na Reforma Tributária sobre o Consumo", 
        "Processos Digitais e Requerimentos Web", "Programa de Regularização Tributária-Débitos Previdenciários", 
        "Programa de Regularização Tributária-Demais Débitos", "Programa Especial Regularização Tributária - PERT-SN", 
        "PER/DCOMP- Consulta Análise Preliminar/Autorregularização", "PER/DCOMP- Consulta Despacho Decisório", 
        "PER/DCOMP- Consulta Intimação", "PER/DCOMP- Consulta Processamento", "PGDAS-D- a partir de 01/2018", 
        "PGF - Consulta Débitos inscritos a partir de 01/11/2012", "PGFN - Consulta Débitos inscritos a partir de 01/11/2012", 
        "Retificação de GPS.", "Sief Cobrança - Intimações DCTF", "Simples Nacional - Acompanhamento Opção", 
        "Simples Nacional - Agendamento de Opção", "Simples Nacional - Alerta - Avisos e comunicações para o contribuinte", 
        "Simples Nacional - Consulta Débitos Sivex", "Simples Nacional - Consulta Declaração Transmitida", 
        "Sistema de Ajuste de Documentos de Arrecadação - SISTAD", "Situação Fiscal do Contribuinte", 
        "Solicitar, acompanhar e emitir DAS de parcelamento", "SPED ECD - Central de Balanços.", 
        "SPED-ECF (Escrituração Contábil Fiscal)", "SPED-ECF-Download - Download via ReceitanetBX", 
        "Transmissão de Declarações/Arquivos, inclusive todos do CNPJ"
    ]

    @staticmethod
    def _normalizar_texto(texto):
        texto = str(texto).lower().strip()
        # Remove acentuação
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
        return texto

    @staticmethod
    def consultar_regime_tributario(cnpj):
        """
        Verifica via Brasil API se a empresa é SN, LP/LR, ou se foi SN nos últimos 5 anos.
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
                        return "SIMPLES NACIONAL", Procuracoes.CHECKLIST_SN
                    
                    if data_exclusao:
                        ano_exclusao = int(data_exclusao[:4])
                        ano_atual = datetime.now().year
                        if (ano_atual - ano_exclusao) <= 5:
                            return "MISTO", Procuracoes.CHECKLIST_MISTO
                    
                    return "LUCRO PRESUMIDO/REAL", Procuracoes.CHECKLIST_LP_LR
                
                
                elif resposta.status_code == 429:
                    Logs.log_step(f" API sobrecarregada. Respirando antes da tentativa {tentativa + 2}...")
                    sleep(3) 
                    continue
                    
                else:
                    
                    Logs.log_fail(f"API retornou status {resposta.status_code} para {cnpj}.")
                    return "FALHA NA API ou CNPJ INVÁLIDO", Procuracoes.CHECKLIST_MISTO
                    
            except requests.exceptions.Timeout:
                Logs.log_fail(f" API demorou muito para responder (Tentativa {tentativa + 1}/3) para {cnpj}.")
                sleep(2)
                
            except Exception as e:
                Logs.log_fail(f"Erro de conexão (Tentativa {tentativa + 1}/3) para {cnpj}: {e}")
                sleep(2)
                
        Logs.log_fail(f"Desistindo do CNPJ {cnpj} após 3 tentativas. Usando Fallback MISTO.")
        return "ERRO API (Fallback para Misto)", Procuracoes.CHECKLIST_MISTO

    @staticmethod
    def auditar_poderes(texto_completo_documento, lista_linhas_extraidas, checklist_alvo):
        texto_minusculo = texto_completo_documento.lower()
        
        if "todos os serviços existentes e os que vierem a permitir autorização" in texto_minusculo or \
           "todos os serviços existentes e os que vierem a ser disponibilizados" in texto_minusculo:
            return "Todos os poderes confere (Procuração Ampla)"

        poderes_encontrados_normalizados = []
        for linha in lista_linhas_extraidas:
            if linha and linha[0].isdigit():
                partes = linha.split(".", 1)
                if len(partes) > 1:
                    linha = partes[1]
            poderes_encontrados_normalizados.append(Procuracoes._normalizar_texto(linha))

        poderes_faltantes = []
        for poder_esperado in checklist_alvo:
            esperado_norm = Procuracoes._normalizar_texto(poder_esperado)
            encontrado = any(esperado_norm in poder_encontrado for poder_encontrado in poderes_encontrados_normalizados)
            
            if not encontrado:
                poderes_faltantes.append(poder_esperado)

        if not poderes_faltantes:
            return "Todos os poderes confere"
        else:
            return f"Faltam {len(poderes_faltantes)} poderes: " + " | ".join(poderes_faltantes)

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
                        Logs.log_sucess("Pulei 10 procuracoes consecutivas. Provavelmente cheguei em um ponto já processado. Encerrando para evitar bloqueio.")
                        break
                    continue

                # === Bate na API para definir qual é a lista correta para este CNPJ ===
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
                            item = Procuracoes.montar_item(nome, cnpj, data_validade, situacao, classificacao_poder, nome_regime)
                            
                            db_instance.salvar_procuracao(item)
                            Logs.log_sucess(f"Sucesso: {cnpj} processado ({'Modal' if 'Modal' in classificacao_poder else 'PDF'})")
                            Logs.log_sucess(f"Processando linha {count}/{len(linhas)}: {cnpj}")
                            break 
                            
                        else:
                            if tentativa == 1: 
                                Logs.log_fail(f"Falha total ao processar {cnpj}")
                                cnpjs_com_erro.append({"cnpj": cnpj, "erro": "Timeout Modal/Download", "data": str(datetime.now())})
                                
                    except Exception as e_click:
                        Logs.log_fail(f"Erro na tentativa {tentativa + 1} para {cnpj}: {e_click}")
                        sleep(2)

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
    def ler_poderes_do_pdf(caminho_pdf, checklist_alvo):
        try:
            texto_completo = ""
            with open(caminho_pdf, 'rb') as arquivo:
                leitor_pdf = PyPDF2.PdfReader(arquivo)
                for pagina in leitor_pdf.pages:
                    texto_extraido = pagina.extract_text()
                    if texto_extraido:
                        texto_completo += texto_extraido + "\n"
            
            linhas_uteis = []
            termo = "Serviços Autorizados"
            if termo.lower() in texto_completo.lower():
                indice_inicio = texto_completo.lower().find(termo.lower()) + len(termo)
                conteudo = texto_completo[indice_inicio:]
                
                for linha in conteudo.split('\n'):
                    linha = linha.strip()
                    if not linha: continue
                    if " de 20" in linha and ("Janeiro" in linha or "Fevereiro" in linha or "Março" in linha or "Abril" in linha or "Maio" in linha or "Junho" in linha or "Julho" in linha or "Agosto" in linha or "Setembro" in linha or "Outubro" in linha or "Novembro" in linha or "Dezembro" in linha):
                        break
                    
                    if linha and linha[0].isdigit():
                        linhas_uteis.append(linha)

            # === Passando o checklist certo pra auditoria ===
            return Procuracoes.auditar_poderes(texto_completo, linhas_uteis, checklist_alvo)
            
        except Exception as e:
            return f"Erro ao ler PDF e auditar: {e}"
        
    @staticmethod
    def validar_modal(sb, checklist_alvo):
        modal_selector = "app-modal-visualizar"
        seletor_corpo = "div.modal-body dl" 
        botao_fechar = "#botao-superior-fechar"

        if sb.is_element_visible(modal_selector):
            Logs.log_step("--- Modal detectado. Extraindo informações para auditoria... ---")
            
            try:
                sleep(1) 
                
                html_modal = sb.get_attribute(seletor_corpo, "outerHTML")
                soup = BeautifulSoup(html_modal, 'html.parser')
                
                texto_completo = soup.get_text(separator="\n")
                
                linhas_uteis = []
                termo = "Serviços Autorizados"
                
                if termo.lower() in texto_completo.lower():
                    indice_inicio = texto_completo.lower().find(termo.lower()) + len(termo)
                    conteudo = texto_completo[indice_inicio:]
                else:
                    conteudo = texto_completo
                
                for linha in conteudo.split('\n'):
                    linha = linha.strip()
                    if not linha: continue
                    
                    # Critério de parada na assinatura/rodapé
                    if " de 20" in linha and any(mes in linha for mes in ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]):
                        break
                    
                    
                    if len(linha) > 3: 
                        linhas_uteis.append(linha)

                sb.js_click(botao_fechar)
                sb.wait_for_element_not_visible(modal_selector, timeout=10)
                
                return Procuracoes.auditar_poderes(texto_completo, linhas_uteis, checklist_alvo)
                
            except Exception as e:
                Logs.log_fail(f"Erro ao extrair/auditar dados do modal: {e}")
                
                try:
                    Logs.log_step("Tentando forçar o fechamento do modal via JavaScript...")
                    sb.execute_script(f"var modal = document.querySelector('{modal_selector}'); if(modal) modal.remove();")
                    sb.execute_script("var backdrop = document.querySelector('.modal-backdrop'); if(backdrop) backdrop.remove();")
                    sleep(1)
                except Exception as e_force:
                    print(f"Não foi possível remover o modal à força: {e_force}")
                
        return None
    
    @staticmethod
    def obter_regime_e_checklist(cnpj):
        Logs.log_step(f" Procuração nova detectada para {cnpj}. Consultando Brasil API...")
        sleep(1)
        nome_regime, checklist = Procuracoes.consultar_regime_tributario(cnpj)
        
        if "ERRO" in nome_regime or "FALHA" in nome_regime:
            Logs.log_step(f"⚠️ API indisponível. Buscando histórico no banco para {cnpj}...")
            
            try:
                regime_salvo = db_instance.buscar_regime_da_empresa(cnpj)
                if regime_salvo:
                    regime_upper = str(regime_salvo).upper()
                    if "SIMPLES NACIONAL" in regime_upper:
                        return regime_salvo, Procuracoes.CHECKLIST_SN
                    elif "LUCRO PRESUMIDO" in regime_upper or "REAL" in regime_upper:
                        return regime_salvo, Procuracoes.CHECKLIST_LP_LR
                    elif "MISTO" in regime_upper:
                        return regime_salvo, Procuracoes.CHECKLIST_MISTO
            except Exception as e:
                Logs.log_fail(f"Aviso: Falha ao checar o banco para {cnpj}: {e}")

        return nome_regime, checklist