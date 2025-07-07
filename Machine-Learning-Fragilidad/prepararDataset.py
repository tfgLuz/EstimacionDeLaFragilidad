import pandas as pd

# --- 1. Cargar los Datasets ---
try:
    # Carga los datos reales y los sintéticos
    df_real = pd.read_csv('datasetRealML.csv')
    df_sintetico = pd.read_csv('datasetIAML.csv')
    print(" Archivos cargados correctamente.")
except FileNotFoundError:
    print(" Error: Asegúrate de que los archivos 'datasetRealML.csv' y 'datasetIAML.csv' están en la misma carpeta.")
    exit()

# --- 2. Combinar los Datasets ---
# Se unen los dos dataframes en uno solo
df_combinado = pd.concat([df_real, df_sintetico], ignore_index=True)
print(f"🔹 Shape tras combinar: {df_combinado.shape}")


# --- 3. Limpiar Valores Nulos ---
# Se eliminan las filas que no tienen datos de sueño (el Día 1 de los datos sintéticos)
df_limpio = df_combinado.dropna()
print(f"🔹 Shape tras limpiar NaNs: {df_limpio.shape}")

print(df_real.columns)
print(df_sintetico.columns)

# --- 4. Codificar la Variable Objetivo ---
# Se crea el mapa para la codificación
mapa_fragilidad = {
    'robusto': 2,
    'pre-fragil': 1,
    'fragil': 0
}

# Se aplica el mapa a la columna 'frailty_status'
df_limpio['frailty_status'] = df_limpio['frailty_status'].map(mapa_fragilidad)
print("✅ Columna 'frailty_status' codificada a valores numéricos (2, 1, 0).")


# --- 5. Guardar el Resultado ---
# Se guarda el dataframe limpio y preparado en un nuevo archivo CSV
df_limpio.to_csv('dataset_preparado.csv', index=False)
print("\n ¡Proceso completado! El archivo 'dataset_preparado.csv' está listo para ser usado.")

# Opcional: Mostrar las primeras 5 filas del resultado
print("\n--- Muestra del dataset final ---")
print(df_limpio.head())