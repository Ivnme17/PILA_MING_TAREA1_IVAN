# Pila MING – Tarea evaluable 1

Pila **M**osquitto + **I**nfluxDB + **N**ode-RED + **G**rafana con Docker Compose para captar el clima de Almería.
Un script en Python consulta la API pública de [Open-Meteo](https://open-meteo.com) cada 5 minutos y envía temperatura, humedad y presión a Node-RED; este las publica en Mosquitto (MQTT), las vuelve a recibir, las valida y las guarda en InfluxDB; Grafana las muestra en un dashboard.

```
Open-Meteo ─► clima_almeria.py ─► Node-RED ─► Mosquitto ─► Node-RED ─► InfluxDB ─► Grafana
  (API)        (cada 5 min,     POST /clima    topic MQTT   valida y      :8086        :3000
                solo requests)                 :1883        guarda
```

## Estructura

```
Tarea1/
├── docker-compose.yml
├── .env                         # puertos y zona horaria
├── .env.influxdb2-admin-*       # secretos de InfluxDB (usuario, contraseña, token)
├── clima_almeria.py             # script de captación (API -> MQTT)
├── requirements.txt             # requests
├── mosquitto/config/            # mosquitto.conf + passwd
├── node-red/data/flows.json     # flujos (incluir también node-red/flujo-clima.json)
├── influxdb2/                   # datos de InfluxDB
└── grafana/data/                # datos de Grafana
```

## Cómo levantar el stack

Requisitos: Docker y Docker Compose v2; Python 3 para el script.

```bash
git clone https://github.com/Ivnme17/PILA_MING_TAREA1_IVAN.git
cd PILA_MING_TAREA1_IVAN/Tarea1
docker compose up -d
docker compose ps          # los 4 contenedores deben estar "running"
docker compose logs -f     # ver logs
docker compose down        # parar (los datos se conservan en las carpetas montadas)
```

1. **Node-RED** (http://localhost:1880): menú ☰ → *Import* → pegar `node-red/flujo-clima.json` → *Import*. Se crea una pestaña nueva «Clima Almería». Abre el nodo **Salida de datos clima**, edita su servidor `influxdb clima` y pega el token de `.env.influxdb2-admin-token` (la URL ya es `http://db:8086`, versión 2.0, org `sdb`, bucket `tarea1`); después *Deploy*. Usa el broker «T1» que ya tienes configurado.
2. **Script** (con Node-RED ya desplegado):

```bash
pip install -r requirements.txt
python3 clima_almeria.py
```

## Script de captación (`clima_almeria.py`)

Solo usa la librería `requests`. Pide a Open-Meteo `temperature_2m`, `relative_humidity_2m` y `surface_pressure` de Almería (latitud 36.8381, longitud −2.4597) y las envía con un `POST` JSON a la entrada HTTP de Node-RED (`http://localhost:1880/clima`). Node-RED las publica en el topic MQTT `sdb/almeria/clima` y las procesa. Se repite cada 300 s (5 minutos), sin ráfagas.

- Si Open-Meteo responde con un código distinto de 200, muestra `Error al conectar con la API: <código>` y lo intenta de nuevo en el siguiente ciclo.
- Si Node-RED no responde 200, muestra `Error al enviar a Node-RED: <código>`.
- Si no hay conexión, muestra el error y sigue funcionando.

Valores configurables al inicio del archivo: `NODERED_URL` y `SEGUNDOS`. El script no guarda ninguna contraseña.

Mensaje enviado (`ts_api` es la hora de la medida en segundos Unix):

```json
{"temperatura": 18.4, "humedad": 63, "presion": 1016.2, "ts_api": 1762804800}
```

## Variables usadas

Fichero `.env`:

| Variable | Valor | Uso |
|---|---|---|
| `MOSQUITTO_PORT` | 1883 | Puerto MQTT publicado |
| `NODERED_PORT` | 1880 | Puerto de Node-RED (*ver nota*) |
| `INFLUXDB_PORT` | 8086 | Puerto de InfluxDB |
| `GRAFANA_PORT` | 3000 | Puerto de Grafana (*ver nota*) |
| `TIMEZONE` | Europe/Madrid | Zona horaria de Node-RED |

InfluxDB (en `docker-compose.yml`): `DOCKER_INFLUXDB_INIT_ORG=sdb`, `DOCKER_INFLUXDB_INIT_BUCKET=tarea1`; usuario, contraseña y token se leen como *Docker secrets* desde los ficheros `.env.influxdb2-admin-*`.

## Endpoints y credenciales

| Servicio | Endpoint | Usuario | Contraseña |
|---|---|---|---|
| Mosquitto | `mqtt://localhost:1883` (sin anónimos) | `admin` | *(la definida en `mosquitto/config/passwd`)* |
| Node-RED | http://localhost:1880 · entrada del script: `POST /clima` | sin autenticación | – |
| InfluxDB | http://localhost:8086 · org `sdb` · bucket `tarea1` | `admin` | *(fichero `.env.influxdb2-admin-password`)* |
| Grafana | http://localhost:3000 | `admin` | `admin` (por defecto; pide cambiarla al entrar) |
| Open-Meteo | https://api.open-meteo.com/v1/forecast | sin clave | – |

Dentro de Docker los servicios se llaman `mosquitto`, `node-red`, `db` (InfluxDB) y `grafana`, en la red `t1-lan`. Topic MQTT: `sdb/almeria/clima`.

Comprobar que llegan mensajes:

```bash
docker exec mosquitto_t1 mosquitto_sub -h localhost -u admin -P <contraseña> -t 'sdb/#' -v
```

## Esquema en InfluxDB

| | |
|---|---|
| measurement | `almeria_clima` |
| tags | `symbol` = `Tª` (temperatura), `H` (humedad), `P` (presión); `source` = `open-meteo` |
| fields | `valor` (float), `ts_api` (hora de la medida, segundos Unix) |

Cada lectura genera 3 puntos (uno por `symbol`). La tendencia de 24 h se calcula en Grafana (opción 4a del enunciado), por lo que no se guarda `cambio_24h`.

## Dashboard de Grafana

| Panel | Tipo | Consulta (Flux, sobre bucket `tarea1`) |
|---|---|---|
| Temperatura, Humedad, Presión actuales | 3 × Gauge | `range(start: -1h)` · `filter(_measurement == "almeria_clima" and _field == "valor" and symbol == "Tª"/"H"/"P")` · `last()` |
| Última hora | Time series (rango fijo `now-1h`, refresco 1 min) | igual, con `range(start: v.timeRangeStart, stop: v.timeRangeStop)`, sin `last()` |
| Tendencia 24 h | Stat con texto ↑/↓ y % | ver `Documentacion_Tarea1.pdf`, apartado 4 |

![Dashboard de Grafana](docs/img/dashboard-grafana.png)
![Flujo en Node-RED](docs/img/flujo-node-red-editor.png)


## Documentación adicional

`Documentacion_Tarea1.pdf` (implementación, flujo Node-RED, esquema Influx y decisiones del dashboard).
