import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configuración
np.random.seed(42)
n_subjects = 25
n_days = 30
start_date = datetime(2025, 6, 1)

# Función de clasificación
def classify_row(row):
    score = 0
    if row['active-steps'] > 6000:
        score += 2
    elif row['active-steps'] > 2500:
        score += 1

    if row['heart_rate_variability_avg'] > 35:
        score += 2
    elif row['heart_rate_variability_avg'] > 25:
        score += 1

    if row['heart_rate_avg'] < 65:
        score += 2
    elif row['heart_rate_avg'] < 72:
        score += 1

    if row['sleep_score'] > 75:
        score += 2
    elif row['sleep_score'] > 60:
        score += 1

    if score >= 6:
        return 'robusto'
    elif score >= 3:
        return 'pre-fragil'
    else:
        return 'fragil'

# Generar datos sintéticos
data = []

for subject_id in range(1, n_subjects + 1):
    age = np.random.randint(65, 81)
    for i in range(n_days):
        date = start_date + timedelta(days=i)
        steps = np.random.randint(500, 13000)
        active_calories = steps * np.random.uniform(0.03, 0.05)
        total_calories = active_calories + np.random.uniform(1400, 2200)
        duration_minutes = np.random.uniform(30, 120)
        hr_avg = np.random.uniform(55, 85)
        hrv_avg = np.random.uniform(15, 65)
        sleep_score = np.random.uniform(45, 90)
        light_sleep = np.random.randint(100, 300)
        deep_sleep = np.random.randint(30, 120)
        rem_sleep = np.random.randint(40, 160)
        interruptions = np.random.randint(0, 30)
        ans_charge = np.random.uniform(20, 100)
        breathing_rate = np.random.uniform(12, 20)
        temp_amplitude = np.random.uniform(0.3, 1.0)

        row = {
            'id_usuario': subject_id,
            'age': age,
            'fecha_comun': date.strftime('%Y-%m-%d'),
            'active-steps': steps,
            'active-calories': round(active_calories, 1),
            'calories': round(total_calories, 1),
            'duration_minutes': round(duration_minutes),
            'heart_rate_avg': round(hr_avg, 1),
            'heart_rate_variability_avg': round(hrv_avg, 1),
            'ans_charge': round(ans_charge, 1),
            'sleep_score': round(sleep_score, 1),
            'light_sleep_min': light_sleep,
            'deep_sleep_min': deep_sleep,
            'rem_sleep_min': rem_sleep,
            'interruptions_min': interruptions,
            'breathing_rate_avg': round(breathing_rate, 1),
            'temp_amplitude': round(temp_amplitude, 2)
        }

        row['frailty_status'] = classify_row(row)
        data.append(row)

# Crear y guardar DataFrame
df = pd.DataFrame(data)
df.to_csv('datasetIAml.csv', index=False)
print("Archivo CSV generado: datasetIAml.csv")
