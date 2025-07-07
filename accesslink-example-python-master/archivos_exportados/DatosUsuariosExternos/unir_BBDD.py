import pandas as pd

# --- CONFIGURACIÓN ---

# 1. Nombres de los archivos de datos y su columna de fecha
ARCHIVOS_DATOS = {
    'actividades': {
        'path': 'polar_daily_activities_util.csv', 
        'date_col': 'date'
    },
    'recarga': {
        'path': 'polar_recharge_summary.csv',
        'date_col': 'date'
    },
    'sueno': {
        'path': 'polar_sleep_summary.csv',
        'date_col': 'date'
    },
    'temperatura': {
        'path': 'temperatura_procesada.csv',
        'date_col': 'date'
    }
}

# 2. Archivo de usuarios (la fuente de la verdad)
ARCHIVO_USUARIOS = {
    'path': 'usuarios.csv',
    'user_col': 'id_usuario',
    'birth_col': 'fecha_nacimiento',
    'start_date_col': 'fecha_inicio',
    'end_date_col': 'fecha_fin'
}

# 3. Columnas deseadas en el archivo final
COLUMNAS_RELEVANTES = [
    'fecha_comun',
    'active-steps', 'active-calories', 'calories', 'duration_minutes',
    'steps_per_minute', 'calories_per_step', 'active_calories_per_minute',
    'heart_rate_avg', 'heart_rate_variability_avg', 'ans_charge',
    'sleep_score', 'light_sleep_min', 'deep_sleep_min', 'rem_sleep_min',
    'interruptions_min', 'breathing_rate_avg',
    'temp_mean', 'temp_std', 'temp_amplitude'
]

# 4. Nombre del archivo de salida
ARCHIVO_SALIDA = 'datos_smartwatch.csv'

# --- FUNCIONES ---

def calcular_edad(fecha_nacimiento, fecha_registro):
    if pd.isna(fecha_nacimiento) or pd.isna(fecha_registro):
        return None
    return fecha_registro.year - fecha_nacimiento.year - \
           ((fecha_registro.month, fecha_registro.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

# --- PROCESAMIENTO PRINCIPAL ---

if __name__ == "__main__":
    print("🚀 Iniciando el proceso de unión y agregación...")

    try:
        # --- PASO 1 y 2: Lectura y enriquecimiento de datos (sin cambios) ---
        df_usuarios = pd.read_csv(ARCHIVO_USUARIOS['path'])
        user_date_cols = [ARCHIVO_USUARIOS['start_date_col'], ARCHIVO_USUARIOS['end_date_col']]
        for col in user_date_cols:
            df_usuarios[col] = pd.to_datetime(df_usuarios[col], errors='coerce')

        date_to_user_map_list = []
        for _, row in df_usuarios.iterrows():
            user_id = row[ARCHIVO_USUARIOS['user_col']]
            start_date = row[ARCHIVO_USUARIOS['start_date_col']]
            end_date = row[ARCHIVO_USUARIOS['end_date_col']]
            if pd.notna(start_date) and pd.notna(end_date):
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                temp_df = pd.DataFrame({'fecha_comun': date_range, 'id_usuario': user_id})
                date_to_user_map_list.append(temp_df)
        df_lookup = pd.concat(date_to_user_map_list, ignore_index=True)
        print(f"✅ Tabla de consulta creada: {len(df_lookup)} registros.")

        processed_dataframes = []
        for nombre, config in ARCHIVOS_DATOS.items():
            print(f"🔄 Procesando '{config['path']}'...")
            df_data = pd.read_csv(config['path'])
            df_data = df_data.rename(columns={config['date_col']: 'fecha_comun'})
            df_data['fecha_comun'] = pd.to_datetime(df_data['fecha_comun'], errors='coerce')
            df_data = df_data.dropna(subset=['fecha_comun'])
            df_enriched = pd.merge(df_data, df_lookup, on='fecha_comun', how='inner')
            if not df_enriched.empty:
                processed_dataframes.append(df_enriched)

        # --- PASO 3: Unión de todos los datos (sin cambios) ---
        if not processed_dataframes:
            raise ValueError("Ningún dato coincidió con los rangos de fecha de los usuarios.")
        df_final = processed_dataframes[0]
        for df_a_unir in processed_dataframes[1:]:
            df_final = pd.merge(df_final, df_a_unir, on=['id_usuario', 'fecha_comun'], how='outer')
        print("\n🔗 Todos los archivos de datos han sido unidos.")

        # --- PASO 4: Añadir edad (sin cambios) ---
        df_usuarios[ARCHIVO_USUARIOS['birth_col']] = pd.to_datetime(df_usuarios[ARCHIVO_USUARIOS['birth_col']], errors='coerce')
        df_usuarios_info = df_usuarios[[ARCHIVO_USUARIOS['user_col'], ARCHIVO_USUARIOS['birth_col']]].rename(columns={
            ARCHIVO_USUARIOS['user_col']: 'id_usuario', ARCHIVO_USUARIOS['birth_col']: 'fecha_nacimiento'})
        df_final = pd.merge(df_final, df_usuarios_info, on='id_usuario', how='left')
        df_final['edad'] = df_final.apply(lambda row: calcular_edad(row['fecha_nacimiento'], row['fecha_comun']), axis=1)
        df_final = df_final.drop(columns=['fecha_nacimiento'])
        print("👤 Edad calculada y añadida.")
        
        # --- PASO 4.5: AGRUPAR Y AGREGAR DATOS POR DÍA ---
        # Lógica de agregación:
        # - max: para las métricas de actividad (coger el valor máximo del día)
        # - mean: para las tasas o promedios (calcular la media del día)
        # - first: para datos que son constantes en un día (coger el primer valor)
        print("📊 Agrupando filas duplicadas por día...")
        
        columnas_a_agregar = {
            # Columnas de actividad: coger el valor máximo del día
            'active-steps': 'max',
            'active-calories': 'max',
            'duration_minutes': 'max',
            'calories': 'max',             
            
            # Columnas de ratios o promedios: calcular la media
            'steps_per_minute': 'mean',
            'breathing_rate_avg': 'mean',
            
            # El resto de columnas son constantes para un día, así que cogemos el primer valor
            'edad': 'first',
            'heart_rate_avg': 'first',
            'heart_rate_variability_avg': 'first',
            'ans_charge': 'first',
            'sleep_score': 'first',
            'light_sleep_min': 'first',
            'deep_sleep_min': 'first',
            'rem_sleep_min': 'first',
            'interruptions_min': 'first',
            'nightly_recharge_status': 'first',
            'temp_mean': 'first',
            'temp_std': 'first',
            'temp_amplitude': 'first'
        }

        # Filtrar el diccionario de agregación para usar solo las columnas que existen en df_final
        agg_rules = {col: rule for col, rule in columnas_a_agregar.items() if col in df_final.columns}
        
        df_agregado = df_final.groupby(['id_usuario', 'fecha_comun']).agg(agg_rules).reset_index()
        print("  -> ¡Agregación completada!")

        # --- PASO 5: Filtrar columnas finales y guardar ---
        columnas_finales = ['id_usuario', 'edad'] + COLUMNAS_RELEVANTES
        columnas_a_mantener = [col for col in columnas_finales if col in df_agregado.columns]
        df_resultado = df_agregado[columnas_a_mantener].copy()
        
        df_resultado['fecha_comun'] = pd.to_datetime(df_resultado['fecha_comun']).dt.date
        df_resultado = df_resultado.sort_values(by=['id_usuario', 'fecha_comun']).reset_index(drop=True)

        df_resultado.to_csv(ARCHIVO_SALIDA, index=False, encoding='utf-8-sig')
        print(f"\n🎉 ¡Proceso completado! Se ha creado el archivo '{ARCHIVO_SALIDA}' con {len(df_resultado)} filas (una por día y usuario).")

    except (FileNotFoundError, KeyError, ValueError) as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("   -> Por favor, revisa los nombres de archivo y columnas en la sección de CONFIGURACIÓN.")