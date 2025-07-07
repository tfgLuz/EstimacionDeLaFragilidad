# polar_temperature.py
import requests
import yaml
import json
import argparse
from datetime import datetime, timedelta
from flask import Flask, request, redirect
import pandas as pd
import os

# --- CONFIGURACIÓN GLOBAL ---
CONFIG_FILENAME = "config.yml"
CALLBACK_PORT = 5000
CALLBACK_ENDPOINT = "/oauth2_callback"
REDIRECT_URL = f"http://localhost:{CALLBACK_PORT}{CALLBACK_ENDPOINT}"
EXPORT_FOLDER = "archivos_exportados"

# --- LÓGICA DE AUTORIZACIÓN (OAuth2 con Flask) ---
# (Esta sección no cambia)
app = Flask(__name__)

def load_config():
    try:
        with open(CONFIG_FILENAME, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: El archivo '{CONFIG_FILENAME}' no fue encontrado.")
        return None

def save_config(config):
    with open(CONFIG_FILENAME, 'w') as f:
        yaml.dump(config, f)

@app.route("/")
def authorize():
    config = load_config()
    auth_url = (f"https://flow.polar.com/oauth2/authorization?"
                f"response_type=code&client_id={config['client_id']}"
                f"&scope=accesslink.read_all&redirect_uri={REDIRECT_URL}")
    return redirect(auth_url)

@app.route(CALLBACK_ENDPOINT)
def callback():
    config = load_config()
    authorization_code = request.args.get("code")
    token_url = "https://polarremote.com/v2/oauth2/token"
    token_data = {"grant_type": "authorization_code", "code": authorization_code, "redirect_uri": REDIRECT_URL}
    token_auth = (config['client_id'], config['client_secret'])
    
    try:
        token_response = requests.post(token_url, data=token_data, auth=token_auth)
        token_response.raise_for_status()
        json_response = token_response.json()
        config["access_token"] = json_response["access_token"]
        config["user_id"] = token_response.headers.get("x-user-id")
        save_config(config)

        register_url = "https://www.polaraccesslink.com/v3/users"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {config['access_token']}"}
        body = {"member-id": str(config["user_id"])}
        reg_response = requests.post(register_url, headers=headers, json=body) 
        
        if reg_response.status_code != 409:
            reg_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        error_text = f"Error durante la obtención del token: {e}"
        if e.response: error_text += f" | Detalles: {e.response.text}"
        return error_text, 500

    shutdown_func = request.environ.get('werkzeug.server.shutdown')
    if shutdown_func: shutdown_func()
    return "¡Autorización completada! Ahora puedes usar los comandos 'fetch' o 'export'."

def run_auth_server():
    print(f"Para autorizar, abre tu navegador y ve a: http://localhost:{CALLBACK_PORT}/")
    app.run(host='localhost', port=CALLBACK_PORT)

# --- CLASE CLIENTE (No cambia) ---
class PolarApiClient:
    def __init__(self, access_token):
        self.access_token = access_token
        self.base_url = "https://www.polaraccesslink.com/v3/users/biosensing/"

    def _make_request(self, endpoint, params):
        headers = {"Accept": "application/json", "Authorization": f"Bearer {self.access_token}"}
        url = self.base_url + endpoint
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200: return response.json()
        elif response.status_code == 204: return None
        else: response.raise_for_status()

    def get_temperature_data(self, start_date, end_date):
        params = {"from": start_date.isoformat(), "to": end_date.isoformat()}
        return self._make_request("bodytemperature", params)

# --- FUNCIÓN DE EXPORTACIÓN MODIFICADA PARA CALCULAR ESTADÍSTICAS ---

def export_body_temp_to_csv(data, filename):
    """
    Procesa los datos de temperatura, calcula estadísticas por día
    y los guarda en un CSV.
    """
    if not data:
        print("No hay datos de temperatura corporal para exportar.")
        return
    
    daily_stats = []
    for measurement in data:
        samples = measurement.get('samples', [])
        if not samples:
            continue

        df = pd.DataFrame(samples)
        temp_series = df['temperature_celsius']
        mean_temp = temp_series.mean()
        
        # --- INICIO DE LA CORRECCIÓN ---
        # Comprueba si la columna de duración existe antes de usarla.
        if 'recordingTimeDeltaMilliseconds' in df.columns:
            # Si existe, se ua para calcular la duración.
            # Rellena el NaN de la primera fila con 0.
            df['recordingTimeDeltaMilliseconds'] = df['recordingTimeDeltaMilliseconds'].fillna(0)
            duration_ms = df['recordingTimeDeltaMilliseconds'].astype(float).max()
        else:
            # Si no existe (porque solo hay una muestra), la duración es 0.
            duration_ms = 0
        # --- FIN DE LA CORRECCIÓN ---

        stats = {
            'date': measurement.get('start_time', '')[:10],
            'temp_mean': mean_temp,
            'temp_max': temp_series.max(),
            'temp_min': temp_series.min(),
            'temp_std': temp_series.std(),
            'temp_deviation_mean': (temp_series - mean_temp).mean(),
            'temp_deviation_max': (temp_series - mean_temp).max(),
            'temp_amplitude': temp_series.max() - temp_series.min(),
            'num_samples': len(df),
            'duration_hours': duration_ms / (1000 * 60 * 60)
        }
        daily_stats.append(stats)
    
    if not daily_stats:
        print("No se encontraron mediciones con muestras para exportar.")
        return

    final_df = pd.DataFrame(daily_stats)
    final_df.to_csv(filename, sep=',', index=False, encoding='utf-8-sig', float_format='%.4f')
    print(f"✓ Estadísticas de temperatura corporal exportadas a '{filename}'")

# --- FUNCIÓN DE VISUALIZACIÓN CORREGIDA ---

def process_and_display_body_temp(data):
    """Muestra las nuevas estadísticas en la terminal."""
    if not data: 
        print("No se encontraron datos de temperatura corporal."); return
        
    print("\n--- Resumen Estadístico de Temperatura Corporal ---")
    for measurement in data:
        samples = measurement.get('samples', [])
        if samples:
            # --- CORRECCIÓN AQUÍ ---
            # También cambiamos el nombre de la clave en este cálculo
            avg_temp = sum(s['temperature_celsius'] for s in samples) / len(samples)
            
            date_str = measurement.get('start_time', 'N/A')[:10]
            
            print(f"\nFecha: {date_str}")
            print(f"  ├─ Temp. Media: {avg_temp:.2f}°C")
            print(f"  └─ Nº Muestras: {len(samples)}")

# --- FUNCIÓN DE VISUALIZACIÓN MODIFICADA ---
def process_and_display_body_temp(data):
    """Muestra las nuevas estadísticas en la terminal."""
    if not data: 
        print("No se encontraron datos de temperatura corporal."); return
        
    print("\n--- Resumen Estadístico de Temperatura Corporal ---")
    for measurement in data:
        samples = measurement.get('samples', [])
        if samples:
            df = pd.DataFrame(samples)
            temp_series = df['temperatureCelsius']
            date_str = measurement.get('start_time', 'N/A')[:10]
            
            print(f"\nFecha: {date_str}")
            print(f"  ├─ Temp. Media: {temp_series.mean():.2f}°C")
            print(f"  ├─ Temp. Máx/Mín: {temp_series.max():.2f}°C / {temp_series.min():.2f}°C")
            print(f"  └─ Nº Muestras: {len(df)}")

# --- FUNCIÓN PRINCIPAL (No cambia) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gestor de datos de temperatura corporal de Polar AccessLink.")
    parser.add_argument("command", choices=['auth', 'fetch', 'export'], 
                        help="'auth' para autorizar, 'fetch' para ver datos, 'export' para guardar en CSV.")
    
    args = parser.parse_args()

    if args.command == 'auth':
        run_auth_server()
    
    elif args.command == 'fetch' or args.command == 'export':
        config = load_config()
        if not config or "access_token" not in config:
            print("Token de acceso no encontrado. Ejecuta primero el comando 'auth'.")
        else:
            client = PolarApiClient(access_token=config["access_token"])
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=28)
            
            print(f"Obteniendo datos de temperatura corporal desde {start_date} hasta {end_date}...")
            
            try:
                body_temp_data = client.get_temperature_data(start_date, end_date)

                if args.command == 'fetch':
                    process_and_display_body_temp(body_temp_data)
                
                elif args.command == 'export':
                    os.makedirs(EXPORT_FOLDER, exist_ok=True)
                    output_file = os.path.join(EXPORT_FOLDER, 'body_temperature_summary.csv')
                    export_body_temp_to_csv(body_temp_data, output_file)

            except requests.exceptions.RequestException as e:
                print(f"\nError al contactar con la API de Polar: {e}")
                if e.response and e.response.status_code == 401:
                    print("El token de acceso puede haber expirado. Ejecuta de nuevo el comando 'auth'.")