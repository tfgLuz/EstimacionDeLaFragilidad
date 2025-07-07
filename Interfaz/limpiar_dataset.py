# limpiar_dataset.py
import pandas as pd
import argparse

def clean_missing_values(input_file, output_file):
    """
    Carga un dataset, imputa los valores NaN y guarda el resultado.
    """
    try:
        df = pd.read_csv(input_file)
        print(f"Archivo '{input_file}' cargado con {len(df)} filas.")
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de entrada '{input_file}'.")
        return

    # --- 1. Análisis de Valores Faltantes ---
    print("\n--- Análisis Inicial de Valores Faltantes ---")
    missing_values = df.isnull().sum()
    missing_cols = missing_values[missing_values > 0]
    if len(missing_cols) > 0:
        print(missing_cols)
    else:
        print("No se encontraron valores NaN.")
    
    # --- 2. Imputación de Valores NaN ---
    print("\nIniciando imputación de valores NaN...")
    for column in df.columns:
        if df[column].isnull().any():
            # Si es una columna numérica, rellenar con la mediana
            if pd.api.types.is_numeric_dtype(df[column]):
                median_value = df[column].median()
                df[column] = df[column].fillna(median_value)
                print(f"  - Columna numérica '{column}': NaN rellenados con la mediana ({median_value:.2f})")
            # Si es una columna de texto/objeto, rellenar con la moda
            else:
                if not df[column].dropna().empty:
                    mode_value = df[column].mode()[0]
                    df[column] = df[column].fillna(mode_value)
                    print(f"  - Columna de texto '{column}': NaN rellenados con la moda ('{mode_value}')")
                else:
                    # Si toda la columna es NaN, rellenar con un valor por defecto
                    df[column] = df[column].fillna("Desconocido")
                    print(f"  - Columna de texto '{column}': Estaba vacía, rellenada con 'Desconocido'")


    # --- 3. Verificación de Limpieza ---
    remaining_nans = df.isnull().sum().sum()
    if remaining_nans == 0:
        print("\n¡Éxito! Todos los valores NaN han sido eliminados/imputados.")
    
    # --- 4. Guardado Final ---
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Dataset final y limpio guardado correctamente en '{output_file}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Limpia valores NaN de un fichero CSV.")
    parser.add_argument("input_file", help="Ruta al fichero CSV de entrada.")
    parser.add_argument("output_file", help="Ruta para guardar el fichero CSV limpio.")
    
    args = parser.parse_args()
    clean_missing_values(args.input_file, args.output_file)
