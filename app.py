import pandas as pd
import requests
from flask import Flask, render_template, request, send_file, send_from_directory
import io
import os
import random
import time
import signal

app = Flask(__name__)

# ... (Código existente)

# Chaves de API 
chaves_api = ["1a1567e352662065b726580c17ab22197f40cb72601994f3a9eb491ac39c4a0772a47345c62ed923",
              "7137ed136f3c82f122cf0f58a881353850f40d9b3f9064f87258a21dd76e9da4c494d7d936b8f258",
              "4e0ff4e4dc8183e66aa93a6e4d9b3f7c4fc36753e1b706464f4b8630aeae7d21734eecebcb7c9f59",
              "75277ec9a079f414c3189d1f1a5fee817c278d10e80dba6c6383559a26644400c2e0ba6c8b61a272",
              "7e73bfc9677d4733416ab07477f432d555784d98916d68495e094498643be6c3e85f6d56f3e3ecf7"]

# Transformar a lista de chaves em uma única string separada por vírgulas
chave_api = ','.join(chaves_api)

# Tempo mínimo para aguardar antes de tentar novamente com uma chave diferente (em segundos)
tempo_espera_minimo = 60

# Dicionário para rastrear o estado de cada chave (ativa ou inativa)
estado_chaves = {chave: 'ativa' for chave in chaves_api}

def obter_chave_api_aleatoria():
    # Filtrar chaves que estão ativas
    chaves_disponiveis = [chave for chave in chaves_api if estado_chaves[chave] == 'ativa']
    
    if not chaves_disponiveis:
        # Se nenhuma chave estiver disponível, esperar e tentar novamente
        time.sleep(tempo_espera_minimo)
        return obter_chave_api_aleatoria()

    return random.choice(chaves_disponiveis)

def verificar_limite_chave(chave):
    url = 'https://api.abuseipdb.com/api/v2/check'
    querystring = {'ipAddress': '8.8.8.8', 'maxAgeInDays': '90'}
    headers = {'Accept': 'application/json', 'Key': chave}

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        decoded_response = response.json()

        # Verifica se a resposta contém informações sobre limites
        if 'errors' in decoded_response:
            for error in decoded_response['errors']:
                if 'status' in error and error['status'] == 429:
                    # A chave atingiu o limite, marque como inativa
                    estado_chaves[chave] = 'inativa'
                    print(f"A chave {chave} atingiu o limite. Marcada como inativa.")
                    return False

        return True

    except requests.RequestException as e:
        return {'error': f"Erro na chamada à API: {e}"}

def buscar_abuse_ip(ip_address):
    url = 'https://api.abuseipdb.com/api/v2/check'
    querystring = {'ipAddress': ip_address, 'maxAgeInDays': '90'}
    
    chave_atual = obter_chave_api_aleatoria()
    
    # Adicionar lógica para verificar se a chave atingiu o limite antes de fazer a chamada à API
    while not verificar_limite_chave(chave_atual):
        chave_atual = obter_chave_api_aleatoria()

    headers = {'Accept': 'application/json', 'Key': chave_atual}

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

        # Buscar informações do IP para cada linha
        for index, row in data_frame.iterrows():
            ip_address = row['Source']
            result = buscar_abuse_ip(ip_address)

            if 'error' not in result:
                decoded_response = result.get('data', {})
                # Adiciona os dados ao DataFrame
                data_frame.at[index, 'ipAddress'] = decoded_response.get('ipAddress', '')
                data_frame.at[index, 'isPublic'] = decoded_response.get('isPublic', '')
                data_frame.at[index, 'ipVersion'] = decoded_response.get('ipVersion', '')
                data_frame.at[index, 'isWhitelisted'] = decoded_response.get('isWhitelisted', '')
                data_frame.at[index, 'abuseConfidenceScore'] = decoded_response.get('abuseConfidenceScore', '')
                data_frame.at[index, 'countryCode'] = decoded_response.get('countryCode', '')
                data_frame.at[index, 'usageType'] = decoded_response.get('usageType', '')
                data_frame.at[index, 'isp'] = decoded_response.get('isp', '')
                data_frame.at[index, 'domain'] = decoded_response.get('domain', '')
                data_frame.at[index, 'hostnames'] = decoded_response.get('hostnames', '')
                data_frame.at[index, 'isTor'] = decoded_response.get('isTor', '')
                data_frame.at[index, 'totalReports'] = decoded_response.get('totalReports', '')
                data_frame.at[index, 'numDistinctUsers'] = decoded_response.get('numDistinctUsers', '')
                data_frame.at[index, 'lastReportedAt'] = decoded_response.get('lastReportedAt', '')

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

# Configurar o tempo limite em segundos
timeout_seconds = 800

def timeout_handler(signum, frame):
    raise TimeoutError("A execução excedeu o tempo limite.")

@app.before_request
def before_request():
    # Configurar o sinal de timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    # Configurar o tempo limite em segundos
    signal.alarm(timeout_seconds)

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

        return send_file(excel_buffer, download_name='Resultado Consulta de IPs.xlsx', as_attachment=True)

    except Exception as e:
        return {'error': str(e)}

    finally:
        # Desativar o sinal de timeout após a conclusão da rota
        signal.alarm(0)

# Mapear o endpoint /favicon.ico para o arquivo no diretório static
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == "__main__":
    # Use a porta 8080 se executando localmente
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
