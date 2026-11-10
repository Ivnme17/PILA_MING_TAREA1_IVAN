# Lee el clima de Almería (API Open-Meteo) y lo envía por MQTT a Mosquitto.

import json
import time

import requests
import paho.mqtt.client as mqtt

'''---------- CONFIGURACIÓN (cambia solo esto) ----------'''
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_USER = "admin"
MQTT_PASSWORD = "admin"
TOPIC = "sdb/almeria/clima"
SEGUNDOS_ENTRE_LECTURAS = 900  # Open-Meteo actualiza cada 15 min(900 segundos)

''' Dirección de la API: coordenadas de Almería y los datos que queremos'''
URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=36.8381&longitude=-2.4597"
    "&current=temperature_2m,apparent_temperature,relative_humidity_2m,"
    "precipitation,surface_pressure,wind_speed_10m,wind_direction_10m,weather_code"
    "&timezone=Europe/Madrid"
)


def leer_clima():
    """Pide los datos a Open-Meteo y devuelve un diccionario con nombres claros."""
    respuesta = requests.get(URL, timeout=15)
    actual = respuesta.json()["current"]
    return {
        "ciudad": "almeria",
        "temperatura_c": actual["temperature_2m"],
        "sensacion_c": actual["apparent_temperature"],
        "humedad_pct": actual["relative_humidity_2m"],
        "precipitacion_mm": actual["precipitation"],
        "presion_hpa": actual["surface_pressure"],
        "viento_kmh": actual["wind_speed_10m"],
        "direccion_viento_deg": actual["wind_direction_10m"],
        "codigo_tiempo": actual["weather_code"],
    }


''' ---------- PROGRAMA PRINCIPAL ----------'''
cliente = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
cliente.username_pw_set(MQTT_USER, MQTT_PASSWORD)
cliente.connect(MQTT_HOST, MQTT_PORT)
cliente.loop_start()
print("Conectado a Mosquitto. Pulsa Ctrl+C para parar.")


while True:
    try:
        datos = leer_clima()
        cliente.publish(TOPIC, json.dumps(datos))
        print("Enviado:", datos)
    except Exception as error:
        print("No se pudo leer el clima:", error)
    time.sleep(SEGUNDOS_ENTRE_LECTURAS)