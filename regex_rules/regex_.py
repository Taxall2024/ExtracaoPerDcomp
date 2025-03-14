import re
import pandas as pd
import calendar


class RegexRules():

    @staticmethod
    def tratar_data_credito(data):
        if 'TRI' in data:
            trimestres = {
                '1º TRI': ('01-01', '03-31'),
                '2º TRI': ('04-01', '06-30'),
                '3º TRI': ('07-01', '09-30'),
                '4º TRI': ('10-01', '12-31')
            }
            for tri, (inicio, fim) in trimestres.items():
                if tri in data:
                    ano = data.split('/')[-1]
                    data_inicial = f'{ano}-{inicio}'
                    data_final = f'{ano}-{fim}'
                    return data_inicial, data_final

        elif any(x in data for x in ['ANUAL', 'Anual']):
            try:
                ano = data.split('/')[-1]
                data_inicial = f'{ano}-01-01'
                data_final = f'{ano}-12-31'
                return data_inicial, data_final
            except Exception:
                return None, None

        else:
            try:
                data = pd.to_datetime(data, dayfirst=True)
                ano = data.year
                mes = data.month
                primeiro_dia = f'{ano}-{mes:02d}-01'
                ultimo_dia = f'{ano}-{mes:02d}-{calendar.monthrange(ano, mes)[1]:02d}'
                return primeiro_dia, ultimo_dia
            except Exception:
                return None, None

    @staticmethod
    def tratar_data_competencia(data):
            try:
                data = data.strip()
                if data.startswith('13/'):
                    ano = data.split('/')[1].strip()
                    return f'{ano}-12-31'
                elif '/' in data:
                    mes, ano = data.split('/')
                    mes = mes.strip()
                    ano = ano.strip()
                    return f'{ano}-{mes.zfill(2)}-01'
                elif data.replace('.0', '').isdigit() and len(data.replace('.0', '')) == 4:
                    ano = data.replace('.0', '')
                    return f'{ano}-01-01'
                return pd.to_datetime(data, dayfirst=True, errors='coerce').strftime('%Y-%m-%d')
            except Exception:
                return None

    @staticmethod
    def extrair_valor_numerico(texto, formatar_para_exibicao=False):
        """
        Converte o texto para um número float, com opção de retornar como string formatada.
        """
        if texto:
            texto = texto.strip()
            texto = texto.replace('.', '').replace(',', '.')
            try:
                valor = float(texto)
                if formatar_para_exibicao:
                    return f"{valor:,.2f}".replace('.', ',')
                return valor
            except ValueError:
                print(f"[ERRO] Não foi possível converter o texto '{texto}' para float.")
        
    @staticmethod
    def extract_info_from_pages(pdf_document):
        info = {
            'cod_cnpj': None,
            'nome_cliente': None,
            'cod_perdcomp': None,
            'data_transmissao': None,
            'tipo_documento': None,
            'tipo_credito': None,
            'perdcomp_retificador': None,
            'cod_perdcomp_retificacao': None,
            'origem_credito_judicial': None,
            'nome_responsavel_preenchimento': None,
            'cod_cpf_preenchimento': None,
            'cod_perdcomp_inicial': None,
            'data_inicial_periodo': None,
            'data_final_periodo': None,
            'data_competencia': None,
            'data_arrecadacao': None, 
            'competencia': None, 
            'numero_documento_arrecadacao': None,
            'valor_saldo_negativo': None,
            'valor_credito_atualizado': None,
            'selic_acumulada': None,
            'csll_devida': None,
            'valor_original_credito_inicial': None,
            'valor_total_debitos_deste_documento': None,
            'valor_total_credito_original_utilizado_documento': None,
            'valor_total_debitos_desta_dcomp': None,
            'valor_total_credito_original_utilizado_dcomp': None,
            'valor_credito_original_data_entrega': None,
            'valor_pedido_restituicao': None,
            'valor_saldo_credito_original': None,
            'cod_perdcomp_cancelado': None,
            'total_parcelas_composicao_credito': None, 
            'imposto_devido': None,
            'grupo_tributo': [],
            'debito_sucedida': [],
            'periodicidade': [],
            'debito_controlado_processo': [],   
            'periodo_apuracao': [],
            'codigos_receita': [],
            'cnpj_detentor_debito': [],
            'numero_recibo_dctfweb': [],
            'data_vencimento_tributo': [],
            'valor_principal_tributo': [],
            'valor_multa_tributo': [],
            'valor_juros_tributo': [],
            'valor_total_tributo': [],
            'data_transmissao_dctfweb': [], 
            'categoria_dcftweb': [],
            'periodicidade_dctfweb': [],   
            'periodo_apuracao_dctfweb': [], 

            'periodo_apuracao_origem_credito': None,
            'cnpj_origem_credito': None,
            'codigo_receita_origem_credito': None,
            'grupo_tributo_origem_credito': None,  
            'valor_principal_origem_credito': None,
            'valor_multa_origem_credito': None,
            'valor_juros_origem_credito': None,
            'valor_total_origem_credito': None,

            'periodo_apuracao_darf': None,
            'cnpj_darf': None,
            'codigo_receita_darf': None,
            'numero_documento_arrecadacao': None,
            'data_vencimento_darf': None,
            'data_arrecadacao_darf': None,
            'valor_principal_darf': None,
            'valor_multa_darf': None,
            'valor_juros_darf': None,
            'valor_total_darf': None,
            'valor_original_credito_darf': None,
            
        }

        page_patterns = {
            0: {
                'cod_cnpj': r"CNPJ \s*([\d./-]+)",
                'cod_perdcomp': r"CNPJ \s*[\d./-]+\s*([\d.]+-[\d.]+)",

                'nome_cliente': r"Nome Empresarial\s*([A-Za-z0-9\s.&-]+?(?:LTDA|ME|EIRELI|SA)\b)",
                #'nome_cliente': r"Nome Empresarial\s*([A-Za-z0-9\s.&-]+?(?:\s(?:LTDA|ME|EIRELI|SA)\b)?)",

                'data_transmissao': r"Data de Transmissão\s*([\d/]+)",
                'tipo_documento': r"Tipo de Documento\s*([\w\s]+?)(?=\s*Tipo de Crédito)",
                'tipo_credito': r"Tipo de Crédito\s*([\w\s]+)(?=\s*PER/DCOMP Retificador)",
                'perdcomp_retificador': r"PER/DCOMP Retificador\s*([\w\s]+?)(?=\n|\.|$)",
                'cod_perdcomp_retificacao': r"N[º°] PER/DCOMP Retificado\s*([\d.]+-[\d.]+)",
                'origem_credito_judicial': r"Crédito Oriundo de Ação Judicial\s*([\w\s]+?)(?=\n|\.|$)",
                'nome_responsavel_preenchimento': r"Nome\s+([\w\s]+)\s+CPF\s+(\d{3}\.\d{3}\.\d{3}-\d{2})",
                'cod_cpf_preenchimento': r"CPF \s*([\d./-]+)",
                'cod_perdcomp_cancelado': r"Número do PER/DCOMP a Cancelar\s*([\d./-]+)"
            },
            1: {
                'nome_responsavel_preenchimento': r"Nome\s+([\w\s]+)\s+CPF\s+(\d{3}\.\d{3}\.\d{3}-\d{2})",
                'cod_cpf_preenchimento': r"CPF \s*([\d./-]+)"
            },

            
            2: {
                'cod_perdcomp_inicial': r"N[º°] do PER/DCOMP Inicial\s*([\d.]+-[\d.]+)",
                'data_inicial_periodo': r"Data Inicial do Período\s*([\d/]+)",
                'data_final_periodo': r"Data Final do Período\s*([\d/]+)",
                'valor_saldo_negativo': r"Valor do Saldo Negativo\s*([\d.,]+)",
                'valor_credito_atualizado': r"Crédito Atualizado\s*([\d.,]+)",
                'valor_saldo_credito_original': r"Saldo do Crédito Original\s*([\d.,]+)",
                'selic_acumulada': r"Selic Acumulada\s*([\d.,]+)",
                'data_competencia': r"(?:1[º°]|2[º°]|3[º°]|4[º°])\s*Trimestre/\d{4}",
                'competencia': r"Competência\s+((?:Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)/\d{4})\s*",
                'valor_credito_original_data_entrega': r"\s*([\d.,]+)Crédito Original na Data da Entrega",
                'total_parcelas_composicao_credito': r"Total das Parcelas de Composição do Crédito\s*([\d.,]+)",
                'valor_original_credito_inicial': r"Valor Original do Crédito Inicial\s*([\d.,]+)",
                'imposto_devido': r"Imposto Devido\s*([\d.,]+)",
                'valor_pedido_restituicao': r"Valor do Pedido de Restituição\s*([\d.,]+)", 
                'valor_total_debitos_deste_documento':r"Total dos Débitos deste Documento\s*([\d.,]+)", 
                'valor_total_credito_original_utilizado_documento': r"Total do Crédito Original [Uu]tilizado neste Documento\s*([\d.,]+)\s",
                'valor_total_debitos_desta_dcomp': r"Total dos débitos desta DCOMP[\s\S]*?(\d{1,3}(?:\.\d{3})*,\d{2})",
                'valor_total_credito_original_utilizado_dcomp': r"Total do Crédito Original [Uu]tilizado nesta DCOMP\s*([\d.,]+)",
                'csll_devida': r"\sCSLL Devida\s([\d.,]+)\s*",

                #Origem do Crédito
                'periodo_apuracao_origem_credito': r"ORIGEM DO CRÉDITO*?\s([\d/]+)\sPeríodo de Apuração",
                'cnpj_origem_credito': r"\s([\d.\/-]+)\sCNPJ do Pagamento\s", 
                'codigo_receita_origem_credito': r"Código da Receita\s(\d{4})",
                'grupo_tributo_origem_credito': r"Grupo de Tributo\s([A-Z]+(?:/[A-Z]+)?(?:,\s[A-Z]+)*)",
                'valor_principal_origem_credito': r"Valor do Principal\s*([\d.,]+)",
                'valor_multa_origem_credito': r"Valor da Multa\s*([\d.,]+)",   
                'valor_juros_origem_credito': r"\s([\d.,]+)\sValor dos Juros", 
                'valor_total_origem_credito': r"Valor Total\s*([\d.,]+)",

                #DARF
                'periodo_apuracao_darf': r"Período de Apuração\s*([\d/]+)\s",
                'cnpj_darf': r"\sCNPJ\s*([\d.\/-]+)\s", 
                'codigo_receita_darf': r"Código da Receita\s*(\d{4})",
                'numero_documento_arrecadacao': r"Número do Documento de Arrecadação\s*([\d.\/-]+)\s", 
                'data_vencimento_darf': r"Data de Vencimento\s*([\d/]+)\s",
                'data_arrecadacao_darf': r"Data da Arrecadação\s*([\d/]+)\s",
                'valor_principal_darf': r"DARF NUMERDADO*?\sData\s+da\s+Arrecadação\s+\d{1,2}/\d{1,2}/\d{4}\s+Valor do Principal\s*([\d.,]+)",
                'valor_multa_darf': r"DARF NUMERDADO*?\sValor da Multa\s*([\d.,]+)", 
                'valor_juros_darf': r"DARF NUMERDADO*?\sValor dos Juros\s*([\d.,]+)", 
                'valor_total_darf': r"DARF NUMERDADO*?\sValor Total do DARF\s*([\d.,]+)", #Adicionar a opção para Valor Total
                'valor_original_credito_darf': r"DARF NUMERDADO*?\sValor Original do Crédito\s([\d.,]+)"
            }
        }

        codigo_receita_pattern = r"Código da Receita/Denominação\s*(\d{4}-\d{2}\s*-\s*.*)(?=\nGrupo de Tributo|$)"
        data_vencimento_tributo_pattern = r"Data de Vencimento do Tributo/Quota\s*([\d/]+)"
        valor_principal_tributo_pattern = r"Principal\s*([\d.,]+)"
        valor_multa_tributo_pattern = r"Multa\s*([\d.,]+)"
        valor_juros_tributo_pattern = r"Juros\s*([\d.,]+)"
        valor_total_tributo_pattern = r"Total\s*([\d.,]+)"
        valor_credito_transmissao_pattern = r"([\d.,]+)\sCrédito Original na Data da Entrega"
        cnpj_detentor_debito_pattern = r"CNPJ do Detentor do Débito\s*([\d./-]+)"
        debito_sucedida_pattern = r"Débito de Sucedida\s*(?:\n+)?\s*(\w+)"
        debito_controlado_processo_pattern = r"Débito Controlado em Processo\s*([\w\s]+?)(?=\n|\.|$)"
        periodo_apuracao_pattern = r"Período de Apuração[:\s]*((?:[\d]{1,2}/)?\d{4}|(?:1º|2º|3º)?\s*(?:Decêndio\s+de\s+)?(?:Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)\s+de\s+\d{4})"
        periodicidade_pattern = r"Periodicidade\s+(Anual|Mensal|Decendial|Diário|Trimestral)"
        grupo_tributo_pattern = r"Grupo de Tributo\s*([\w\s/\-]+?)(?=\n|\.|$)"
        numero_recibo_dctfweb_pattern = r"Indicativo de organismo estrangeiro DCTFWeb\s*(\d{15,16})"
        data_transmissao_dctfweb_pattern = r"Data de Transmissão DCTFWeb\s*(\d{2}/\d{2}/\d{4})"
        categoria_dcftweb_pattern = r"Categoria DCTFWeb Geral\s"
        periodicidade_dctfweb_pattern = r"Periodicidade DCTFWeb\s+(Anual|Mensal|Decendial|Diário|Trimestral)"
        periodo_apuracao_dctfweb_pattern = r"Período\s*Apuração\s*DCTFWeb\s*Periodicidade\s*DCTFWeb\s*(?:Mensal)?\s*(\d{4}|\d{2}/\d{4})"

        for page_num, patterns in page_patterns.items():
            if page_num < pdf_document.page_count:
                page_text = pdf_document[page_num].get_text()
                if info.get('tipo_documento') == 'Pedido de Ressarcimento' and page_num == 2:
                    ano_match = re.search(r"Ano\s*(\d{4})", page_text)
                    trimestre_match = re.search(r"(\d{1,2}[º])\s*Trimestre", page_text)
                    if ano_match and trimestre_match:
                        ano = ano_match.group(1)
                        trimestre = trimestre_match.group(1)
                        info['data_competencia'] = f'{trimestre}/{ano}'
                    else:
                        info['data_competencia'] = "---"

                for key, pattern in patterns.items():
                    matches = re.findall(pattern, page_text)
                    if matches:
                        if key == 'nome_responsavel_preenchimento' and len(matches) > 1:
                            info['nome_responsavel_preenchimento'] = matches[1][0].strip()
                            info['cod_cpf_preenchimento'] = matches[1][1].strip()
                        elif key not in ['nome_responsavel_preenchimento', 'cod_cpf_preenchimento']:
                            info[key] = matches[0].strip()

                #match_compensado = re.search(valor_compensado_pattern, page_text)
                #if match_compensado:
                    #info['valor_total_credito_original_usado_dcomp'] = match_compensado.group(1)
                    #info['valor_total_credito_original_usado_dcomp'] = info['valor_total_credito_original_usado_dcomp'].replace('.', '').replace(',', '.')

                # valor_credito_data_transmissao
                match_credito_transmissao = re.search(valor_credito_transmissao_pattern, page_text)
                if match_credito_transmissao:
                    info['valor_credito_original_data_entrega'] = match_credito_transmissao.group(1)

                if info.get('tipo_documento'):
                    if info['tipo_documento'] in ['Pedido de Restituição', 'Declaração de Compensação', 'Pedido de Ressarcimento']:
                        tipo_credito_pattern = r"Tipo de Crédito\s*([\w\s\-/\.]+)(?=\s*PER/DCOMP Retificador)"
                        cod_per_origem_pattern = r"N[º°] do PER/DCOMP Inicial\s*([\d./-]+)"
                    elif info['tipo_documento'] == "Pedido de Cancelamento":
                        tipo_credito_pattern = r"Tipo de Crédito\s*([\w\s]+)(?=\s*Número do PER)"
                        cod_per_origem_pattern = r"Número do PER/DCOMP a Cancelar\s*([\d./-]+)"

                    tipo_credito_match = re.search(tipo_credito_pattern, page_text)
                    if tipo_credito_match:
                        info['tipo_credito'] = tipo_credito_match.group(1).strip()

                    cod_per_origem_match = re.search(cod_per_origem_pattern, page_text)
                    if cod_per_origem_match:
                        if info['tipo_documento'] == "Pedido de Cancelamento":
                            info['cod_perdcomp_cancelado'] = cod_per_origem_match.group(1).strip()
                        else:
                            info['cod_perdcomp_inicial'] = cod_per_origem_match.group(1).strip()

        patterns_pags_extras = {
            'cnpj_detentor_debito': cnpj_detentor_debito_pattern,
            'codigos_receita': codigo_receita_pattern,
            'grupo_tributo': grupo_tributo_pattern, 
            'debito_sucedida': debito_sucedida_pattern,
            'debito_controlado_processo': debito_controlado_processo_pattern,
            'periodo_apuracao': periodo_apuracao_pattern,
            'periodicidade': periodicidade_pattern,
            'data_vencimento_tributo': data_vencimento_tributo_pattern,
            'numero_recibo_dctfweb': numero_recibo_dctfweb_pattern,
            'data_transmissao_dctfweb': data_transmissao_dctfweb_pattern,
            'categoria_dcftweb': categoria_dcftweb_pattern,
            'periodicidade_dctfweb': periodicidade_dctfweb_pattern, 
            'periodo_apuracao_dctfweb': periodo_apuracao_dctfweb_pattern,   
            'valor_principal_tributo': valor_principal_tributo_pattern,
            'valor_multa_tributo': valor_multa_tributo_pattern,
            'valor_juros_tributo': valor_juros_tributo_pattern,
            'valor_total_tributo': valor_total_tributo_pattern
        }

        for page_num_extra in range(3, pdf_document.page_count):
            page_text_extra = pdf_document[page_num_extra].get_text()
            for key, pattern in patterns_pags_extras.items():
                matches_extra = re.findall(pattern, page_text_extra)
                if matches_extra:
                    for match_item in matches_extra:
                        info[key].append(match_item)

        for key, value in info.items():
            if isinstance(value, list):
                info[key] = ";".join(value)
        return info
