import re
import pandas as pd
#import calendar
import streamlit as st

from exportar_dados.gerar_excel import ExportarDados
from processamento_de_arquivos.processamento import Processamento
from limpeza_dos_dados.tratamentos_dados import LimpezaETratamentoDados


def main():
    texto = ("Extração de Dados de PER/DCOMP (PDF)")
    texto =("""
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
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ALTERAR AQUI <<

    uploaded_files_1 = st.file_uploader(
        "Envie seus arquivos PDF de PER/DCOMP",
        type=["pdf"],
        accept_multiple_files=True
    )
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ALTERAR AQUI <<

    uploaded_files_2 = st.file_uploader(
        "Envie seus arquivo .TXT ",
        type=["txt"],
        accept_multiple_files=False)
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> <

    if uploaded_files_1:
        df_result = Processamento.process_pdfs_in_memory(uploaded_files_1)

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
            'forma_tributacao_lucro',
            'forma_apuracao',
            'exercicio',
            'data_arrecadacao', 
            'selic_acumulada',
            'valor_credito_passivel_restituicao',
            'valor_original_credito_utilizado_compensacoes_gfip',
            'valor_disponivel_para_restituicao_apurado_documento_inicial', 
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
            'cnpj_pagamento_origem_credito',
            'codigo_receita_origem_credito',
            'grupo_tributo_origem_credito',
            'data_arrecadacao_origem_credito', 
            'valor_principal_origem_credito',
            'valor_multa_origem_credito', 
            'valor_juros_origem_credito',
            'valor_total_origem_credito', 
            'valor_original_credito_origem_credito',
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
            'valor_original_credito_darf',
        ]

        tabela5_cols = [
            'cod_perdcomp',
            'codigo_pagamento_gps',
            'data_competencia_gps',
            'periodo_apuracao_gps',
            'identificador_detentor_credito_gps',
            'data_arrecadacao_gps',
            'valor_inss_gps',
            'valor_outras_entidades_gps',
            'valor_atm_multa_juros_gps',
            'valor_total_gps',
        ]

        df_tabela1 = df_result[tabela1_cols].copy()
        df_tabela2 = df_result[tabela2_cols].copy()
        df_tabela3 = df_result[tabela3_cols].copy()
        df_tabela4 = df_result[tabela4_cols].copy()
        df_tabela5 = df_result[tabela5_cols].copy()

      # Explodir Tabela2 (múltiplas linhas viram colunas numeradas)
        df_tabela2_explodida = LimpezaETratamentoDados.explodir_tabela2(df_tabela2)
        df_tabela3 = LimpezaETratamentoDados.explodir_origem_credito(df_tabela3)
        df_tabela4 = LimpezaETratamentoDados.explodir_darf(df_tabela4)
        df_tabela5 = LimpezaETratamentoDados.explodir_gps(df_tabela5)
        df_tabela3, df_tabela4 = LimpezaETratamentoDados.limpar_tabelas_3_e_4(df_tabela3, df_tabela4)


        #Substituir '.' por ',' nas colunas de tributos na Tabela2 explodida
        tributo_cols = ['valor_principal_tributo', 'valor_multa_tributo', 'valor_juros_tributo', 'valor_total_tributo']
        for col in tributo_cols:
            if col in df_tabela2_explodida.columns:
                # Garantir que a coluna é string antes de replace, se não for string, converter
                df_tabela2_explodida[col] = df_tabela2_explodida[col].astype(str).str.replace('.', ',', regex=False)

        # Criar Tabelona com as colunas numeradas corretamente
        df_tabelona = LimpezaETratamentoDados.criar_tabelona(df_tabela1, df_tabela2_explodida, df_tabela3, df_tabela4)

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
                .str.replace('.', '', regex=False) 
                .str.replace(',', '.', regex=False)  
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
            df_txt = Processamento.ler_arquivo_txt(uploaded_files_2, 'cod_perdcomp', 'situacao_perdcomp')
            
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

        st.subheader("Tabela 5 - Dados GPS Pagos")
        st.dataframe(df_tabela5)

        nome_arquivo_excel = "extract_pdf_result.xlsx"
        if not df_tabela1.empty:
            nome_cliente = df_tabela1.iloc[0].get("nome_cliente", "")
            if nome_cliente:
                nome_cliente = nome_cliente.strip().split(" ")[0]
                nome_arquivo_excel = f"{nome_cliente}_Export_PERDCOMPs.xlsx"

        # Gerar Excel em memória
        excel_bytes = ExportarDados.gerar_excel_em_memoria( df_tabela1, df_tabela2_explodida, df_tabelona, df_tabela3, df_tabela4, df_tabela5)
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ALTERAR AQUI <<
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
    main()