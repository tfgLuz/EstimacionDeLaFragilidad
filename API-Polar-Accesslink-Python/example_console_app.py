#!/usr/bin/env python

from __future__ import print_function

from utils import load_config, save_config, pretty_print_json
from accesslink import AccessLink

#LIBRERÍAS ADICIONALES------------------------------------------------------------------------------------------------------------------
import requests
import csv
from datetime import datetime
import pandas as pd
import os
import re
#---------------------------------------------------------------------------------------------------------------------------------------

try:
    input = raw_input
except NameError:
    pass


CONFIG_FILENAME = "config.yml"


class PolarAccessLinkExample(object):
    """Example application for Polar Open AccessLink v3."""

    def __init__(self):
        self.config = load_config(CONFIG_FILENAME)

        if "access_token" not in self.config:
            print("Authorization is required. Run authorization.py first and complete the authentication process.")
            return

        self.accesslink = AccessLink(client_id=self.config["client_id"],
                                     client_secret=self.config["client_secret"])

        self.running = True
        self.show_menu()

    def show_menu(self):
        while self.running:
            print("\nChoose an option:\n" +
                  "-----------------------\n" +
                  "1) Get user information and export physical info\n" + # Modified menu option text
                  "2) Get available transactional data\n" +          
                  "3) Get available non-transactional data\n" +
                  "4) Revoke access token\n" +
                  "5) Exit\n" +
                  "-----------------------")
            self.get_menu_choice()

    def get_menu_choice(self):
        choice = input("> ")
        {
            "1": self.get_user_information,
            "2": self.check_available_data,
            "3": self.print_data ,
            "4": self.revoke_access_token,           
            "5": self.exit
        }.get(choice, self.get_menu_choice)()

    def print_data(self):
        exercise = self.accesslink.get_exercises(access_token=self.config["access_token"])
        sleep = self.accesslink.get_sleep(access_token=self.config["access_token"])
        recharge = self.accesslink.get_recharge(access_token=self.config["access_token"])


        # FRAGMENTO DE CÓDIGO AÑADIDO PARA EXPORTAR DATOS DEL SUEÑO----------------------------------------------------------------------
        if sleep:
            self.export_sleep_data(sleep)

        if recharge:
            self.export_recharge_data(recharge)   # Nueva función para exportar recharge
        #--------------------------------------------------------------------------------------------------------------------------------

        print("exercises: ", end = '')
        pretty_print_json(exercise)
        pretty_print_json(sleep)
        pretty_print_json(recharge)


    # FRAGMENTO DE CÓDIGO AÑADIDO PARA EXPORTAR DATOS DEL SUEÑO--------------------------------------------------------------------------
    def export_sleep_data(self, sleep_data):   # Añade sleep_data como parámetro
        if not sleep_data or 'nights' not in sleep_data:
            print("No hay datos de sueño disponibles.")
            return
        
        # Exportar datos básicos del sueño
        self.export_sleep_summary(sleep_data)


    def export_sleep_summary(self, sleep_data):
        export_folder = 'archivos_exportados'
        os.makedirs(export_folder, exist_ok=True)
        
        # Nombre de archivo fijo (sin timestamp)
        csv_filename = os.path.join(export_folder, "polar_sleep_summary.csv")
        
        # Leer fechas existentes si el archivo ya existe
        existing_dates = set()
        file_exists = os.path.exists(csv_filename)
        
        if file_exists:
            with open(csv_filename, mode='r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                existing_dates = {row['date'] for row in reader}
        
        # Preparar datos nuevos para añadir
        new_rows = []
        for night in sleep_data['nights']:
            night_date = night.get('date', '')
            if not night_date or night_date in existing_dates:
                continue
                
            new_rows.append({
                'date': night_date,
                'start_time': night.get('sleep_start_time', '').split('T')[1][:8] if night.get('sleep_start_time') else '',
                'end_time': night.get('sleep_end_time', '').split('T')[1][:8] if night.get('sleep_end_time') else '',
                'light_sleep_min': round(night.get('light_sleep', 0)/60, 1),
                'deep_sleep_min': round(night.get('deep_sleep', 0)/60, 1),
                'rem_sleep_min': round(night.get('rem_sleep', 0)/60, 1),
                'sleep_score': night.get('sleep_score', ''),
                'interruptions_min': round(night.get('total_interruption_duration', 0)/60, 1)
            })
            existing_dates.add(night_date)   # Para evitar duplicados en esta ejecución
        
        # Escribir al archivo (añadir si ya existe)
        if new_rows:
            mode = 'a' if file_exists else 'w'
            with open(csv_filename, mode=mode, newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=[
                    'date', 'start_time', 'end_time', 
                    'light_sleep_min', 'deep_sleep_min', 'rem_sleep_min',
                    'sleep_score', 'interruptions_min'
                ])
                
                if mode == 'w':   # Solo escribir encabezado si es nuevo archivo
                    writer.writeheader()
                    
                writer.writerows(new_rows)
            
            print(f"\n✓ Añadidos {len(new_rows)} nuevos registros a {csv_filename}")
        else:
            print("\nℹ No se encontraron nuevos datos para añadir al resumen de sueño")
        
    def export_recharge_data(self, recharge_data):
        """Exporta todos los datos de recharge siguiendo el mismo patrón que sleep"""
        if not recharge_data or 'recharges' not in recharge_data:
            print("No hay datos de recharge disponibles.")
            return
        
        # Exportar datos básicos del recharge
        self.export_recharge_summary(recharge_data)

    def export_recharge_summary(self, recharge_data):
        """Exporta el resumen de datos de recharge"""
        export_folder = 'archivos_exportados'
        os.makedirs(export_folder, exist_ok=True)
        
        csv_filename = os.path.join(export_folder, "polar_recharge_summary.csv")
        
        # Leer fechas existentes si el archivo ya existe
        existing_dates = set()
        file_exists = os.path.exists(csv_filename)
        
        if file_exists:
            with open(csv_filename, mode='r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                existing_dates = {row['date'] for row in reader}
        
        # Preparar datos nuevos para añadir
        new_rows = []
        for day in recharge_data['recharges']:
            day_date = day.get('date', '')
            if not day_date or day_date in existing_dates:
                continue
                
            new_rows.append({
                'date': day_date,
                'polar_user': str(day.get('polar_user', '')).split('/')[-1],
                'heart_rate_avg': day.get('heart_rate_avg', ''),
                'heart_rate_variability_avg': day.get('heart_rate_variability_avg', ''),
                'nightly_recharge_status': day.get('nightly_recharge_status', ''),
                'ans_charge': day.get('ans_charge', ''),
                'ans_charge_status': day.get('ans_charge_status', ''),
                'beat_to_beat_avg': day.get('beat_to_beat_avg', ''),
                'breathing_rate_avg': day.get('breathing_rate_avg', '')
            })
            existing_dates.add(day_date)
        
        # Escribir al archivo (añadir si ya existe)
        if new_rows:
            mode = 'a' if file_exists else 'w'
            with open(csv_filename, mode=mode, newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=[
                    'date', 'polar_user', 'heart_rate_avg', 'heart_rate_variability_avg',
                    'nightly_recharge_status', 'ans_charge', 'ans_charge_status',
                    'beat_to_beat_avg', 'breathing_rate_avg'
                ])
                
                if mode == 'w':
                    writer.writeheader()
                    
                writer.writerows(new_rows)
            
            print(f"\n✓ Añadidos {len(new_rows)} nuevos registros a {csv_filename}")
        else:
            print("\nℹ No se encontraron nuevos datos para añadir al resumen de recharge")
    #------------------------------------------------------------------------------------------------------------------------------------

    def get_user_information(self):
        user_info = self.accesslink.users.get_information(user_id=self.config["user_id"],
                                                          access_token=self.config["access_token"])
        print("User information:")
        pretty_print_json(user_info)
        
        # Call get_physical_info to export the physical data
        self.get_physical_info()

    def check_available_data(self):
        available_data = self.accesslink.pull_notifications.list()

        if not available_data:
            print("No new data available.")
            return

        print("Available data:")
        pretty_print_json(available_data)
        for item in available_data["available-user-data"]:
            if item["data-type"] == "EXERCISE":
                self.get_exercises()
            elif item["data-type"] == "ACTIVITY_SUMMARY":
                self.get_daily_activity()
            elif item["data-type"] == "PHYSICAL_INFORMATION":
                self.get_physical_info()

    def revoke_access_token(self):
        self.accesslink.users.delete(user_id=self.config["user_id"],
                                     access_token=self.config["access_token"])

        del self.config["access_token"]
        del self.config["user_id"]
        save_config(self.config, CONFIG_FILENAME)

        print("Access token was successfully revoked.")

        self.exit()

    def exit(self):
        self.running = False

    def get_exercises(self):
        transaction = self.accesslink.training_data.create_transaction(user_id=self.config["user_id"],
                                                                        access_token=self.config["access_token"])
        if not transaction:
            print("No new exercises available.")
            return

        resource_urls = transaction.list_exercises()["exercises"]

        for url in resource_urls:
            exercise_summary = transaction.get_exercise_summary(url)

            print("Exercise summary:")
            pretty_print_json(exercise_summary)

        transaction.commit()

     # FUNCIÓN NUEVA PARA CONVERTIR LA FECHA--------------------------------------------------------------------------------------------------
    def parse_iso_duration_to_minutes(self, duration_str):
        """
        Convierte una duración en formato ISO 8601 (ej. "PT8H11M") a minutos totales.
        """
        if not isinstance(duration_str, str) or not duration_str.startswith('PT'):
            return 0.0

        hours_match = re.search(r'(\d+)H', duration_str)
        minutes_match = re.search(r'(\d+)M', duration_str)
        
        hours = int(hours_match.group(1)) if hours_match else 0
        minutes = int(minutes_match.group(1)) if minutes_match else 0
        
        total_minutes = (hours * 60) + minutes
        return total_minutes
    #---------------------------------------------------------------------------------------------------------------------------------------


    # FUNCIÓN MODIFICADA PARA EXPORTAR LA ACTIVIDAD FÍSICA DIARIA CON EL VALOR MÁXIMO
    def get_daily_activity(self):
        try:
            transaction = self.accesslink.daily_activity.create_transaction(
                user_id=self.config["user_id"],
                access_token=self.config["access_token"])
        except requests.exceptions.HTTPError as e:
            print(f"Error al crear transacción: {e}")
            return
        
        if not transaction:
            print("No new daily activity available.")
            return
        
        resource_urls = transaction.list_activities().get("activity-log", [])
        if not resource_urls:
            print("No activity log URLs found in the transaction.")
            transaction.commit()
            return

        # --- PASO 1: Agrupar datos de la API por día y quedarse con el máximo 'active-steps' ---
        api_daily_max = {}
        print("Fetching data from Polar API...")
        for url in resource_urls:
            summary = transaction.get_activity_summary(url)
            date = summary.get('date')
            if not date:
                continue
            
            current_steps = summary.get('active-steps', 0) or 0
            
            # Si la fecha no está registrada o los pasos del registro actual son mayores, se guarda.
            if date not in api_daily_max or current_steps > api_daily_max[date].get('active-steps', 0):
                api_daily_max[date] = summary

        # --- PASO 2: Leer los datos existentes del CSV ---
        export_folder = 'archivos_exportados'
        os.makedirs(export_folder, exist_ok=True)
        csv_filename = os.path.join(export_folder, "polar_daily_activities.csv")
        
        fieldnames = [
            'id', 'date', 'active-steps', 'active-calories', 'calories',
            'duration_minutes', 'steps_per_minute', 'calories_per_step',
            'active_calories_per_minute'
        ]
        
        existing_data = {}
        if os.path.exists(csv_filename):
            try:
                with open(csv_filename, mode='r', newline='', encoding='utf-8') as csv_file:
                    reader = csv.DictReader(csv_file)
                    for row in reader:
                        # Se convierte 'active-steps' a entero para una comparación numérica correcta
                        row['active-steps'] = int(row.get('active-steps', 0))
                        existing_data[row['date']] = row
            except (IOError, KeyError) as e:
                print(f"Aviso: No se pudo leer el archivo CSV existente. Se creará de nuevo. Error: {e}")

        # --- PASO 3: Comparar y decidir qué datos actualizar o añadir ---
        updates_found = 0
        additions_found = 0

        for date, summary in api_daily_max.items():
            new_steps = summary.get('active-steps', 0) or 0
            
            # Comprobar si la fecha ya existe o si los nuevos pasos son mayores
            if date not in existing_data or new_steps > existing_data[date]['active-steps']:
                # Procesar y calcular las métricas solo para los datos que se van a añadir/actualizar
                duration_minutes = self.parse_iso_duration_to_minutes(summary.get('duration', 'PT0M'))
                steps_per_minute = (new_steps / duration_minutes) if duration_minutes > 0 else 0
                total_calories = summary.get('calories', 0) or 0
                active_calories = summary.get('active-calories', 0) or 0
                calories_per_step = (total_calories / new_steps) if new_steps > 0 else 0
                active_calories_per_minute = (active_calories / duration_minutes) if duration_minutes > 0 else 0
                
                # Crear la nueva fila
                processed_row = {
                    'id': summary.get('id'),
                    'date': date,
                    'active-steps': new_steps,
                    'active-calories': active_calories,
                    'calories': total_calories,
                    'duration_minutes': round(duration_minutes, 2),
                    'steps_per_minute': round(steps_per_minute, 2),
                    'calories_per_step': round(calories_per_step, 4),
                    'active_calories_per_minute': round(active_calories_per_minute, 2)
                }
                
                if date in existing_data:
                    updates_found += 1
                else:
                    additions_found += 1

                # Añadir/actualizar el registro en nuestro diccionario de datos
                existing_data[date] = processed_row
                
        # --- PASO 4: Reescribir el archivo CSV con todos los datos actualizados ---
        if updates_found > 0 or additions_found > 0:
            # Ordenar los datos por fecha antes de escribirlos
            sorted_data = sorted(existing_data.values(), key=lambda x: x['date'])
            
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(sorted_data)
            
            print(f"\n✓ Proceso completado. Resumen:")
            print(f"  - {additions_found} días nuevos añadidos.")
            print(f"  - {updates_found} días existentes actualizados con valores más altos.")
            print(f"  - Archivo guardado en: {csv_filename}")
        else:
            print("\nℹ No se encontraron actividades nuevas o con valores superiores para exportar.")

        transaction.commit()

    #------------------------------------------------------------------------------------------------------------------------------------

    #FUNCIÓN MODIFICADA PARA EXPORTAR LA INFORMACIÓN FÍSICA DEL USUARIO QUE PORTA EL SMARTWATCH -----------------------------------------
    def get_physical_info(self):
        transaction = self.accesslink.physical_info.create_transaction(user_id=self.config["user_id"],
                                                                        access_token=self.config["access_token"])
        if not transaction:
            print("No new physical information available.")
            return

        transaction.commit()
    #-----------------------------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    PolarAccessLinkExample()