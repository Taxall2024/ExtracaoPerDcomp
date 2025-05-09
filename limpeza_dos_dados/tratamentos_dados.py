

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

        for _, row in df_origem.iterrows():
            # Extrair listas ou valores únicos
            max_len = 1
            valores_colunas = {}

            for col in cols_origem_credito:
                valor = row.get(col, '')
                if isinstance(valor, list):
                    valores_colunas[col] = valor
                    max_len = max(max_len, len(valor))
                else:
                    valores_colunas[col] = [valor]  # transforma em lista para manter consistência

            for i in range(max_len):
                nova_linha = {'cod_perdcomp': row.get('cod_perdcomp', '')}
                for col in cols_origem_credito:
                    valores = valores_colunas.get(col, [])
                    nova_linha[col] = valores[i] if i < len(valores) else ''
                linhas_expandidas.append(nova_linha)

        df_explodido = pd.DataFrame(linhas_expandidas)

        # Filtrar linhas com código de receita válido
        df_explodido = df_explodido[
            df_explodido["codigo_receita_origem_credito"].notna() &
            (df_explodido["codigo_receita_origem_credito"].astype(str).str.strip() != "")
        ]

        # Converter colunas numéricas
        colunas_numericas = [col for col in cols_origem_credito if 'valor_' in col]
        for col in colunas_numericas:
           df_explodido[col] = (
            df_explodido[col]
            .fillna('0,00')  # Preenche valores None com '0'
            .replace('', '0,00')  # Garante que strings vazias também sejam '0'
            #.astype(str)
            #.str.replace('.', '', regex=False)
            #.str.replace(',', '.', regex=False).astype(str).str.replace('.', ',', regex=False)
        )
        return df_explodido
    
    @staticmethod
    def explodir_darf(df_darf):
        cols = [col for col in df_darf.columns if col.startswith('codigo_receita_darf') or 
                'valor_' in col or 'data_' in col or 'periodo_apuracao' in col or 
                'cnpj_darf' in col or 'numero_documento_arrecadacao' in col]
        
        linhas_expandidas = []

        for _, row in df_darf.iterrows():
            cod = row.get('cod_perdcomp', None)
            if not cod:
                print(f"[AVISO] Linha ignorada na função explodir_darf (sem cod_perdcomp): {row.to_dict()}")
                continue

            valores_colunas = {col: row[col] if isinstance(row[col], list) else [row[col]] for col in cols}
            max_len = max(len(valores) for valores in valores_colunas.values())

            for i in range(max_len):
                nova = {'cod_perdcomp': cod}
                for col in cols:
                    valor = valores_colunas[col]
                    nova[col] = valor[i] if i < len(valor) else ''
                linhas_expandidas.append(nova)

        return pd.DataFrame(linhas_expandidas)



    @staticmethod
    def explodir_gps(df_gps):
        cols = [col for col in df_gps.columns if col.startswith('codigo_pagamento_gps') or 'valor_' in col or 'data_' in col or 'periodo_apuracao' in col or 'identificador_detentor' in col or 'data_competencia_gps' in col]
        linhas_expandidas = []

        for _, row in df_gps.iterrows():
            valores_colunas = {col: row[col] if isinstance(row[col], list) else [row[col]] for col in cols}
            max_len = max(len(valores) for valores in valores_colunas.values())

            for i in range(max_len):
                nova = {'cod_perdcomp': row['cod_perdcomp']}
                for col in cols:
                    valor = valores_colunas[col]
                    nova[col] = valor[i] if i < len(valor) else ''
                linhas_expandidas.append(nova)

        return pd.DataFrame(linhas_expandidas)


        
    @staticmethod
    def criar_tabelona(df_tabela1, df_tabela2_explodida, df_tabela3, df_tabela4):
        """
        Converte múltiplas linhas das Tabelas 2, 3 e 4 em colunas numeradas e
        mescla os dados com a Tabela 1 utilizando cod_perdcomp como chave.
        """

        # Lista dos códigos de PER/DCOMP
        codigos_perdcomp = df_tabela1['cod_perdcomp'].dropna().unique()

        # Preenche cod_perdcomp nos DataFrames vazios
        for df in [df_tabela2_explodida, df_tabela3, df_tabela4]:
            if 'cod_perdcomp' not in df.columns:
                df['cod_perdcomp'] = codigos_perdcomp[0] if len(codigos_perdcomp) == 1 else ''
            elif df.empty:
                df['cod_perdcomp'] = codigos_perdcomp[0] if len(codigos_perdcomp) == 1 else ''

        # Pivotar Tabela 2
        tabela2_renomeada = df_tabela2_explodida.copy()
        tabela2_renomeada["row_number"] = tabela2_renomeada.groupby("cod_perdcomp").cumcount() + 1

        df_tabela2_pivot = tabela2_renomeada.pivot(index="cod_perdcomp", columns="row_number")
        df_tabela2_pivot.columns = [f"{col}_{num}" for col, num in df_tabela2_pivot.columns]

        colunas_tabela2 = sorted(df_tabela2_pivot.columns, key=lambda x: int(x.split('_')[-1]))

        # Merge principal
        df_tabelona = df_tabela1.copy()

        if not df_tabela2_pivot.empty:
            df_tabelona = df_tabelona.merge(df_tabela2_pivot[colunas_tabela2], on="cod_perdcomp", how="left")

        # Pivotar Tabela 3 (Origem do Crédito)
        if not df_tabela3.empty:
            df_tabela3 = df_tabela3.copy()
            df_tabela3["row_number"] = df_tabela3.groupby("cod_perdcomp").cumcount() + 1
            df_tabela3_pivot = df_tabela3.pivot(index="cod_perdcomp", columns="row_number")
            df_tabela3_pivot.columns = [f"{col}_{num}" for col, num in df_tabela3_pivot.columns]
            df_tabela3_pivot = df_tabela3_pivot.reset_index()
            df_tabelona = df_tabelona.merge(df_tabela3_pivot, on="cod_perdcomp", how="left")

        # Pivotar Tabela 4 (DARFs)
        if not df_tabela4.empty:
            df_tabela4 = df_tabela4.copy()
            df_tabela4["row_number"] = df_tabela4.groupby("cod_perdcomp").cumcount() + 1
            df_tabela4_pivot = df_tabela4.pivot(index="cod_perdcomp", columns="row_number")
            df_tabela4_pivot.columns = [f"{col}_{num}" for col, num in df_tabela4_pivot.columns]
            df_tabela4_pivot = df_tabela4_pivot.reset_index()
            df_tabelona = df_tabelona.merge(df_tabela4_pivot, on="cod_perdcomp", how="left")

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
