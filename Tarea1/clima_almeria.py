import requests

url = "https://api.open-meteo.com/v1/forecast"
parametros = {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "current": "temperature_2m,wind_speed_10m",
    "hourly": "temperature_2m",
}

respuesta = requests.get(url, params=parametros)

if respuesta.status_code == 200:
    data = respuesta.json()

    temp_actual = data["current"]["temperature_2m"]
    viento_actual = data["current"]["wind_speed_10m"]

    print(f"Temperatura actual: {temp_actual} °C")
    print(f"Velocidad del viento: {viento_actual} km/h")
else:
    print("Error al conectar con la API:", respuesta.status_code)
