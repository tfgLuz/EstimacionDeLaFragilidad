# app.py 
import streamlit as st
import pandas as pd
import os
import subprocess
import joblib

# --- 1. Configuración de la Página y Constantes ---
st.set_page_config(
    page_title="Estimador de Fragilidad",
    page_icon="👨‍⚕️",
    layout="wide"
)

st.title("👨‍⚕️ Estimador de Fragilidad Basado en Datos de Smartwatch")

# --- Constantes de Archivos ---
UPLOAD_DIR = "temp_uploads"
ACTIVITY_FILE = os.path.join(UPLOAD_DIR, "activity.csv")
RECHARGE_FILE = os.path.join(UPLOAD_DIR, "recharge.csv")
SLEEP_FILE = os.path.join(UPLOAD_DIR, "sleep.csv")
TEMP_FILE = os.path.join(UPLOAD_DIR, "temperature.csv")
CONSOLIDATED_FILE = os.path.join(UPLOAD_DIR, "datos_consolidados.csv")
COMPLETE_RAW_FILE = os.path.join(UPLOAD_DIR, "dataset_completo_raw.csv")
COMPLETE_CLEANED_FILE = os.path.join(UPLOAD_DIR, "dataset_completo_limpio.csv")
PIPELINE_FILE = 'fragility_pipeline.joblib'

os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- 2. Funciones Auxiliares ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))

def run_script(script_name, args=[]):
    """Ejecuta un script externo y muestra su salida."""
    script_path = os.path.join(APP_DIR, script_name)
    
    command = ["python", script_path] + args
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, encoding='latin-1'
        )
        st.info(f"Salida de '{script_name}':\n{result.stdout}")
        return True
    except FileNotFoundError:
        st.error(f"Error: No se encontró el intérprete de Python o el script '{script_path}'.")
        return False
    except subprocess.CalledProcessError as e:
        st.error(f"Error al ejecutar '{script_name}':\n{e.stderr}")
        return False

def display_prediction_results(df_to_predict, probabilities):
    """Toma las probabilidades y muestra los resultados en un formato amigable."""
    predictions_numeric = probabilities.argmax(axis=1)
    
    label_map = {
        0: 'Frágil',
        1: 'Pre-frágil',
        2: 'Robusto'
    }
    predictions_text = [label_map.get(p, 'Desconocido') for p in predictions_numeric]

    results_df = pd.DataFrame({'date': df_to_predict['date']})
    results_df['predicted_frailty'] = predictions_text
    
    for class_index, class_name in label_map.items():
        if class_index < probabilities.shape[1]:
            results_df[f'prob_{class_name}'] = probabilities[:, class_index].round(3)

    st.success("¡Predicción completada!")
    st.dataframe(results_df)
    st.subheader("Resumen de la Clasificación")
    st.bar_chart(results_df['predicted_frailty'].value_counts())


    # --- Gráfico de línea para la evolución ---
    st.subheader("Evolución de la Fragilidad en el Tiempo")
    
    # Definir el orden de las categorías para que el eje Y se muestre lógicamente
    category_order = ['Robusto', 'Pre-frágil', 'Frágil']
    
    # Crear una copia del dataframe para la gráfica
    plot_df = results_df.copy()
    
    # Convertir la columna de predicción a un tipo categórico con orden
    plot_df['predicted_frailty'] = pd.Categorical(
        plot_df['predicted_frailty'], 
        categories=category_order, 
        ordered=True
    )
    
    # Ordenar por fecha para que la línea tenga sentido
    plot_df = plot_df.sort_values('date')

    # Para st.line_chart, es mejor tener la fecha como índice
    plot_df = plot_df.set_index('date')

    # Generar el gráfico de línea
    st.line_chart(
        plot_df['predicted_frailty']
    )

def predict_on_dataframe(df):
    """Función central que realiza la predicción sobre un dataframe ya limpio."""
    try:
        pipeline = joblib.load(os.path.join(APP_DIR, PIPELINE_FILE))
        
        numeric_features = [
            'age', 'active-steps', 'active-calories', 'calories', 'duration_minutes',
            'heart_rate_avg', 'heart_rate_variability_avg', 'ans_charge', 'sleep_score',
            'light_sleep_min', 'deep_sleep_min', 'rem_sleep_min', 'interruptions_min',
            'breathing_rate_avg', 'temp_amplitude'
        ]
        
        missing_cols = list(set(numeric_features) - set(df.columns))
        if missing_cols:
            st.error(f"Error Crítico: Faltan columnas para la predicción: {missing_cols}")
            return

        probabilities = pipeline.predict_proba(df)
        display_prediction_results(df, probabilities)

    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo del modelo '{PIPELINE_FILE}'. Asegúrate de haber entrenado el modelo.")
    except Exception as e:
        st.error(f"Ocurrió un error durante la predicción: {e}")

# --- 3. Interfaz con Pestañas ---
tab1, tab2, tab3 = st.tabs([
    "📘 Instrucciones",
    "🚀 Predecir desde 4 Archivos", 
    "📂 Examinar Dataset Completo",
])

# --- Pestaña 1: Instrucciones ---
with tab1:
    st.header("📘 Instrucciones de Uso y Formato")

    st.subheader("Opción A: Predecir desde 4 Archivos")
    st.markdown("""
    1.  **Introduce la Edad**: Escribe la edad del sujeto en el campo numérico.
    2.  **Carga los 4 Archivos**: Sube cada uno de los ficheros CSV correspondientes.
    3.  **Ejecuta**: Pulsa el botón "Unir, Limpiar y Predecir".
    
    La aplicación unirá los archivos por fecha, eliminará los días que no tengan datos completos en los 4 ficheros, añadirá la edad y realizará la predicción.
    """)

    st.subheader("Opción B: Examinar Dataset Completo")
    st.markdown("""
    1.  **Prepara tu Archivo**: Asegúrate de que tu fichero CSV contiene **todas** las columnas necesarias que usa el modelo, incluyendo `date` y `age`.
    2.  **Carga el Archivo**: Sube el fichero CSV completo.
    3.  **Ejecuta**: Pulsa el botón "Limpiar y Predecir Dataset".

    La aplicación tomará tu archivo, rellenará cualquier valor `NaN` que encuentre usando la mediana (para números) o la moda (para texto), y luego realizará la predicción.
    """)

    st.subheader("Columnas Requeridas por el Modelo")
    st.code("""
        # El modelo necesita obligatoriamente estas columnas:
        date, age, active-steps, active-calories, calories, duration_minutes,
        heart_rate_avg, heart_rate_variability_avg, ans_charge, sleep_score,
        light_sleep_min, deep_sleep_min, rem_sleep_min, interruptions_min,
        breathing_rate_avg, temp_amplitude
            """, language="text")
# --- Pestaña 2: Flujo de 4 archivos + edad ---
with tab2:
    st.header("Opción A: Predecir uniendo 4 archivos")
    st.write("Carga los 4 ficheros CSV por separado. La edad se introduce manualmente.")
    
    age_input = st.number_input(
        "Introduce la Edad del Usuario", 
        min_value=18, max_value=120, value=75, step=1, key="age_input_tab1"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        uploaded_activity = st.file_uploader("1. Fichero de Actividad", type="csv", key="act_up")
        uploaded_recharge = st.file_uploader("2. Fichero de Recuperación", type="csv", key="rec_up")
    with col2:
        uploaded_sleep = st.file_uploader("3. Fichero de Sueño", type="csv", key="sle_up")
        uploaded_temp = st.file_uploader("4. Fichero de Temperatura", type="csv", key="tem_up")
    
    if st.button("Unir, Limpiar y Predecir", key="btn_tab1"):
        if all([uploaded_activity, uploaded_recharge, uploaded_sleep, uploaded_temp]):
            # Guardar archivos
            with open(ACTIVITY_FILE, "wb") as f: f.write(uploaded_activity.getbuffer())
            with open(RECHARGE_FILE, "wb") as f: f.write(uploaded_recharge.getbuffer())
            with open(SLEEP_FILE, "wb") as f: f.write(uploaded_sleep.getbuffer())
            with open(TEMP_FILE, "wb") as f: f.write(uploaded_temp.getbuffer())
            st.success("Archivos cargados.")

            # Unir y limpiar con prepararDF.py
            st.subheader("Paso 1: Uniendo y Limpiando Datasets")
            input_files = [ACTIVITY_FILE, RECHARGE_FILE, SLEEP_FILE, TEMP_FILE]
            if run_script("prepararDF.py", ["--inputs"] + input_files + ["--output", CONSOLIDATED_FILE]):
                # Añadir edad
                df = pd.read_csv(CONSOLIDATED_FILE)
                df['age'] = age_input
                
                # Predecir
                st.subheader("Paso 2: Realizando la Predicción")
                predict_on_dataframe(df)
        else:
            st.error("Por favor, carga los cuatro archivos necesarios.")

# --- Pestaña 3: Flujo de 1 archivo completo ---
with tab3:
    st.header("Opción B: Predecir desde un Dataset Completo")
    st.write("Carga un único fichero CSV que ya contenga **todas las columnas, incluida la edad**.")
    
    uploaded_complete = st.file_uploader("Cargar Fichero de Datos Consolidado", type="csv", key="comp_up")

    if st.button("Limpiar y Predecir Dataset", key="btn_tab2"):
        if uploaded_complete:
            # Guardar archivo
            with open(COMPLETE_RAW_FILE, "wb") as f:
                f.write(uploaded_complete.getbuffer())
            st.success("Archivo consolidado cargado.")

            # Limpiar NaNs con limpiar_dataset.py
            st.subheader("Paso 1: Limpiando el Dataset (imputando NaNs)")
            if run_script("limpiar_dataset.py", [COMPLETE_RAW_FILE, COMPLETE_CLEANED_FILE]):
                # Cargar dataframe limpio y predecir
                df_cleaned = pd.read_csv(COMPLETE_CLEANED_FILE)
                st.subheader("Paso 2: Realizando la Predicción")
                predict_on_dataframe(df_cleaned)
        else:
            st.error("Por favor, carga un archivo consolidado.")



