# prepararDF.py
import pandas as pd
import argparse

def preparar_dataframe(activity_file, recharge_file, sleep_file, temp_file, output_file):
    """
    Carga 4 archivos CSV, los une por fecha, elimina filas con valores nulos
    y guarda el resultado.
    """
    try:
        # Carga los archivos CSV
        activity_df = pd.read_csv(activity_file)
        recharge_df = pd.read_csv(recharge_file)
        sleep_df = pd.read_csv(sleep_file)
        temperature_df = pd.read_csv(temp_file)
        print("Archivos de entrada cargados correctamente.")

        # Convierte la columna 'date' a datetime para asegurar consistencia
        for df in [activity_df, recharge_df, sleep_df, temperature_df]:
            df['date'] = pd.to_datetime(df['date'])

        # Une los datasets por la columna 'date'
        merged_df = activity_df \
            .merge(recharge_df, on='date', how='inner') \
            .merge(sleep_df, on='date', how='inner') \
            .merge(temperature_df, on='date', how='inner')
        print(f"Datasets unidos. Total de filas antes de limpiar: {len(merged_df)}")

        # Elimina las filas que contengan NaN
        cleaned_df = merged_df.dropna()
        print(f"Filas con NaN eliminadas. Total de filas final: {len(cleaned_df)}")

        # Guarda el resultado final
        cleaned_df.to_csv(output_file, index=False)
        print(f"Datos fusionados y limpiados guardados en '{output_file}'")

    except FileNotFoundError as e:
        print(f"Error: No se encontró el archivo {e.filename}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Une y limpia 4 datasets de salud.")
    parser.add_argument("--inputs", nargs=4, required=True, help="Ruta a los 4 archivos de entrada (actividad, recuperacion, sueno, temperatura).")
    parser.add_argument("--output", required=True, help="Ruta para guardar el fichero CSV final.")
    
    args = parser.parse_args()
    
    preparar_dataframe(
        activity_file=args.inputs[0],
        recharge_file=args.inputs[1],
        sleep_file=args.inputs[2],
        temp_file=args.inputs[3],
        output_file=args.output
    )
