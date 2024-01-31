from celery import Celery
from your_module import app, buscar_abuse_ip, adicionar_dados_ao_dataframe, criar_excel_com_dados

@app.task
def process_data(data_frame):
    try:
        # Adicionar dados ao DataFrame
        data_frame_com_dados = adicionar_dados_ao_dataframe(data_frame)

        # Criar Excel com os dados
        excel_buffer = criar_excel_com_dados(data_frame_com_dados)

        return excel_buffer

    except Exception as e:
        raise Exception(f"Erro ao processar os dados: {e}")
