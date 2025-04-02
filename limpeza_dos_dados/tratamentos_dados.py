

import pandas as pd

class LimpezaETratamentoDados():

    @staticmethod
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

    @staticmethod
    def explodir_origem_credito(df_origem):
        cols_origem_credito = [
            'periodo_apuracao_origem_credito',
            'cnpj_pagamento_origem_credito',
            'codigo_receita_origem_credito',
            'grupo_tributo_origem_credito',
            'data_arrecadacao_origem_credito',
            'valor_principal_origem_credito',
            'valor_multa_origem_credito',
            'valor_juros_origem_credito',
            'valor_total_origem_credito',
            'valor_original_credito_origem_credito'
        ]
        
        linhas_expandidas = []
        
        for idx, row in df_origem.iterrows():
            splitted = {}
            max_len = 1
            
            for col in cols_origem_credito:
                # Verificar se a coluna existe na linha
                if col not in row:
                    splitted[col] = []
                    continue
                    
                valor = row[col]
                
                # Tratar listas e valores não listados
                if isinstance(valor, list):
                    partes = [str(item).strip() for item in valor]
                else:
                    if pd.isna(valor) or (valor in ['---', '']):
                        partes = []
                    else:
                        partes = [str(valor).strip()]
                
                splitted[col] = partes
                max_len = max(max_len, len(partes))
            
            for i in range(max_len):
                nova_linha = {'cod_perdcomp': row.get('cod_perdcomp', '')}
                
                for col in cols_origem_credito:
                    valores = splitted[col]
                    nova_linha[col] = valores[i] if i < len(valores) else ''
                
                linhas_expandidas.append(nova_linha)
        
        df_explodido = pd.DataFrame(linhas_expandidas)
        
        # Filtrar linhas com código de receita válido
        df_explodido = df_explodido[
            df_explodido["codigo_receita_origem_credito"].str.strip().ne("")
        ]
        
        # Converter colunas numéricas
        colunas_numericas = [col for col in cols_origem_credito if 'valor_' in col]
        for col in colunas_numericas:
            df_explodido[col] = (
                df_explodido[col]
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
                .astype(float, errors='ignore')
            )
        
        return df_explodido
        
    @staticmethod
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

    @staticmethod
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
