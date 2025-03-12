import fitz
from regex_rules.regex_ import RegexRules
import pandas as pd


class Processamento():

    @staticmethod
    def process_pdfs_in_memory(uploaded_files):
        all_data = []
        for uploaded_file in uploaded_files:
            pdf_bytes = uploaded_file.read()
            with fitz.open(stream=pdf_bytes, filetype='pdf') as pdf_document:
                info = RegexRules.extract_info_from_pages(pdf_document)
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
                numeros_convertidos = [str(RegexRules.extrair_valor_numerico(parte)) for parte in partes]
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

    @staticmethod
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
            print(f" ======= > LOG ERROR < ======== :  Erro ao ler o arquivo TXT: {e}")
            return None
