import pandas as pd
import requests
from flask import Flask, render_template, request, send_file, redirect, url_for
import io
import os

app = Flask(__name__)

# Chave de API (substitua por sua chave real)
chave_api = "1a1567e352662065b726580c17ab22197f40cb72601994f3a9eb491ac39c4a0772a47345c62ed923"

def buscar_abuse_ip(ip_address):
    url = 'https://api.abuseipdb.com/api/v2/check'
    querystring = {'ipAddress': ip_address, 'maxAgeInDays': '90'}
    headers = {'Accept': 'application/json', 'Key': chave_api}

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        decoded_response = response.json()

        return decoded_response

    except requests.RequestException as e:
        return {'error': f"Erro na chamada à API: {e}"}

def ler_dados_do_arquivo(file):
    try:
        # Ler dados do arquivo em um buffer de bytes
        file_buffer = io.BytesIO()
        file.save(file_buffer)
        file_buffer.seek(0)
        
        data_frame = pd.read_excel(file_buffer)

        return data_frame

    except Exception as e:
        raise Exception(f"Erro ao ler dados do arquivo: {e}")

def adicionar_dados_ao_dataframe(data_frame):
    try:
        # Adicionar colunas para armazenar resultados
        data_frame['ipAddress'] = ''
        data_frame['isPublic'] = ''
        data_frame['ipVersion'] = ''
        data_frame['isWhitelisted'] = ''
        data_frame['abuseConfidenceScore'] = ''
        data_frame['countryCode'] = ''
        data_frame['usageType'] = ''
        data_frame['isp'] = ''
        data_frame['domain'] = ''
        data_frame['hostnames'] = ''
        data_frame['isTor'] = ''
        data_frame['totalReports'] = ''
        data_frame['numDistinctUsers'] = ''
        data_frame['lastReportedAt'] = ''

        return data_frame

    except Exception as e:
        raise Exception(f"Erro ao adicionar dados ao DataFrame: {e}")

def criar_excel_com_dados(data_frame):
    try:
        # Criar um buffer de bytes
        excel_buffer = io.BytesIO()
        data_frame.to_excel(excel_buffer, index=False, sheet_name='Sheet1')
        excel_buffer.seek(0)

        return excel_buffer

    except Exception as e:
        raise Exception(f"Erro ao criar arquivo Excel: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/consulta', methods=['POST'])
def consulta():
    try:
        file = request.files['file']

        # Ler dados do arquivo
        data_frame = ler_dados_do_arquivo(file)

        # Adicionar dados ao DataFrame
        data_frame_com_dados = adicionar_dados_ao_dataframe(data_frame)

        # Criar Excel com os dados
        excel_buffer = criar_excel_com_dados(data_frame_com_dados)

        return send_file(excel_buffer, download_name='resultados.xlsx', as_attachment=True)

    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    # Use a porta 8080 se executando localmente
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
