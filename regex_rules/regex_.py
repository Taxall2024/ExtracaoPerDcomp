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
            'valor_disponivel_para_restituicao_apurado_documento_inicial': None,
            'valor_original_credito_utilizado_compensacoes_gfip': None,
            'valor_original_credito_disponivel': None,
            'imposto_devido': None,
            'valor_credito_passivel_restituicao': None,
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

            'periodo_apuracao_origem_credito': [],
            'cnpj_pagamento_origem_credito': [],
            'codigo_receita_origem_credito': [],
            'grupo_tributo_origem_credito': [], 
            'data_arrecadacao_origem_credito': [],
            'valor_principal_origem_credito': [],
            'valor_multa_origem_credito': [],
            'valor_juros_origem_credito': [],
            'valor_total_origem_credito': [],
            'valor_original_credito_origem_credito': [],

            'periodo_apuracao_darf': [],
            'cnpj_darf': [],
            'codigo_receita_darf': [],
            'numero_documento_arrecadacao': [],
            'data_vencimento_darf': [],
            'data_arrecadacao_darf': [],
            'valor_principal_darf': [],
            'valor_multa_darf': [],
            'valor_juros_darf': [],
            'valor_total_darf': [],
            'valor_original_credito_darf': [],

            'codigo_pagamento_gps': [],
            'data_competencia_gps': [],
            'periodo_apuracao_gps': [],
            'identificador_detentor_credito_gps': [],
            'data_arrecadacao_gps': [],
            'valor_inss_gps': [],
            'valor_outras_entidades_gps': [],
            'valor_atm_multa_juros_gps': [],
            'valor_total_gps': [],
            
        }

        origem_credito_pattern = {
            'periodo_apuracao_origem_credito': r'(?i)Período\s+de\s+Apuração[\s:]*(\d{2}/\d{2}/\d{4})',
            'cnpj_pagamento_origem_credito': r'(?i)CNPJ\s+do\s+Pagamento[\s:]*(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})',
            'codigo_receita_origem_credito': r'(?i)Código\s+da\s+Receita[\s:-]*(\d{4}(?:-\d{2})?)',  # Aceita códigos com ou sem "-XX"
            'grupo_tributo_origem_credito': r'(?i)Grupo\s+de\s+Tributo[\s:]+([A-Za-zÀ-ú\s\-–]+?)(?=\s*(?:Código|Valor|Data|$))',
            'data_arrecadacao_origem_credito': r'(?i)Data\s+de\s+Arrecadação[\s:]*(\d{2}/\d{2}/\d{4})',
            'valor_principal_origem_credito': r'(?i)Valor\s+do\s+Principal[\s:]*([\d.,]+)',
            'valor_multa_origem_credito': r'(?i)Valor\s+da\s+Multa[\s:]*([\d.,]+)',
            'valor_juros_origem_credito': r'(?i)Valor\s+dos\s+Juros[\s:]*([\d.,]+)',
            'valor_total_origem_credito': r'(?i)Valor\s+Total[\s:]*([\d.,]+)',
            'valor_original_credito_origem_credito': r'(?i)Valor\s+Original\s+do\s+Crédito[\s:]*([\d.,]+)'
}
        def extract_origem_credito(text):
            """
            Extrai múltiplos blocos de Origem do Crédito com base em '1.Período de Apuração', '2.Período...' etc.
            """
            resultados = {key: [] for key in origem_credito_pattern.keys()}

            # Normalizar texto
            text = re.sub(r'[ \t]+', ' ', text)
            text = re.sub(r'\n+', '\n', text)

            # Dividir por blocos que começam com número + "Período de Apuração"
            blocos = re.split(r'(?=\d+\.\s*Período de Apuração)', text, flags=re.IGNORECASE)

            for bloco in blocos:
                if not re.search(r'Período de Apuração', bloco, flags=re.IGNORECASE):
                    continue

                temp = {}
                for campo, pattern in origem_credito_pattern.items():
                    match = re.search(pattern, bloco, flags=re.IGNORECASE | re.MULTILINE)
                    if match:
                        value = match.group(1).strip()
                        temp[campo] = value
                    else:
                        temp[campo] = None

                if temp['periodo_apuracao_origem_credito']:  # Campo obrigatório
                    for key in origem_credito_pattern:
                        resultados[key].append(temp[key])

            return resultados


        page_patterns = {
            0: {
                'cod_cnpj': r"CNPJ \s*([\d./-]+)",
                'cod_perdcomp': r"CNPJ \s*[\d./-]+\s*([\d.]+-[\d.]+)",
                'nome_cliente': r"Nome Empresarial\s*(.+)",

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
                'valor_saldo_credito_original': r"Saldo do Crédito Original[\s:]*([\d.,]+)", 
                'selic_acumulada': r"Selic Acumulada\s*([\d.,]+)",
                'data_competencia': r"(?:1[º°]|2[º°]|3[º°]|4[º°])\s*Trimestre/\d{4}",
                'competencia': r"Competência\s+((?:Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)\s*(?:\/|de)\s*\d{4})\s*",
                'data_arrecadacao': r'Data de Arrecadação\s*([\d/]+)', 
                'valor_credito_original_data_entrega': r'(?:Crédito Original na Data (?:de|da) Entrega|Crédito Original na Data da Entrega)[\s:]*([\d]{1,3}(?:\.?\d{3})*(?:,\d{2}))',
                'total_parcelas_composicao_credito': r'(?:(?<=Total das Parcelas de Composição do Crédito\s)[\d.,]+|[\d.,]+(?=\s*Total das Parcelas de Composição do Crédito))',
                'valor_original_credito_inicial': r"Valor Original do Crédito Inicial\s*([\d.,]+)",
                'imposto_devido': r"Imposto Devido\s*([\d.,]+)",
                'valor_pedido_restituicao': r"Valor do Pedido de Restituição\s*([\d.,]+)", 
                'valor_total_debitos_deste_documento':r"Total dos Débitos deste Documento\s*([\d.,]+)", 
                'valor_total_credito_original_utilizado_documento': r"Total do Crédito Original [Uu]tilizado neste Documento\s*([\d.,]+)\s",
                'valor_total_debitos_desta_dcomp': r"Total dos débitos desta DCOMP[\s\S]*?(\d{1,3}(?:\.\d{3})*,\d{2})",
                'valor_total_credito_original_utilizado_dcomp': r"Total do Crédito Original [Uu]tilizado nesta DCOMP\s*([\d.,]+)",
                'csll_devida': r"\sCSLL Devida\s([\d.,]+)\s*",
                'valor_disponivel_para_restituicao_apurado_documento_inicial': r'(?i)Valor\s+Disponível\s+para\s+Restituição\s+Apurado\s+no.*?(\d{1,3}(?:\.\d{3})*,\d{2}).*?Documento\s+Inicial',
                'valor_original_credito_utilizado_compensacoes_gfip': r'(?i)Valor\s+Original\s+do\s+Crédito\s+Utilizado\s+em.*?(\d{1,3}(?:\.\d{3})*,\d{2}).*?Compensações\s+em\s+GFIP',
                'valor_credito_passivel_restituicao': r"Crédito Passível de Restituição\s*([\d.,]+)",


                # # Origem do Crédito
                # 'periodo_apuracao_origem_credito': r"(?i)(?:Período de Apuração|Período de Apuração)\s*(\d{2}/\d{2}/\d{4})",
                # 'cnpj_pagamento_origem_credito': r"(?<!\d)(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})\s+CNPJ do Pagamento",
                # 'codigo_receita_origem_credito': r"Código da Receita\s+(\d{4}-\d{2})",
                # 'grupo_tributo_origem_credito': r"Grupo de Tributo\s+([A-Z]+)(?=\s*Código da Receita)",
                # 'data_arrecadacao_origem_credito': r"Data de Arrecadação\s+(\d{2}/\d{2}/\d{4})",  
                # 'valor_principal_origem_credito': r"Valor do Principal\s+([\d.,]+)",
                # 'valor_multa_origem_credito': r"Valor da Multa\s+([\d.,]+)",   
                # 'valor_juros_origem_credito': r"([\d.,]+)\s+Valor dos Juros", 
                # 'valor_total_origem_credito': r"Valor Total\s+([\d.,]+)\b",  
                # 'valor_original_credito_origem_credito': r'Valor Original do Crédito\s+([\d.,]+)\b', 


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
                'valor_original_credito_darf': r"DARF NUMERDADO*?\sValor Original do Crédito\s([\d.,]+)",

                #GPS
                'codigo_pagamento_gps':   r'(?i)Código\s+do\s+Pagamento\s+(.*?)(?=\s*Competência)',
                'data_competencia_gps': r'(?i)Competência\s+([A-Za-zç]+\s+de\s+\d{4})',
                'identificador_detentor_credito_gps': r'(?i)Identificador\s+do\s+Detentor\s+do\s+Crédito\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})',
                'periodo_apuracao_gps': r"Período de Apuração\s*([\d/]+)", 
                'valor_inss_gps': r'(?i)Valor\s+do\s+INSS\s+([\d\.,]+)',
                'valor_outras_entidades_gps': r'(?i)Valor\s+de\s+Outras\s+Entidades\s+([\d\.,]+)',
                'valor_atm_multa_juros_gps': r'(?i)Valor\s+de\s+ATM,\s+Multa\s+e\s+Juros\s+([\d\.,]+)',
                'valor_total_gps': r'(?i)Valor\s+Total\s+da\s+GPS\s+([\d\.,]+)',
                'data_arrecadacao_gps': r'(?i)Data\s+da\s+Arrecadação\s+(\d{2}/\d{2}/\d{4})',
                
            },
        }

        cnpj_detentor_debito_pattern = r'CNPJ\s+do\s+Detentor\s+do\s+Débito[\s:]*([\d./-]+)'
        debito_sucedida_pattern = r"Débito de Sucedida\s*(?:\n+)?\s*(\w+)"
        grupo_tributo_pattern = r'Grupo\s+de\s+Tributo\s+([^\n]+?)(?=\s*\n|Código|$|\.)'
        codigo_receita_pattern = r"Código da Receita/Denominação[\s:-]*(.*?)(?=\s*Débito Controlado em Processo)"
        debito_controlado_processo_pattern = r"Débito Controlado em Processo[\s:]*(\b\w+\b)(?=\s*(?:\n|\.|Período|Data|$))"
        periodo_apuracao_pattern = r"Período de Apuração[:\s]*((?:[\d]{1,2}/)?\d{4}|(?:1º|2º|3º)?\s*(?:Decêndio\s+de\s+)?(?:Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)\s+de\s+\d{4})"
        periodicidade_pattern = r"Periodicidade\s+(Anual|Mensal|Decendial|Diário|Trimestral)"
        data_vencimento_tributo_pattern = r"(?i)Data\s*de\s*Vencimento\s*do\s*Tributo/Quota[\s:]*(\d{2}/\d{2}/\d{4})"
        numero_recibo_dctfweb_pattern = r"Número\s+do\s+Recibo\s+de\s+Transmissão\s+DCTFWeb\s+(\d{15,16})"
        data_transmissao_dctfweb_pattern = r"Data\s+de\s+Transmissão\s+DCTFWeb\s+(\d{2}/\d{2}/\d{4})"
        categoria_dcftweb_pattern = r"Categoria\s+DCTFWeb\s+([A-Za-zÀ-ú]+)"
        periodicidade_dctfweb_pattern = r"Periodicidade\s+DCTFWeb\s+(Anual|Mensal|Decendial|Diário|Trimestral)\b"
        periodo_apuracao_dctfweb_pattern = r"Período\s+de\s+Apuração\s+DCTFWeb\s+(\d{4}|\d{2}/\d{4})"
        valor_principal_tributo_pattern = r"(?i)Principal[\s:\-]*([\d\.]{1,3}(?:\.\d{3})*,\d{2})"
        valor_multa_tributo_pattern = r"(?i)Multa[\s:\-]*([\d\.]{1,3}(?:\.\d{3})*,\d{2})"
        valor_juros_tributo_pattern = r"(?i)Juros[\s:\-]*([\d\.]{1,3}(?:\.\d{3})*,\d{2})"
        valor_total_tributo_pattern = r"(?i)(?:Total\s+do\s+Tributo|Total)[\s:\-]*([\d\.]{1,3}(?:\.\d{3})*,\d{2})"

        for page_num, patterns in page_patterns.items():
            if page_num < len(pdf_document.pages):
                page = pdf_document.pages[page_num]  # Acessando a página corretamente com pdfplumber
                page_text = page.extract_text()
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

        flags = re.IGNORECASE | re.MULTILINE

        def clean_text(text):
            """Normaliza o texto para facilitar a extração"""
            text = re.sub(r'\s+', ' ', text)  
            text = re.sub(r'(?<=\d)\s+(?=\d)', '', text)  
            return text

        for page_num_extra in range(3, len(pdf_document.pages)):
            page_text_extra = pdf_document.pages[page_num_extra].extract_text()  # Correção aqui
            page_text_extra = clean_text(page_text_extra)
            # Extrai blocos de débito separadamente
            debito_blocks = re.split(r'\n?(?=\d{3}\.\s+Débito\s+)', page_text_extra)
            debito_blocks = [b for b in debito_blocks if "Débito" in b]

            
            for block in debito_blocks:
                for key, pattern in patterns_pags_extras.items():
                    matches = re.findall(pattern, block, flags)
                    for match in matches:
                        value = match.strip() if isinstance(match, str) else match[0].strip()
                        if key == 'codigos_receita':
                            value = re.sub(r'\s+', ' ', value).replace('- ', '-')
                        info[key].append(value)

        
        
        origem_credito_keys = set(origem_credito_pattern.keys())

        texto_completo = "\n".join(page.extract_text() for page in pdf_document.pages)
        origem_credito_data = extract_origem_credito(texto_completo)

        for key in origem_credito_pattern.keys():
            info[key].extend(origem_credito_data.get(key, []))


        for key, value in info.items():
            if isinstance(value, list):
                if key not in origem_credito_keys:
                    info[key] = ";".join(value) if value else None
                else:
                    # Mantém como lista, mesmo se vazia
                    info[key] = value if value else []

        return info  # Garantir que isso está no final
