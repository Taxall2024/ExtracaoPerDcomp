import pandas as pd
import io

class ExportarDados():

    @staticmethod
    def gerar_excel_em_memoria(df1, df2, df_tabelona, df3, df4, df5):

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_tabelona.to_excel(writer, sheet_name="Tabela Geral", index=False)
            df1.to_excel(writer, sheet_name="Tabela PERDCOMP", index=False)
            df2.to_excel(writer, sheet_name="Tabela Tributos", index=False)
            df3.to_excel(writer, sheet_name="Tabela Origem Créditos", index=False)
            df4.to_excel(writer, sheet_name="Tabela DARF", index=False) 
            df5.to_excel(writer, sheet_name="Tabela GPS", index=False)
        output.seek(0)
        
        return output
