import pandas as pd
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier
import joblib
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

print("Iniciando el entrenamiento del pipeline final...")

# --- 1. Cargar el Dataset ---
try:
    df = pd.read_csv('dataset_preparado.csv')
    print("Archivo 'dataset_preparado.csv' cargado.")
except FileNotFoundError:
    print("Error: No se encontro el archivo 'dataset_preparado.csv'.")
    exit()

# --- 2. Definir Columnas y Objetivo ---
# Estas son las columnas que el modelo usará para predecir.
# Es importante que coincidan con las que usaste en el entrenamiento.
numeric_features = [
    'age', 'active-steps', 'active-calories', 'calories', 'duration_minutes',
    'heart_rate_avg', 'heart_rate_variability_avg', 'ans_charge', 'sleep_score',
    'light_sleep_min', 'deep_sleep_min', 'rem_sleep_min', 'interruptions_min',
    'breathing_rate_avg', 'temp_amplitude'
]

X_full = df[numeric_features]
y_full = df['frailty_status']

# --- 3. Balancear los Datos con SMOTE ---
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_full, y_full)
print(f"Datos balanceados con SMOTE, total de filas: {X_resampled.shape[0]}")

# --- 4. Crear el Pipeline ---
# El preprocesador se asegura de que solo se usen las columnas numéricas.
preprocessor = ColumnTransformer(
    transformers=[
        ('num', 'passthrough', numeric_features)
    ])

# El modelo XGBoost con los mejores parámetros
model = XGBClassifier(objective='multi:softmax', num_class=3, use_label_encoder=False, eval_metric='mlogloss', random_state=42)

# Unimos el preprocesador y el modelo en un único Pipeline
final_pipeline = Pipeline(steps=[('preprocessor', preprocessor),
                                 ('classifier', model)])

# --- 5. Entrenar el Pipeline Completo ---
final_pipeline.fit(X_resampled, y_resampled)
print("Pipeline final (preprocesador + modelo) entrenado.")

# --- 6. Guardar el Pipeline ---
pipeline_filename = 'fragility_pipeline.joblib'
joblib.dump(final_pipeline, pipeline_filename)

print(f"\n¡Listo! Pipeline guardado exitosamente como '{pipeline_filename}'")