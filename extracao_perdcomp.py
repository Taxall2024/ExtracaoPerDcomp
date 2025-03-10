import re
import fitz  # PyMuPDF
import pandas as pd
import os
import calendar
import io
import streamlit as st

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
        'competencia': None,    
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

def process_pdfs_in_memory(uploaded_files):
    import fitz
    all_data = []
    for uploaded_file in uploaded_files:
        pdf_bytes = uploaded_file.read()
        with fitz.open(stream=pdf_bytes, filetype='pdf') as pdf_document:
            info = extract_info_from_pages(pdf_document)
            info['Arquivo'] = uploaded_file.name
            all_data.append(info)

    df = pd.DataFrame(all_data)

    cols_tributos_numericos = [
        'valor_principal_tributo',
        'valor_multa_tributo',
        'valor_juros_tributo',
        'valor_total_tributo',
    ]

    for col in cols_tributos_numericos:
        def converter_lista_de_numeros(item):
            if pd.isna(item) or not item:
                return item
            partes = [p.strip() for p in item.split(';')]
            numeros_convertidos = [str(extrair_valor_numerico(parte)) for parte in partes]
            return ";".join(numeros_convertidos)
        if col in df.columns:
            df[col] = df[col].apply(converter_lista_de_numeros)

    colunas_texto = [
        'perdcomp_retificador', 'cod_perdcomp_retificacao', 'tipo_credito',
        'origem_credito_judicial', 'nome_responsavel_preenchimento', 'cod_cpf_preenchimento',
        'cod_perdcomp_inicial', 'cod_perdcomp_cancelado', 'codigos_receita', 'data_vencimento_tributo', 'grupo_tributo', 'debito_sucedida',
        'cnpj_detentor_debito', 'periodicidade', 'debito_controlado_processo', 'periodo_apuracao', 'data_transmissao_dctfweb', 'numero_recibo_dctfweb',
        'categoria_dcftweb', 'periodicidade_dctfweb', 'periodo_apuracao_dctfweb'
    ]
    for coluna in colunas_texto:
        if coluna in df.columns:
            df[coluna] = df[coluna].fillna('---')

    colunas_data = ['data_inicial_periodo', 'data_final_periodo', 'data_transmissao']
    for coluna in colunas_data:
        if coluna in df.columns:
            df[coluna] = pd.to_datetime(df[coluna], format='%d/%m/%Y', errors='coerce')

    return df


def explodir_tabela2(df_tabela2):
    cols_explodir = [
        'cnpj_detentor_debito',
        'debito_sucedida',
        'grupo_tributo',
        'codigos_receita',
        'debito_controlado_processo',
        'periodo_apuracao',
        'periodicidade',
        'data_vencimento_tributo',
        'numero_recibo_dctfweb',
        'data_transmissao_dctfweb',
        'categoria_dcftweb',
        'periodicidade_dctfweb',
        'periodo_apuracao_dctfweb',
        'valor_principal_tributo',
        'valor_multa_tributo',
        'valor_juros_tributo',
        'valor_total_tributo',
    ]
    
    linhas_expandidas = []
    for idx, row in df_tabela2.iterrows():
        splitted = {}
        max_len = 1
        for col in cols_explodir:
            if (col not in row) or pd.isna(row[col]) or row[col] == '---':
                splitted[col] = []
            else:
                partes = [p.strip() for p in row[col].split(';')]
                splitted[col] = partes
                max_len = max(max_len, len(partes))

        for i in range(max_len):
            nova_linha = {}
            nova_linha['cod_perdcomp'] = row['cod_perdcomp']
            for col in cols_explodir:
                valores = splitted[col]
                if i < len(valores):
                    nova_linha[col] = valores[i]
                else:
                    nova_linha[col] = ''
            linhas_expandidas.append(nova_linha)

    df_explodido = pd.DataFrame(linhas_expandidas)
    df_explodido = df_explodido[
        df_explodido["codigos_receita"].notna() &
        (df_explodido["codigos_receita"].str.strip() != "")
    ]
    return df_explodido

def gerar_excel_em_memoria(df1, df2, df_tabelona, df3, df4):
    import openpyxl
    from openpyxl import Workbook
    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_tabelona.to_excel(writer, sheet_name="Tabela Geral", index=False)
        df1.to_excel(writer, sheet_name="Tabela PERDCOMP", index=False)
        df2.to_excel(writer, sheet_name="Tabela Tributos", index=False)
        df3.to_excel(writer, sheet_name="Tabela Origem Créditos", index=False)
        df4.to_excel(writer, sheet_name="Tabela DARF", index=False) 
    output.seek(0)
    return output

def criar_tabelona(df_tabela1, df_tabela2_explodida, df_tabela3, df_tabela4):
    """
    Converte múltiplas linhas da Tabela 2 em colunas numeradas e
    mescla os dados com a Tabela 1 utilizando cod_perdcomp como chave.
    """
    tabela2_renomeada = df_tabela2_explodida.copy()
    tabela2_renomeada["row_number"] = tabela2_renomeada.groupby("cod_perdcomp").cumcount() + 1

    df_tabela2_pivot = tabela2_renomeada.pivot(index="cod_perdcomp", columns="row_number")
    df_tabela2_pivot.columns = [f"{col}_{num}" for col, num in df_tabela2_pivot.columns]

    # Ordenar as colunas anexadas por numeração crescente (_1, _2, _3, etc)
    colunas_tabela2 = sorted(df_tabela2_pivot.columns, key=lambda x: int(x.split('_')[-1]))

    #df_tabelona = df_tabela1.merge(df_tabela2_pivot, on="cod_perdcomp", how="left")
    df_tabelona = df_tabela1.merge(df_tabela2_pivot[colunas_tabela2], on="cod_perdcomp", how="left")
    df_tabelona = df_tabelona.merge(df_tabela3, on="cod_perdcomp", how="left") 
    df_tabelona = df_tabelona.merge(df_tabela4, on="cod_perdcomp", how="left") 

    return df_tabelona

def limpar_tabelas_3_e_4(df_tabela3, df_tabela4):
    """
    Remove linhas das tabelas 3 e 4 onde apenas 'cod_perdcomp' existe e os demais dados são vazios.
    """

    # Remover da Tabela 3 quando só existe 'cod_perdcomp'
    colunas_dados_tabela3 = [col for col in df_tabela3.columns if col != 'cod_perdcomp']
    df_tabela3 = df_tabela3.dropna(subset=colunas_dados_tabela3, how='all')

    # Remover da Tabela 4 quando só existe 'cod_perdcomp'
    colunas_dados_tabela4 = [col for col in df_tabela4.columns if col != 'cod_perdcomp']
    df_tabela4 = df_tabela4.dropna(subset=colunas_dados_tabela4, how='all')

    return df_tabela3, df_tabela4

# Função para ler o arquivo TXT
def ler_arquivo_txt(uploaded_file, nome_coluna1='cod_perdcomp', nome_coluna2='situacao_perdcomp'):
    """
    Lê um arquivo TXT e retorna um DataFrame com duas colunas.
    Supõe que o arquivo tenha duas colunas separadas por um delimitador (por exemplo, vírgula ou tabulação).
    """
    try:
        # Ler o conteúdo do arquivo
        conteudo = uploaded_file.read().decode('utf-8')
        
        # Dividir o conteúdo em linhas
        linhas = conteudo.strip().split('\n')
        
        # Processar cada linha para extrair as colunas
        dados = []
        #cabecalho = linhas[0].strip().split(';')  # Extrair o cabeçalho
        for linha in linhas[1:]:  # Ignorar o cabeçalho
            colunas = linha.strip().split(';')  # Usar ';' como delimitador
            if len(colunas) >= 5:  # Verificar se há pelo menos 5 colunas
                dados.append([colunas[0], colunas[4]])    
        # Criar o DataFrame
        df = pd.DataFrame(dados, columns=['Número de PER/DCOMP', 'Situação'])

        df = df.rename(columns={
            'Número de PER/DCOMP': nome_coluna1,
            'Situação': nome_coluna2
        })
        return df
    
    except Exception as e:
        st.error(f"Erro ao ler o arquivo TXT: {e}")
        return None


# -------------------------------------------------------
# APLICAÇÃO STREAMLIT
# -------------------------------------------------------
def main():
    st.title("Extração de Dados de PER/DCOMP (PDF)")
    st.write("""
    Faça upload dos PDFs de PER/DCOMP que deseja analisar. 
    O sistema fará a raspagem de dados e exibirá nas seguintes tabelas:
    - Tabela Geral: visão unificada de todas as informações
    - Tabela 1: dados gerais das PER/DCOMP
    - Tabela 2: códigos de receita e respectivos valores de tributos
    - Tabela 3: dados da origem dos créditos
    - Tabela 4: dados das DARF pagos
             
    [ATENÇÃO] Tome cuidado ao utilizar os dados, pois a extração pode conter erros. 
    Algumas das colunas podem vir vazias já que o pdf não contém a informação.
    Se houver dúvidas, consulte o arquivo original.
    """)

    uploaded_files_1 = st.file_uploader(
        "Envie seus arquivos PDF de PER/DCOMP",
        type=["pdf"],
        accept_multiple_files=True
    )

    uploaded_files_2 = st.file_uploader(
        "Envie seus arquivo .TXT ",
        type=["txt"],
        accept_multiple_files=False)

    if uploaded_files_1:
        st.write("[INFO] Processando PDFs... aguarde.")
        df_result = process_pdfs_in_memory(uploaded_files_1)

        # Monta Tabela1 / Tabela2
        tabela1_cols = [
            'cod_cnpj',
            'nome_cliente',
            'cod_perdcomp',
            'data_transmissao',
            'tipo_documento',
            'tipo_credito',
            'perdcomp_retificador',
            'cod_perdcomp_retificacao',
            'origem_credito_judicial',
            'nome_responsavel_preenchimento',
            'cod_cpf_preenchimento',
            'cod_perdcomp_inicial',
            'data_inicial_periodo',
            'data_final_periodo',
            'data_competencia',
            'competencia',
            'selic_acumulada',
            'imposto_devido', 
            'csll_devida',
            'total_parcelas_composicao_credito',
            'valor_original_credito_inicial',
            'valor_saldo_negativo',
            'valor_credito_original_data_entrega',
            'valor_pedido_restituicao',
            'valor_credito_atualizado',
            'valor_total_debitos_deste_documento',
            'valor_total_credito_original_utilizado_documento',
            'valor_total_debitos_desta_dcomp', 
            'valor_total_credito_original_utilizado_dcomp',
            'valor_saldo_credito_original',
            'cod_perdcomp_cancelado',
            'Arquivo', 
        ]
        tabela2_cols = [
            'cod_perdcomp',
            'cnpj_detentor_debito',
            'debito_sucedida',
            'grupo_tributo',
            'debito_controlado_processo',
            'periodo_apuracao',
            'periodicidade',
            'codigos_receita',
            'data_vencimento_tributo',
            'numero_recibo_dctfweb',
            'data_transmissao_dctfweb',
            'categoria_dcftweb',
            'periodicidade_dctfweb',
            'periodo_apuracao_dctfweb',
            'valor_principal_tributo',
            'valor_multa_tributo',
            'valor_juros_tributo',
            'valor_total_tributo'
        ]

        tabela3_cols =[   
            'cod_perdcomp',
            'periodo_apuracao_origem_credito',
            'cnpj_origem_credito',
            'codigo_receita_origem_credito',
            'grupo_tributo_origem_credito',
            'valor_principal_origem_credito',
            'valor_multa_origem_credito', 
            'valor_juros_origem_credito',
            'valor_total_origem_credito'
            ]

        tabela4_cols = [
            'cod_perdcomp',
            'periodo_apuracao_darf',
            'cnpj_darf',
            'codigo_receita_darf',
            'numero_documento_arrecadacao',
            'data_vencimento_darf',
            'data_arrecadacao_darf',
            'valor_principal_darf',
            'valor_multa_darf',
            'valor_juros_darf',
            'valor_total_darf',
            'valor_original_credito_darf'

        ]

        df_tabela1 = df_result[tabela1_cols].copy()
        df_tabela2 = df_result[tabela2_cols].copy()
        df_tabela3 = df_result[tabela3_cols].copy()
        df_tabela4 = df_result[tabela4_cols].copy()

      # Explodir Tabela2 (múltiplas linhas viram colunas numeradas)
        df_tabela2_explodida = explodir_tabela2(df_tabela2)
        df_tabela3, df_tabela4 = limpar_tabelas_3_e_4(df_tabela3, df_tabela4)

        #Substituir '.' por ',' nas colunas de tributos na Tabela2 explodida
        tributo_cols = ['valor_principal_tributo', 'valor_multa_tributo', 'valor_juros_tributo', 'valor_total_tributo']
        for col in tributo_cols:
            if col in df_tabela2_explodida.columns:
                # Garantir que a coluna é string antes de replace, se não for string, converter
                df_tabela2_explodida[col] = df_tabela2_explodida[col].astype(str).str.replace('.', ',', regex=False)

        # Criar Tabelona com as colunas numeradas corretamente
        df_tabelona = criar_tabelona(df_tabela1, df_tabela2_explodida, df_tabela3, df_tabela4)

        colunas_para_somar = [
            'valor_principal_tributo',
            'valor_multa_tributo',
            'valor_juros_tributo',
            'valor_total_tributo'
        ]

        df_totalizadores = df_tabela2_explodida.copy()

        # Converter as colunas para números
        for coluna in colunas_para_somar:
            df_totalizadores[coluna] = (
                df_totalizadores[coluna]
                .str.replace('.', '', regex=False)  # Remove pontos (separadores de milhares)
                .str.replace(',', '.', regex=False)  # Substitui vírgula por ponto (decimal)
                .apply(pd.to_numeric, errors='coerce')
        )
        
        df_totalizadores = (
            df_totalizadores.groupby('cod_perdcomp')[colunas_para_somar]
            .sum().round(2)
            .reset_index()
        )

        for coluna in colunas_para_somar:
            df_totalizadores[coluna] = df_totalizadores[coluna].astype(str).str.replace('.', ',', regex=False)


        df_totalizadores.columns = [
            'cod_perdcomp',
            'total_valor_principal_tributo',
            'total_valor_multa_tributo',
            'total_valor_juros_tributo',
            'total_valor_total_tributo'
        ]
        
        # Mesclar os totais na Tabela 1
        df_tabela1 = df_tabela1.merge(df_totalizadores, on='cod_perdcomp', how='left')


         # Processar o arquivo TXT, se enviado
        if uploaded_files_2:
            st.write("[INFO] Processando arquivo TXT... aguarde.")
            df_txt = ler_arquivo_txt(uploaded_files_2, 'cod_perdcomp', 'situacao_perdcomp')
            
            if not df_txt.empty:
                #st.subheader("Dados do Arquivo TXT")
                #st.dataframe(df_txt)  # Exibir o DataFrame do TXT para verificação

                # Garantir que a coluna 'cod_perdcomp' em df_txt e df_tabela1 tenha o mesmo tipo
                df_txt['cod_perdcomp'] = df_txt['cod_perdcomp'].astype(str)
                df_tabela1['cod_perdcomp'] = df_tabela1['cod_perdcomp'].astype(str)

                # Mesclar os dados do TXT na Tabela 1
                df_tabela1 = df_tabela1.merge(df_txt, on='cod_perdcomp', how='left')

                # Preencher valores ausentes na coluna 'situacao_perdcomp'
                df_tabela1['situacao_perdcomp'] = df_tabela1['situacao_perdcomp'].fillna('---')

         # Exibir Tabelona
        st.subheader("Tabela Geral")
        st.dataframe(df_tabelona)

        st.subheader("Tabela 1 - Dados das PER/DCOMP")
        st.dataframe(df_tabela1)

        st.subheader("Tabela 2 - Detalhamento de Tributos Compensados da PER/DCOMP")
        st.dataframe(df_tabela2_explodida)

        st.subheader("Tabela 3 - Dados Origem do Créditos")
        st.dataframe(df_tabela3)

        st.subheader("Tabela 4 - Dados DARF Pagos")
        st.dataframe(df_tabela4)


        # Cria nome do arquivo Excel de acordo com a primeira palavra do nome_cliente
        nome_arquivo_excel = "extract_pdf_result.xlsx"
        if not df_tabela1.empty:
            nome_cliente = df_tabela1.iloc[0].get("nome_cliente", "")
            if nome_cliente:
                nome_cliente = nome_cliente.strip().split(" ")[0]
                nome_arquivo_excel = f"{nome_cliente}_Export_PERDCOMPs.xlsx"

        # Gerar Excel em memória
        excel_bytes = gerar_excel_em_memoria( df_tabela1, df_tabela2_explodida, df_tabelona, df_tabela3, df_tabela4)

       # Botão para download
        st.download_button(
            label="Baixar arquivo Excel",
            data=excel_bytes,
            file_name=nome_arquivo_excel,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    else:
        st.info("Por favor, faça o upload de um ou mais arquivos PDF.")

if __name__ == "__main__":
    import pandas as pd
    main()