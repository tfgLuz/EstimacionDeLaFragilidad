import pandas as pd

# --- CONFIGURACIÓN ---
nombres_archivos = {
    'actividades': 'polar_daily_activities.csv',
    'recarga': 'polar_recharge_summary.csv',
    'sueno': 'polar_sleep_summary.csv',
    'temperatura': 'body_temperature_summary.csv'
}

mapeo_columnas_fecha = {
    'actividades': 'date',
    'recarga': 'date',
    'sueno': 'date',
    'temperatura': 'date'
}

# --- VARIABLES RELEVANTES PARA FRAGILIDAD ---
columnas_relevantes = [
    'date',
    'active-steps', 'active-calories', 'calories', 'duration_minutes',
    'steps_per_minute', 'calories_per_step', 'active_calories_per_minute',
    'heart_rate_avg', 'heart_rate_variability_avg', 'ans_charge',
    'sleep_score', 'light_sleep_min', 'deep_sleep_min', 'rem_sleep_min',
    'interruptions_min', 'breathing_rate_avg','temp_amplitude'
]

# --- PROCESAMIENTO ---
dataframes = {}

print("Leyendo archivos...")
for nombre, archivo in nombres_archivos.items():
    try:
        df = pd.read_csv(archivo)
        columna_fecha_original = mapeo_columnas_fecha[nombre]
        
        # Se asegura de que la columna 'date' exista y tenga el formato correcto
        df['date'] = pd.to_datetime(df[columna_fecha_original]).dt.date
        
        # Solo borra la columna de fecha original si su nombre no es 'date'
        if columna_fecha_original != 'date':
            df = df.drop(columns=[columna_fecha_original])
            
        dataframes[nombre] = df
        print(f"-> Archivo '{archivo}' leído y procesado.")
    except FileNotFoundError:
        print(f"¡ERROR! No se encontró el archivo: {archivo}")
    except KeyError:
        print(f"¡ERROR! La columna '{mapeo_columnas_fecha[nombre]}' no se encontró en el archivo '{archivo}'.")
    except Exception as e:
        print(f"Ocurrió un error inesperado con el archivo {archivo}: {e}")
if len(dataframes) == len(nombres_archivos):
    df_final = dataframes['actividades']
    for nombre, df_a_unir in list(dataframes.items())[1:]:
        df_final = pd.merge(df_final, df_a_unir, on='date', how='outer', suffixes=('', f'_{nombre}'))
    df_final = df_final.sort_values(by='date').reset_index(drop=True)

    # --- FILTRAR SÓLO LAS COLUMNAS RELEVANTES ---
    columnas_presentes = [col for col in columnas_relevantes if col in df_final.columns]
    df_filtrado = df_final[columnas_presentes]

    # --- GUARDADO ---
    nombre_archivo_salida = 'datos_smartwatch.csv'
    df_filtrado.to_csv(nombre_archivo_salida, index=False, encoding='utf-8-sig')

    print("\n¡Unión y filtrado completados con éxito!")
    print(f"Archivo creado: '{nombre_archivo_salida}' con {len(df_filtrado)} filas y {len(df_filtrado.columns)} columnas.")
else:
    print("\nNo se pudo completar la unión debido a errores al leer los archivos.")
