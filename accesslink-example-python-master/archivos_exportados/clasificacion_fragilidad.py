# classify_frailty.py
import pandas as pd
import argparse

def classify_frailty_by_rules(row):
    """
    Aplica un sistema de puntuación basado en reglas para clasificar una fila de datos.
    Puntuación: 2 (Robusto), 1 (Pre-frágil), 0 (Frágil)
    """
    score = 0
    
    # 1. Pasos Activos (Métrica de Actividad)
    # Más es mejor
    if row['active-steps'] > 6000:
        score += 2
    elif row['active-steps'] > 2500:
        score += 1
        
    # 2. Variabilidad de la Frecuencia Cardíaca (Métrica de Resiliencia Fisiológica)
    # Más es mejor
    if row['heart_rate_variability_avg'] > 35:
        score += 2
    elif row['heart_rate_variability_avg'] > 25:
        score += 1
        
    # 3. Frecuencia Cardíaca Media Nocturna (Métrica de Estrés Fisiológico)
    # Menos es mejor
    if row['heart_rate_avg'] < 65:
        score += 2
    elif row['heart_rate_avg'] < 72:
        score += 1
        
    # 4. Puntuación del Sueño (Métrica de Calidad del Descanso)
    # Más es mejor
    if row['sleep_score'] > 75:
        score += 2
    elif row['sleep_score'] > 60:
        score += 1
    
    # --- Clasificación Final basada en la Puntuación Total (Máximo 8 puntos) ---
    if score >= 6:
        return 'robusto'
    elif score >= 3:
        return 'pre-fragil'
    else:
        return 'fragil'

def main(input_file, output_file):
    """
    Función principal para cargar, clasificar y guardar los datos.
    """
    try:
        df = pd.read_csv(input_file)
        print(f"✓ Archivo '{input_file}' cargado con {len(df)} filas.")
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de entrada '{input_file}'.")
        return

    # Aplicar la función de clasificación a cada fila del DataFrame
    # axis=1 le dice a apply que trabaje por filas
    df['frailty_status'] = df.apply(classify_frailty_by_rules, axis=1)
    
    # Guardar el DataFrame con la nueva columna
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"✓ Clasificación completada. Archivo guardado como '{output_file}'.")
    
    # Mostrar un resumen de la clasificación
    print("\nResumen de la clasificación:")
    print(df['frailty_status'].value_counts())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clasifica datos de smartwatch en niveles de fragilidad.")
    parser.add_argument("input_file", help="Ruta al fichero CSV de entrada (datos_smartwatch.csv).")
    parser.add_argument("output_file", help="Ruta para guardar el fichero CSV clasificado.")
    
    args = parser.parse_args()
    main(args.input_file, args.output_file)