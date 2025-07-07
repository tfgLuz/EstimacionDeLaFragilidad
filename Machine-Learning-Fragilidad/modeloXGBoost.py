import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
from imblearn.over_sampling import SMOTE
# Importar el nuevo clasificador
from xgboost import XGBClassifier

# --- 1. Cargar el Dataset Preparado ---
try:
    df = pd.read_csv('dataset_preparado.csv')
    print("Archivo 'dataset_preparado.csv' cargado correctamente.")
except FileNotFoundError:
    print("Error: No se encontro el archivo 'dataset_preparado.csv'.")
    exit()

# --- 2. Separar Características (X) y Objetivo (y) ---
X = df.drop(columns=['frailty_status', 'id_usuario', 'fecha_comun'])
y = df['frailty_status']

# --- 3. División de Datos por Usuario (Train/Test) ---
user_ids = df['id_usuario'].unique()
train_user_ids, test_user_ids = train_test_split(user_ids, test_size=0.25, random_state=42)

train_indices = df[df['id_usuario'].isin(train_user_ids)].index
test_indices = df[df['id_usuario'].isin(test_user_ids)].index

X_train, X_test = X.loc[train_indices], X.loc[test_indices]
y_train, y_test = y.loc[train_indices], y.loc[test_indices]

# --- 4. Aplicar SMOTE (Solo a los datos de entrenamiento) ---
smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
print(f"Set de entrenamiento balanceado con SMOTE: {X_train_resampled.shape[0]} filas")

# --- 5. Entrenar el Modelo con XGBoost ---
# Se inicializa el clasificador XGBoost
# 'use_label_encoder=False' y 'eval_metric='mlogloss'' para evitar warnings comunes
model = XGBClassifier(objective='multi:softmax', num_class=3, use_label_encoder=False, eval_metric='mlogloss', random_state=42)

# Se entrena el modelo con los datos balanceados
model.fit(X_train_resampled, y_train_resampled)
print("Modelo XGBoost entrenado.")

# --- 6. Evaluar el Modelo ---
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)
print(f"\nPrecisión (Accuracy) del modelo: {accuracy:.2%}")

print("\nReporte de Clasificación:")
target_names = ['frágil (0)', 'pre-frágil (1)', 'robusto (2)']
print(classification_report(y_test, y_pred, target_names=target_names))

# --- 7. Visualizar la Matriz de Confusión ---
print("\nLa matriz de confusión muestra los aciertos (diagonal) y errores.")
cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2])

plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=target_names, yticklabels=target_names)
plt.title('Matriz de Confusión - XGBoost')
plt.ylabel('Valor Real')
plt.xlabel('Predicción del Modelo')
plt.show()


# --- 8. Analizar Importancia de Características ---
# (Añadir esto al final del script anterior)

print("\nImportancia de las características según el modelo XGBoost:")
feature_importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)

# Imprimir las 10 más importantes
print(feature_importances.head(10))

# Crear un gráfico de barras para visualizar
plt.figure(figsize=(10, 8))
sns.barplot(x=feature_importances, y=feature_importances.index, palette='viridis')
plt.title('Importancia de las Características - XGBoost')
plt.xlabel('Importancia')
plt.ylabel('Características')
plt.show()