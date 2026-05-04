# ==============================================================================
# Módulo: server.py
#
# Descripción:
# Este script implementa un servidor web de tipo API utilizando el framework Flask.
# El servidor gestiona varias rutas (`endpoints`) para interactuar con un sistema
# de gestión de inventario, un dron, un sistema JD Edwards, y una base de datos.
# Las funciones principales incluyen la recepción de datos de inventario, la
# orquestación del proceso de actualización de inventario, la carga de archivos,
# y la verificación de la conectividad.
#
# El código utiliza:
# - `Flask` para definir las rutas de la API.
# - `dotenv` para cargar variables de entorno (como rutas de carpetas y credenciales).
# - `jsonschema` para validar las estructuras de datos JSON entrantes.
# - Módulos de servicio locales (`JDService`, `DronService`, etc.) para encapsular
#   la lógica de negocio y la interacción con sistemas externos.
# ==============================================================================

# ------------------------------------------------------------------------------
# Importaciones de Módulos
# ------------------------------------------------------------------------------
import time
from dotenv import load_dotenv
from flask import Flask, jsonify, request, redirect
from flasgger import Flasgger
import jsonschema
import pandas as pd
from Services import JDService, LogService as SaveExecutions
from Services import DronService
from Services import MsSQL_Service as dbService
from Services import Video_Service 
import os
import datetime
import logging
import json
import atexit
import signal
import sys
import traceback
from logging.handlers import RotatingFileHandler
from flask import Flask, request as flask_request
from Services.tracking import track_visit

# Cargar variables de entorno desde un archivo .env.
# La opción `override=True` permite sobrescribir variables de entorno existentes.
load_dotenv(override=True)

# Obtener configuración de la API desde variables de entorno
API_HOST = os.getenv('API_HOST', '10.185.36.30')  # IP del servidor
API_PORT = os.getenv('API_PORT', '5100')  # Puerto del servidor

# Crear una instancia de la aplicación Flask.
app = Flask(__name__)

# Inicializar Flasgger para documentación Swagger
swagger = Flasgger(app, template={
    "swagger": "2.0",
    "info": {
        "title": "Sierra Dron API",
        "description": "API para gestión de inventario de drones y sincronización con JD Edwards",
        "contact": {
            "email": "support@sierra.com",
        },
        "version": "1.0.0"
    },
    "host": f"{API_HOST}:{API_PORT}",
    "basePath": "/",
    "schemes": ["http", "https"]
})

# Configuración del logger con RotatingFileHandler
# Crear directorio de logs si no existe
logs_dir = 'logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Configurar el archivo de log
log_file_path = os.path.join(logs_dir, 'api.log')

# Configurar logger con RotatingFileHandler
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Limpiar handlers existentes
logger.handlers = []

# RotatingFileHandler: máximo 5MB (5242880 bytes), mantiene 5 archivos de respaldo
rotating_handler = RotatingFileHandler(
    log_file_path,
    maxBytes=5242880,  # 5 MB
    backupCount=5,      # Mantiene 5 archivos de respaldo (api.log.1, api.log.2, etc.)
    encoding='utf-8'
)

# Formato del log
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
rotating_handler.setFormatter(formatter)

# Agregador a la consola también
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(rotating_handler)
logger.addHandler(console_handler)

# Log al iniciar el servidor
logging.info("=" * 80)
logging.info("Servidor Flask iniciado.")
logging.info("Logs guardados en: " + os.path.abspath(log_file_path))
logging.info("=" * 80)

# ===============================================================================
# MANEJADOR GLOBAL DE EXCEPCIONES Y SEÑALES
# ===============================================================================
def log_exit_event(signal_num=None, frame=None):
    """Registra cuándo el servidor está siendo terminado"""
    if signal_num:
        logging.warning(f"SIGNAL RECEIVED: {signal_num} - Ignoring this signal, server continues running")
        # NO hacer nada - ignorar la señal para que Streamlit no pueda matar el servidor
    else:
        logging.error("Server is exiting (atexit called)")

def excepthook(exc_type, exc_value, exc_traceback):
    """Manejador global de excepciones no capturadas"""
    if issubclass(exc_type, KeyboardInterrupt):
        logging.info("KeyboardInterrupt received - ignoring to keep server alive")
        # NO salir - ignorar Ctrl+C para que Streamlit no pueda matar el servidor
    else:
        logging.critical(
            f"UNCAUGHT EXCEPTION! Type: {exc_type.__name__}\n"
            f"Message: {str(exc_value)}\n"
            f"Traceback:\n{''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))}"
        )

# Registrar manejadores
sys.excepthook = excepthook
atexit.register(log_exit_event)

# Capturar y IGNORAR señales de terminación (prevent interruption from Streamlit)
try:
    # Ignorar SIGTERM y SIGINT completamente
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
except Exception as e:
    logging.warning(f"Could not register signal handlers: {str(e)}")

# Log al iniciar el servidor
logging.info("=" * 80)

# Log para cada request
@app.before_request
def log_request_info():
    logging.info(f"Ruta accedida: {request.path} | Método: {request.method} | IP: {request.remote_addr}")
    track_visit(
        pagina="API: " + request.path,
        url=request.url,
        ip_cliente=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )

@app.after_request
def log_response_info(response):
    status = "Success" if response.status_code < 400 else "Error"
    logging.info(f"Ruta accedida: {request.path} | Status: {response.status_code} ({status})")
    return response

# Ruta de redirección para /docs → /apidocs
@app.route('/docs')
def docs_redirect():
    """Redirecciona a /apidocs"""
    return redirect('/apidocs', code=302)

# Ruta de redirección para /docs/ → /apidocs
@app.route('/docs/')
def docs_slash_redirect():
    """Redirecciona a /apidocs"""
    return redirect('/apidocs', code=302)

# ------------------------------------------------------------------------------
# Funciones Auxiliares
# ------------------------------------------------------------------------------
def utc_time():
    """
    Genera una cadena de tiempo en formato 'YYYY-MM-DD_HH_MM_SS'.

    Esta función se utiliza para crear nombres de archivo únicos y con marca de tiempo.
    
    Returns:
        str: La marca de tiempo formateada.
    """
    return datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')

# ------------------------------------------------------------------------------
# Definición de Rutas (Endpoints) de la API
# ------------------------------------------------------------------------------

@app.route('/test')
def hello_world():
    """
    Endpoint de prueba para verificar que la API está funcionando.
    ---
    tags:
      - Testing
    responses:
      200:
        description: Prueba exitosa
        schema:
          type: object
          properties:
            message:
              type: string
              example: "¡Prueba de Api Exitosa!"
    """
    start_time = time.time()
    end_time = time.time()
    SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "test", 200)
    return '¡Prueba de Api Exitosa!'

@app.route('/inventarios-pendientes', methods=['GET'])
def obtener_datos_inventarios_pendientes():
    """
    Endpoint para obtener lista de inventarios pendientes con predicción de zona.
    
    ESTRATEGIA OPTIMIZADA:
    1. Obtener IDs desde BD (muy rápido)
    2. Cargar caché con predicciones previas
    3. Comparar: detectar nuevos
    4. Predecir solo los nuevos (no recalcular los existentes)
    5. Combinar caché + nuevas predicciones
    
    Retorna todos los inventarios con estado 'Pendiente' junto con:
    - Datos básicos (ID, Fecha, Elementos, Tiempo de vuelo)
    - Predicción de zona automática (PF1, PF2, PF5, PT, o null)
    - Confianza de la predicción
    - Desglose de zonas detectadas
    
    ---
    tags:
      - Inventario - Listado
    responses:
      200:
        description: Lista de inventarios pendientes con predicciones
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            count:
              type: integer
              description: Total de inventarios pendientes
              example: 5
            inventarios:
              type: array
              items:
                type: object
                properties:
                  ID:
                    type: integer
                    example: 46
                  Fecha_Vuelo:
                    type: string
                    format: date-time
                    example: "2026-01-31"
                  N_Elementos:
                    type: integer
                    example: 300
                  Tiempo_Vuelo:
                    type: integer
                    description: Segundos
                    example: 1200
                  predicted_zone:
                    type: string
                    description: "Zona predicha (PF1, PF2, PF5, PT, o null)"
                    example: "PF2"
                  zone_confidence:
                    type: number
                    description: Porcentaje de confianza (0-100)
                    example: 83.5
                  zone_breakdown:
                    type: object
                    description: Desglose de porcentajes por zona
                    example: {"PF1": 5.0, "PF2": 83.5, "PF5": 11.5}
      500:
        description: Error al obtener datos
    """
    try:
        start_time = time.time()
        
        # ===== PASO 1: OBTENER IDS DE BD (RÁPIDO) =====
        time_p1_start = time.time()
        conn = dbService.get_db_connection()
        sql_query = '''
            SELECT ID, Fecha_Vuelo, N_Elementos, Tiempo_Vuelo 
            FROM Inventario_Vuelos
            WHERE Estado_Inventario = 'Pendiente' AND N_Elementos > 0 
            ORDER BY ID DESC
        '''
        df_pendientes = dbService.execute_sql_query(sql_query, conn, params=None)
        dbService.close_connection(conn)
        time_p1_end = time.time()
        
        # Si no hay inventarios pendientes
        if df_pendientes is None or len(df_pendientes) == 0:
            logging.info("GET /inventarios-pendientes: No pending inventories found")
            return jsonify({
                'success': True,
                'count': 0,
                'inventarios': []
            }), 200
        
        bd_ids = set(df_pendientes['ID'].astype(int).tolist())
        
        # ===== PASO 2: CARGAR CACHÉ CON PREDICCIONES PREVIAS =====
        time_p2_start = time.time()
        cache_file = os.path.join('cache', 'inventarios_pendientes_cache.json')
        cache_predicciones = {}  # {id: prediction_data}
        cache_exists = False
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Mapear predicciones en caché por ID para búsqueda rápida
                for inv in cache_data.get('inventarios', []):
                    cache_predicciones[inv['ID']] = {
                        'predicted_zone': inv.get('predicted_zone'),
                        'zone_confidence': inv.get('zone_confidence'),
                        'zone_breakdown': inv.get('zone_breakdown', {})
                    }
                cache_exists = True
                logging.info(f"GET /inventarios-pendientes: Loaded {len(cache_predicciones)} cached predictions")
            except Exception as e:
                logging.warning(f"GET /inventarios-pendientes: Error loading cache - {str(e)}")
        time_p2_end = time.time()
        
        # ===== PASO 3: DETECTAR NUEVOS INVENTARIOS =====
        time_p3_start = time.time()
        cache_ids = set(cache_predicciones.keys())
        nuevos_ids = bd_ids - cache_ids
        desaparecidos_ids = cache_ids - bd_ids
        time_p3_end = time.time()
        
        logging.info(f"GET /inventarios-pendientes: BD={len(bd_ids)} IDs, Caché={len(cache_ids)} IDs, Nuevos={len(nuevos_ids)}, Desaparecidos={len(desaparecidos_ids)}")
        
        # ===== PASO 4: PREDECIR SOLO LOS NUEVOS =====
        time_p4_start = time.time()
        nuevas_predicciones = {}
        
        if nuevos_ids:
            logging.info(f"GET /inventarios-pendientes: Calculating predictions for {len(nuevos_ids)} new IDs: {nuevos_ids}")
            for id_inventario in nuevos_ids:
                try:
                    # Predecir zona para este nuevo inventario
                    prediction = dbService.predict_inventory_zone(id_inventario)
                    logging.debug(f"GET /inventarios-pendientes: ID {id_inventario} - Prediction: {prediction.get('zone')} (confidence: {prediction.get('confidence')})")
                    nuevas_predicciones[id_inventario] = {
                        'predicted_zone': prediction.get('zone'),
                        'zone_confidence': prediction.get('confidence'),
                        'zone_breakdown': prediction.get('breakdown', {})
                    }
                except Exception as e:
                    logging.error(f"GET /inventarios-pendientes: Error predicting zone for ID {id_inventario} - {str(e)}", exc_info=True)
                    nuevas_predicciones[id_inventario] = {
                        'predicted_zone': None,
                        'zone_confidence': 0,
                        'zone_breakdown': {}
                    }
        time_p4_end = time.time()
        
        # ===== PASO 5: COMBINAR CACHÉ + NUEVAS PREDICCIONES =====
        predicciones_finales = {**cache_predicciones, **nuevas_predicciones}
        
        # Construir respuesta con todos los inventarios
        inventarios_con_prediccion = []
        
        for idx, row in df_pendientes.iterrows():
            id_inventario = int(row['ID'])
            
            # Obtener predicción del caché combinado
            prediction = predicciones_finales.get(id_inventario, {
                'predicted_zone': None,
                'zone_confidence': 0,
                'zone_breakdown': {}
            })
            
            inventario_data = {
                'ID': id_inventario,
                'Fecha_Vuelo': str(row['Fecha_Vuelo']),
                'N_Elementos': int(row['N_Elementos']),
                'Tiempo_Vuelo': int(row['Tiempo_Vuelo']),
                'predicted_zone': prediction.get('predicted_zone'),
                'zone_confidence': prediction.get('zone_confidence'),
                'zone_breakdown': prediction.get('zone_breakdown', {})
            }
            
            inventarios_con_prediccion.append(inventario_data)
        
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "obtener_inventarios_pendientes", 200)
        
        # Mostrar desglose de tiempos
        total_time = end_time - start_time
        logging.info(f"""GET /inventarios-pendientes: TIMING BREAKDOWN
        └─ Paso 1 (BD query): {time_p1_end - time_p1_start:.2f}s
        └─ Paso 2 (Load cache): {time_p2_end - time_p2_start:.2f}s
        └─ Paso 3 (Detect new): {time_p3_end - time_p3_start:.2f}s
        └─ Paso 4 (Predict {len(nuevos_ids)} new): {time_p4_end - time_p4_start:.2f}s (avg {(time_p4_end - time_p4_start) / max(1, len(nuevos_ids)):.2f}s per prediction)
        └─ TOTAL REQUEST: {total_time:.2f}s
        ✓ Returned {len(inventarios_con_prediccion)} inventories""")
        
        # ===== PASO 6: ACTUALIZAR CACHÉ CON NUEVAS PREDICCIONES =====
        if nuevas_predicciones:
            try:
                cache_dir = 'cache'
                if not os.path.exists(cache_dir):
                    os.makedirs(cache_dir, exist_ok=True)
                
                cache_data = {
                    'timestamp': datetime.datetime.now().isoformat(),
                    'count': len(inventarios_con_prediccion),
                    'inventarios': inventarios_con_prediccion
                }
                
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
                logging.info(f"GET /inventarios-pendientes: Cache updated with {len(nuevas_predicciones)} new predictions")
            except Exception as cache_err:
                logging.warning(f"GET /inventarios-pendientes: Could not update cache - {str(cache_err)}")
        
        return jsonify({
            'success': True,
            'count': len(inventarios_con_prediccion),
            'inventarios': inventarios_con_prediccion
        }), 200
    
    except Exception as e:
        logging.error(f"GET /inventarios-pendientes: Error - {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'inventarios': []
        }), 500

@app.route('/inventarios-realizados', methods=['GET'])
def obtener_inventarios_realizados():
    """
    Endpoint para obtener los últimos 100 inventarios realizados.
    ---
    tags:
      - Inventario - Listado
    responses:
      200:
        description: Lista de inventarios realizados
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            count:
              type: integer
              example: 100
            inventarios:
              type: array
              items:
                type: object
                properties:
                  ID:
                    type: integer
                    example: 10
                  ID_Vuelo:
                    type: integer
                    example: 5
                  Fecha_Vuelo:
                    type: string
                    format: date-time
                    example: "2026-01-31"
                  Tiempo_Vuelo:
                    type: integer
                    example: 1200
                  Fecha_Inventario:
                    type: string
                    format: date-time
                    example: "2026-01-31T18:22:41"
                  Elementos_OK:
                    type: integer
                    example: 290
                  Elementos_Faltantes:
                    type: integer
                    example: 5
                  Porcentaje_Lectura:
                    type: number
                    example: 96.67
                  NumeroConteo:
                    type: integer
                    example: 1
                  Sucursal:
                    type: string
                    example: "PF2"
                  Ubicacion:
                    type: string
                    example: "Pasillo 3"
                  TransactionId:
                    type: string
                    example: "abc123"
                  Elementos_Sobrantes:
                    type: integer
                    example: 5
                  N_elementos:
                    type: integer
                    example: 300
                  Imagen_Vuelo:
                    type: string
                    example: "imagen.png"
                  Video_Vuelo:
                    type: string
                    example: "video.mp4"
      500:
        description: Error al obtener datos
    """
    try:
        start_time = time.time()

        conn = dbService.get_db_connection()
        sql_query = '''
            SELECT TOP (100) j.ID, j.ID_Vuelo, v.Fecha_Vuelo, v.Tiempo_Vuelo, j.Fecha_Inventario,
                   j.Elementos_OK, j.Elementos_Faltantes,
                   j.Porcentaje_Lectura, j.NumeroConteo, j.Sucursal, j.Ubicacion,
                   j.TransactionId, (v.N_elementos - j.Elementos_OK) AS Elementos_Sobrantes,
                   v.N_elementos, j.Imagen_Vuelo, j.Video_Vuelo
            FROM Inventarios_JDE j
            JOIN Inventario_Vuelos v ON j.ID_Vuelo = v.ID
            ORDER BY j.ID DESC
        '''
        df = dbService.execute_sql_query(sql_query, conn, params=None)
        dbService.close_connection(conn)

        if df is None or len(df) == 0:
            return jsonify({'success': True, 'count': 0, 'inventarios': []}), 200

        inventarios = []
        for _, row in df.iterrows():
            inventarios.append({
                'ID': int(row['ID']),
                'ID_Vuelo': int(row['ID_Vuelo']),
                'Fecha_Vuelo': str(row['Fecha_Vuelo']),
                'Tiempo_Vuelo': int(row['Tiempo_Vuelo']) if row['Tiempo_Vuelo'] is not None else None,
                'Fecha_Inventario': str(row['Fecha_Inventario']),
                'Elementos_OK': int(row['Elementos_OK']) if row['Elementos_OK'] is not None else None,
                'Elementos_Faltantes': int(row['Elementos_Faltantes']) if row['Elementos_Faltantes'] is not None else None,
                'Porcentaje_Lectura': float(row['Porcentaje_Lectura']) if row['Porcentaje_Lectura'] is not None else None,
                'NumeroConteo': int(row['NumeroConteo']) if row['NumeroConteo'] is not None else None,
                'Sucursal': row['Sucursal'],
                'Ubicacion': row['Ubicacion'],
                'TransactionId': row['TransactionId'],
                'Elementos_Sobrantes': int(row['Elementos_Sobrantes']) if row['Elementos_Sobrantes'] is not None else None,
                'N_elementos': int(row['N_elementos']) if row['N_elementos'] is not None else None,
                'Imagen_Vuelo': row['Imagen_Vuelo'],
                'Video_Vuelo': row['Video_Vuelo'],
            })

        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "obtener_inventarios_realizados", 200)
        logging.info(f"GET /inventarios-realizados: Returned {len(inventarios)} records")

        return jsonify({'success': True, 'count': len(inventarios), 'inventarios': inventarios}), 200

    except Exception as e:
        logging.error(f"GET /inventarios-realizados: Error - {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'inventarios': []}), 500

@app.route('/inventario-jde', methods=['GET'])
def obtener_elementos_jde():
    """
    Endpoint para obtener los elementos JDE de un inventario específico.
    ---
    tags:
      - Inventario - Listado
    parameters:
      - in: query
        name: id_inventario
        type: integer
        required: true
        description: ID del inventario
        example: 10
    responses:
      200:
        description: Lista de elementos JDE del inventario
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            count:
              type: integer
              example: 50
            elementos:
              type: array
              items:
                type: object
                properties:
                  EPC:
                    type: string
                    example: "E28011702000"
                  Resultado:
                    type: string
                    example: "OK"
                  Ubicacion:
                    type: string
                    example: "PT"
                  CodigoArticulo:
                    type: string
                    example: "ART001"
      400:
        description: Parámetro id_inventario requerido
      500:
        description: Error al obtener datos
    """
    try:
        start_time = time.time()

        id_inventario = request.args.get('id_inventario')
        if not id_inventario:
            return jsonify({'success': False, 'error': 'El parámetro id_inventario es requerido'}), 400

        conn = dbService.get_db_connection()
        sql_query = '''
            SELECT EPC, Resultado, Ubicacion, CodigoArticulo
            FROM Elementos_JDE
            WHERE ID_Inventario = ?
        '''
        df = dbService.execute_sql_query(sql_query, conn, params=[int(id_inventario)])
        dbService.close_connection(conn)

        if df is None or len(df) == 0:
            return jsonify({'success': True, 'count': 0, 'elementos': []}), 200

        elementos = df.to_dict(orient='records')

        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "obtener_elementos_jde", 200)
        logging.info(f"GET /inventario-jde: id={id_inventario} - Returned {len(elementos)} records")

        return jsonify({'success': True, 'count': len(elementos), 'elementos': elementos}), 200

    except Exception as e:
        logging.error(f"GET /inventario-jde: Error - {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'elementos': []}), 500

@app.route('/dron/actualizar-estado-inventario', methods=['POST'])
def actualizar_estado_inventario():
    """
    Endpoint para actualizar el estado del inventario basado en los datos del dron.
    ---
    tags:
      - Dron - Inventario
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - Inventario
          properties:
            Inventario:
              type: array
              items:
                type: object
                required:
                  - BatchNumber
                  - Sequence
                  - NumeroConteo
                  - Bodega
                  - Ubicacion
                  - NumeroEtiqueta
                  - CodigoArticulo
                  - CoordenadaX
                  - CoordenadaY
                  - TransactionId
                  - TotalBatch
                  - CoordenadaZ
                properties:
                  BatchNumber:
                    type: string
                    example: "BATCH001"
                  Sequence:
                    type: string
                    example: "1"
                  NumeroConteo:
                    type: integer
                    example: 1
                  Bodega:
                    type: string
                    example: "WAREHOUSE_A"
                  Ubicacion:
                    type: string
                    example: "PT"
                  NumeroEtiqueta:
                    type: string
                    example: "TAG001"
                  CodigoArticulo:
                    type: string
                    example: "ART001"
                  CoordenadaX:
                    type: string
                    example: "10.5"
                  CoordenadaY:
                    type: string
                    example: "20.3"
                  TransactionId:
                    type: string
                    example: "TXN001"
                  TotalBatch:
                    type: string
                    example: "100"
                  CoordenadaZ:
                    type: string
                    example: "5.0"
    responses:
      200:
        description: Inventario actualizado exitosamente
        schema:
          type: object
      404:
        description: Esquema de archivo no válido
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Esquema de Archivo no Valido!"
      500:
        description: Error general del servidor
        schema:
          type: object
          properties:
            Error:
              type: string
    """
    # Esquema de validación JSON para los datos del inventario.
    json_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "Inventario": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "BatchNumber": {"type": "string"},
                        "Sequence": {"type": "string"},
                        "NumeroConteo": {"type": "integer"},
                        "Bodega": {"type": "string"},
                        "Ubicacion": {"type": "string"},
                        "NumeroEtiqueta": {"type": "string"},
                        "CodigoArticulo": {"type": "string"},
                        "CoordenadaX": {"type": "string"},
                        "CoordenadaY": {"type": "string"},
                        "TransactionId": {"type": "string"},
                        "TotalBatch": {"type": "string"},
                        "CoordenadaZ": {"type": "string"}
                    },
                    "required": [
                        "BatchNumber", "Sequence", "NumeroConteo", "Bodega", "Ubicacion", 
                        "NumeroEtiqueta", "CodigoArticulo", "CoordenadaX", "CoordenadaY", 
                        "TransactionId", "TotalBatch", "CoordenadaZ"
                    ]
                }
            }
        },
        "required": ["Inventario"]
    }

    start_time = time.time()
    archivo_json = request.get_json()
    logging.info(f"POST /dron/actualizar-estado-inventario: request recibido desde {request.remote_addr}")

    try:
        # Validar el JSON entrante contra el esquema.
        jsonschema.validate(instance=archivo_json, schema=json_schema)

        # Procesar el inventario si la validación es exitosa.
        archivo_json = DronService.actualizar_estado_inventario(archivo_json)

        end_time = time.time()
        logging.info(f"POST /dron/actualizar-estado-inventario: OK ({end_time - start_time:.2f}s)")
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-estado-inventario", 200)
        return jsonify(archivo_json), 200

    except jsonschema.exceptions.ValidationError as e:
        end_time = time.time()
        logging.warning(f"POST /dron/actualizar-estado-inventario: Esquema invalido - {e.message}")
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-estado-inventario", 404)
        return jsonify({'error': 'Esquema de Archivo no Valido!', 'Campos necesarios': json_schema["properties"]["Inventario"]["items"]["required"]}), 404
    except Exception as e:
        end_time = time.time()
        logging.error(f"POST /dron/actualizar-estado-inventario: Error - {str(e)}", exc_info=True)
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-estado-inventario", 500)
        return jsonify({'Error': str(e)}), 500

@app.route('/dron/actualizar-inventario', methods=['POST'])
def actualizar_inventario():
    """
    Endpoint para orquestar el proceso completo de actualización de inventario.
    ---
    tags:
      - Dron - Inventario
    parameters:
      - in: query
        name: Sucursal
        type: string
        default: "SGMINA"
        description: Código de sucursal
      - in: query
        name: Ubicacion
        type: string
        default: "PT"
        description: Código de ubicación
      - in: query
        name: ID
        type: integer
        required: true
        description: ID del inventario de vuelo
      - in: query
        name: Tipo_Inventario
        type: string
        enum: ["Completo", "Parcial"]
        required: true
        description: Tipo de inventario a realizar
    responses:
      200:
        description: Inventario actualizado exitosamente en JD
        schema:
          type: object
          properties:
            OK:
              type: string
              example: "Inventario en JD Actualizado con Éxito"
      404:
        description: Error en la actualización del inventario
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Error general del servidor
        schema:
          type: object
          properties:
            Error General:
              type: string
    """
    start_time = time.time()

    Sucursal = request.args.get('Sucursal', "SGMINA")
    Ubicacion = request.args.get('Ubicacion', "PT")
    ID = request.args.get('ID')
    Tipo_Inventario = request.args.get('Tipo_Inventario')

    logging.info(f"POST /dron/actualizar-inventario: ID={ID}, Sucursal={Sucursal}, Ubicacion={Ubicacion}, Tipo={Tipo_Inventario} | IP={request.remote_addr}")

    if Tipo_Inventario == "Completo":
        Ubicacion = "PT"

    try:
        # Conectar y limpiar la carpeta compartida de JD.
        logging.info(f"POST /dron/actualizar-inventario: Conectando a carpeta JD: {os.getenv('JD_REMOTE_FOLDER')}")
        DronService.connect_to_share_folder(os.getenv('JD_REMOTE_FOLDER'), os.getenv('JD_REMOTE_FOLDER_USERNAME'), os.getenv('JD_REMOTE_FOLDER_PASSWORD'))
        DronService.borrar_archivos_en_carpeta(os.getenv('JD_REMOTE_FOLDER'))

        # Generar el conteo en JD Edwards.
        logging.info(f"POST /dron/actualizar-inventario: Generando conteo JD para Sucursal={Sucursal}, Ubicacion={Ubicacion}")
        if JDService.Generar_Conteo(Sucursal, Ubicacion) is not None:
            logging.info("POST /dron/actualizar-inventario: Conteo JD generado. Esperando archivo (40s)...")
            time.sleep(40)

            if JDService.Archivo_Conteo_Generado_Nuevo(start_time):
                logging.info("POST /dron/actualizar-inventario: Archivo JD detectado. Procesando inventario...")
                inventario_json, NumeroConteo, TransactionId = DronService.actualizar_estado_inventario(ID)

                if inventario_json:
                    logging.info(f"POST /dron/actualizar-inventario: Inventario procesado. NumeroConteo={NumeroConteo}, TransactionId={TransactionId}")
                    DronService.Guardar_json_como_csv(inventario_json, os.getenv('DRON_FOLDER_RESULTS'), Ubicacion)

                    logging.info("POST /dron/actualizar-inventario: Enviando datos de conteo a JD...")
                    if JDService.Retorno_Datos_Conteo(inventario_json):
                        JDService.Generar_Reporte_Conteo(NumeroConteo)
                        logging.info(f"POST /dron/actualizar-inventario: Reporte JD generado para NumeroConteo={NumeroConteo}")

                        end_time = time.time()
                        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 200)

                        if ID:
                            dbService.Actuaizar_Estado_inventario_vuelos(int(ID))
                            resumen = dbService.Resumen_de_Conteo_desde_Json(inventario_json)
                            logging.info(f"POST /dron/actualizar-inventario: Resumen - OK={resumen['OK Count']}, Faltantes={resumen['FALTANTE Count']}, Otros={resumen['Other Count']}, %OK={resumen['Percentage OK']}")
                            ahora = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            Inventario_jed_id = dbService.insertar_inventario_jde(ID, ahora, resumen['OK Count'], resumen['FALTANTE Count'], resumen['Other Count'], resumen['Percentage OK'], NumeroConteo, Sucursal, Ubicacion, TransactionId)
                            logging.info(f"POST /dron/actualizar-inventario: Inventario JDE insertado con ID={Inventario_jed_id}")
                            dbService.insertar_elementos_jde(Inventario_jed_id, inventario_json)
                            dbService.insertar_Fecha_Vuelo_Elementos_JED(ID, Inventario_jed_id)

                            elementos_jed_df = dbService.Exportar_Elementos_JED_a_df(Inventario_jed_id)
                            if elementos_jed_df is not None:
                                logging.info(f"POST /dron/actualizar-inventario: Generando video 3D para Inventario_jed_id={Inventario_jed_id} ({len(elementos_jed_df)} elementos)")
                                ruta_video = Video_Service.create_dron_video_3d(elementos_jed_df, Inventario_jed_id)
                                if ruta_video is not None:
                                    dbService.insertar_ruta_video_inventario_jde(Inventario_jed_id, ruta_video)
                                    logging.info(f"POST /dron/actualizar-inventario: Video generado en '{ruta_video}'")
                                else:
                                    logging.warning(f"POST /dron/actualizar-inventario: No se pudo generar el video para Inventario_jed_id={Inventario_jed_id}")
                            else:
                                logging.warning(f"POST /dron/actualizar-inventario: Exportar_Elementos_JED_a_df retorno None para Inventario_jed_id={Inventario_jed_id}")

                        logging.info(f"POST /dron/actualizar-inventario: Completado con exito para ID={ID} ({end_time - start_time:.2f}s)")
                        return jsonify({'OK': 'Inventario en JD Actualizado con Exito'}), 200
                    else:
                        end_time = time.time()
                        logging.error(f"POST /dron/actualizar-inventario: Fallo al enviar datos de conteo a JD (ID={ID})")
                        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 404)
                        return jsonify({'error': 'No fue posible Enviar Inventario a JD'}), 404
                else:
                    end_time = time.time()
                    logging.error(f"POST /dron/actualizar-inventario: actualizar_estado_inventario retorno None para ID={ID}")
                    SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 404)
                    return jsonify({'error': 'No fue posible Obtener Inventario desde JD'}), 404
            else:
                end_time = time.time()
                logging.error(f"POST /dron/actualizar-inventario: Archivo JD no generado dentro del tiempo esperado (ID={ID})")
                SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 404)
                return jsonify({'error': 'Archivo desde JD No Generado'}), 404
        else:
            end_time = time.time()
            logging.error(f"POST /dron/actualizar-inventario: Generar_Conteo retorno None (Sucursal={Sucursal}, Ubicacion={Ubicacion})")
            SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 404)
            return jsonify({'error': 'No fue posible Obtener Inventario desde JD'}), 404

    except Exception as e:
        end_time = time.time()
        logging.error(f"POST /dron/actualizar-inventario: Error general para ID={ID} - {str(e)}", exc_info=True)
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 500)
        return jsonify({'Error General': str(e)}), 500
    finally:
        DronService.disconnect_from_share_folder(os.getenv('JD_REMOTE_FOLDER'))

@app.route('/dron/crear-video', methods=['POST'])
def crear_video():
    """
    Endpoint para crear el video 3D de un inventario de vuelo.
    ---
    tags:
      - Dron - Inventario
    parameters:
      - in: query
        name: ID
        type: integer
        required: true
        description: ID del vuelo (Inventario_Vuelos)
    responses:
      200:
        description: Video creado exitosamente
        schema:
          type: object
          properties:
            OK:
              type: string
            ruta_video:
              type: string
      404:
        description: No se encontró el inventario o no se pudo generar el video
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Error general del servidor
        schema:
          type: object
          properties:
            Error General:
              type: string
    """
    start_time = time.time()

    ID = request.args.get('ID')
    logging.info(f"POST /dron/crear-video: ID={ID}")

    if not ID or int(ID) <= 0:
        end_time = time.time()
        logging.warning(f"POST /dron/crear-video: ID de vuelo no válido (ID={ID})")
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "crear-video", 404)
        return jsonify({'error': 'ID de vuelo requerido'}), 404

    try:
        Inventario_jed_id = dbService.obtener_inventario_jde_id_por_vuelo(int(ID))
        if not Inventario_jed_id:
            end_time = time.time()
            logging.warning(f"POST /dron/crear-video: No se encontró Inventarios_JDE para ID_Vuelo={ID}")
            SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "crear-video", 404)
            return jsonify({'error': f'No se encontró registro en Inventarios_JDE para el vuelo ID={ID}'}), 404

        logging.info(f"POST /dron/crear-video: Inventario_jed_id={Inventario_jed_id} encontrado para ID_Vuelo={ID}")

        elementos_jed_df = dbService.Exportar_Elementos_JED_a_df(Inventario_jed_id)
        if elementos_jed_df is None:
            end_time = time.time()
            logging.warning(f"POST /dron/crear-video: No se pudieron obtener elementos JDE para Inventario_jed_id={Inventario_jed_id}")
            SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "crear-video", 404)
            return jsonify({'error': 'No se pudieron obtener los elementos JDE para generar el video'}), 404

        logging.info(f"POST /dron/crear-video: {len(elementos_jed_df)} elementos exportados. Generando video 3D...")

        ruta_video = Video_Service.create_dron_video_3d(elementos_jed_df, Inventario_jed_id)
        if ruta_video is None:
            end_time = time.time()
            logging.error(f"POST /dron/crear-video: create_dron_video_3d retornó None para Inventario_jed_id={Inventario_jed_id}")
            SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "crear-video", 404)
            return jsonify({'error': 'No se pudo generar el video 3D'}), 404

        dbService.insertar_ruta_video_inventario_jde(Inventario_jed_id, ruta_video)
        logging.info(f"POST /dron/crear-video: Video generado en '{ruta_video}' para Inventario_jed_id={Inventario_jed_id}")

        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "crear-video", 200)
        return jsonify({'OK': 'Video creado con Éxito', 'ruta_video': ruta_video}), 200

    except Exception as e:
        end_time = time.time()
        logging.error(f"POST /dron/crear-video: Error general para ID={ID} - {str(e)}", exc_info=True)
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "crear-video", 500)
        return jsonify({'Error General': str(e)}), 500


@app.route('/dron/eliminar-inventario', methods=['POST'])
def eliminar_inventario():
    """
    Endpoint para eliminar un registro de inventario de vuelo de la base de datos.
    ---
    tags:
      - Dron - Inventario
    parameters:
      - in: query
        name: ID
        type: integer
        required: true
        description: ID del inventario a eliminar
    responses:
      200:
        description: Inventario eliminado exitosamente
        schema:
          type: object
          properties:
            OK:
              type: string
              example: "Inventario eliminado con Éxito"
      404:
        description: Error al eliminar inventario
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Error general del servidor
        schema:
          type: object
          properties:
            Error:
              type: string
    """
    start_time = time.time()
    
    ID = request.args.get('ID')
    logging.info(f"POST /dron/eliminar-inventario: ID={ID} | IP={request.remote_addr}")

    if ID and int(ID) > 0:
        try:
            Eliminar_inventario_id = dbService.delete_inventario_vuelo_row(ID)
            if Eliminar_inventario_id:
                end_time = time.time()
                logging.info(f"POST /dron/eliminar-inventario: ID={ID} eliminado correctamente")
                SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "eliminar-inventario", 200)
                return jsonify({'OK': 'Inventario eliminado con Exito'}), 200
            else:
                end_time = time.time()
                logging.warning(f"POST /dron/eliminar-inventario: No se pudo eliminar ID={ID}")
                SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "eliminar-inventario", 404)
                return jsonify({'error': 'No fue posible Eliminar Inventario'}), 404
        except Exception as e:
            end_time = time.time()
            logging.error(f"POST /dron/eliminar-inventario: Error al eliminar ID={ID} - {str(e)}", exc_info=True)
            SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "eliminar-inventario", 500)
            return jsonify({'Error': str(e)}), 500
    else:
        end_time = time.time()
        logging.warning(f"POST /dron/eliminar-inventario: ID invalido o no proporcionado (ID={ID})")
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "eliminar-inventario", 404)
        return jsonify({'error': 'No fue posible Obtener ID de Inventario'}), 404

@app.route('/api/data', methods=['POST'])
def post_data():
    """
    Endpoint genérico para recibir datos JSON.
    ---
    tags:
      - Data
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
    responses:
      201:
        description: Datos recibidos exitosamente
        schema:
          type: object
    """
    new_data = request.json
    return jsonify(new_data), 201

@app.route('/log-de-vuelos', methods=['GET'])
def obtener_log_vuelos():
    """
    Endpoint para obtener el log de los últimos 300 vuelos registrados.
    ---
    tags:
      - Data
    responses:
      200:
        description: Lista de vuelos registrados
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            count:
              type: integer
              example: 300
            vuelos:
              type: array
              items:
                type: object
                properties:
                  ID:
                    type: integer
                    example: 1
                  Nombre_Archivo:
                    type: string
                    example: "vuelo_001.csv"
                  Fecha_Vuelo:
                    type: string
                    format: date-time
                    example: "2026-01-31"
                  N_Elementos:
                    type: integer
                    example: 300
                  Tiempo_Vuelo:
                    type: integer
                    example: 1200
                  Estado_Inventario:
                    type: string
                    example: "Pendiente"
      500:
        description: Error al obtener datos
    """
    try:
        start_time = time.time()

        conn = dbService.get_db_connection()
        sql_query = '''
            SELECT TOP 300 ID, Nombre_Archivo, Fecha_Vuelo, N_Elementos, Tiempo_Vuelo, Estado_Inventario
            FROM Inventario_Vuelos
            ORDER BY Fecha_Vuelo DESC
        '''
        df = dbService.execute_sql_query(sql_query, conn, params=None)
        dbService.close_connection(conn)

        if df is None or len(df) == 0:
            return jsonify({'success': True, 'count': 0, 'vuelos': []}), 200

        dron_folder = os.getenv('Dron_Folder', '')
        if dron_folder:
            df['Nombre_Archivo'] = df['Nombre_Archivo'].apply(
                lambda x: os.path.join(dron_folder, x) if x else x
            )

        vuelos = df.to_dict(orient='records')
        for v in vuelos:
            v['Fecha_Vuelo'] = str(v['Fecha_Vuelo'])

        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "log_de_vuelos", 200)
        logging.info(f"GET /log-de-vuelos: Returned {len(vuelos)} records")

        return jsonify({'success': True, 'count': len(vuelos), 'vuelos': vuelos}), 200

    except Exception as e:
        logging.error(f"GET /log-de-vuelos: Error - {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'vuelos': []}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para recibir y procesar archivos CSV del dron.
    ---
    tags:
      - File Upload
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: Archivo CSV con registros EPC
    responses:
      200:
        description: Archivo cargado exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
              example: "File successfully uploaded"
            filename:
              type: string
      400:
        description: Error de validación de archivo
        schema:
          type: object
          properties:
            error:
              type: string
      500:
        description: Error en el procesamiento del archivo
        schema:
          type: object
          properties:
            error:
              type: string
    """
    start_time = time.time()
    logging.info(f"POST /upload: request recibido desde {request.remote_addr}")

    if 'file' not in request.files:
        end_time = time.time()
        logging.warning(f"POST /upload: request sin archivo adjunto desde {request.remote_addr}")
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "Upload_File", 400)
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        end_time = time.time()
        logging.warning("POST /upload: nombre de archivo vacio")
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "Upload_File", 400)
        return jsonify({'error': 'No selected file'}), 400

    if file:
        logging.info(f"POST /upload: procesando archivo '{file.filename}'")
        try:
            df = pd.read_csv(file.stream, sep=',', dtype=str)
            archivos_creados = DronService.Limpiar_Archivos_Dron(df, os.getenv('Dron_Folder'))
            logging.info(f"POST /upload: {len(archivos_creados)} archivos generados desde el CSV")

            for filename in archivos_creados:
                SaveExecutions.Guardar_Recepcion_Archivos_Dron_a_csv(filename)
                dbService.insertar_datos_inventario_vuelos(filename)
                logging.info(f"POST /upload: archivo '{filename}' procesado e insertado en BD")

            end_time = time.time()
            logging.info(f"POST /upload: completado ({end_time - start_time:.2f}s), ultimo archivo='{filename}'")
            SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "Upload_File", 200)
            return jsonify({'message': 'File successfully uploaded', 'filename': filename}), 200
        except Exception as e:
            end_time = time.time()
            logging.error(f"POST /upload: Error procesando archivo - {str(e)}", exc_info=True)
            SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "Upload_File", 500)
            return jsonify({'error': str(e)}), 500

@app.route('/predict-zone', methods=['POST'])
def predict_zone():
    """
    Endpoint para predecir la zona (PF1, PF2, PF5, PT) de un inventario.
    
    Analiza la distribución de ubicaciones (zonas) de los EPCs en un inventario
    y predice su zona basado en el porcentaje de ocurrencias.
    
    Reglas de predicción:
    - Si una zona tiene >60% de EPCs → retorna esa zona
    - Si múltiples zonas con distribución mixta → retorna 'PT' (todas)
    - Si ninguna cumple criterios → retorna null (Unknown)
    
    ---
    tags:
      - Inventario - Análisis
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - id_inventario
          properties:
            id_inventario:
              type: integer
              description: ID del inventario a analizar
              example: 46
    responses:
      200:
        description: Predicción de zona exitosa
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            zone:
              type: string
              description: "Zona predicha (PF1, PF2, PF5, PT, o null)"
              example: "PF2"
            confidence:
              type: number
              description: "Porcentaje de confianza (0-100, null si es PT)"
              example: 83.5
            breakdown:
              type: object
              description: "Desglose de porcentajes por zona"
              example: {"PF1": 5.0, "PF2": 83.5, "PF5": 11.5}
            total_elements:
              type: integer
              description: "Total de EPCs analizados"
              example: 200
      400:
        description: Parámetros inválidos o inventario no encontrado
      500:
        description: Error interno del servidor
    """
    try:
        start_time = time.time()
        
        # Obtener ID del inventario desde el request
        data = request.get_json()
        
        if not data:
            logging.warning("POST /predict-zone: Request sin JSON")
            return jsonify({'success': False, 'error': 'Request body must be JSON'}), 400
        
        id_inventario = data.get('id_inventario')
        
        if not id_inventario:
            logging.warning("POST /predict-zone: Missing id_inventario parameter")
            return jsonify({'success': False, 'error': 'id_inventario is required'}), 400
        
        # Validar que sea un entero
        try:
            id_inventario = int(id_inventario)
        except (TypeError, ValueError):
            logging.warning(f"POST /predict-zone: id_inventario no es entero: {id_inventario}")
            return jsonify({'success': False, 'error': 'id_inventario must be an integer'}), 400
        
        # Llamar función de predicción
        prediction = dbService.predict_inventory_zone(id_inventario)
        
        if prediction.get('error'):
            logging.error(f"POST /predict-zone: Error en predicción - {prediction['error']}")
            return jsonify({
                'success': False,
                'error': prediction['error']
            }), 500
        
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "predict_zone", 200)
        
        logging.info(f"POST /predict-zone: ID={id_inventario}, Zone={prediction['zone']}, Confidence={prediction['confidence']}%")
        
        return jsonify({
            'success': True,
            'zone': prediction['zone'],
            'confidence': prediction['confidence'],
            'breakdown': prediction['breakdown'],
            'total_elements': prediction['total_elements']
        }), 200
    
    except Exception as e:
        logging.error(f"POST /predict-zone: Error general - {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/printer/<msg>', methods=['POST'])
def show_message(msg):
    """
    Endpoint de 'Keep Alive' para que el dron verifique la conectividad con el servidor.
    ---
    tags:
      - Keep Alive
    parameters:
      - in: path
        name: msg
        type: string
        required: true
        description: Mensaje de keep alive
    responses:
      200:
        description: Keep alive registrado (sin solicitud de envío)
        schema:
          type: object
          properties:
            message:
              type: string
              example: "ok"
      201:
        description: Keep alive registrado (solicitud de envío de datos activa)
        schema:
          type: object
          properties:
            message:
              type: string
              example: "ok"
      500:
        description: Error en el servidor
        schema:
          type: object
          properties:
            Error:
              type: string
    """
    try:
        client_ip = request.remote_addr
        dbService.insert_client_ip_to_heartbeats(client_ip)

        if dbService.Dron_GET_Boton_Envio_Datos():
            logging.info(f"POST /printer/{msg}: heartbeat desde {client_ip} - solicitud de envio activa")
            return jsonify({'message': 'ok'}), 201
        else:
            logging.debug(f"POST /printer/{msg}: heartbeat desde {client_ip}")
            return jsonify({'message': 'ok'}), 200

    except Exception as e:
        logging.error(f"POST /printer/{msg}: Error - {str(e)}", exc_info=True)
        return jsonify({'Error': str(e)}), 500

@app.route('/dron/TestJDFolder', methods=['POST'])
def TestJDFolder():
    """
    Endpoint de prueba para verificar la conexión a la carpeta compartida de JD.
    ---
    tags:
      - Testing
    responses:
      200:
        description: Conexión exitosa a la carpeta compartida
        schema:
          type: object
          properties:
            message:
              type: string
              example: "OK"
      500:
        description: Error de conexión
        schema:
          type: object
          properties:
            Error:
              type: string
    """
    try:
        logging.info(f"POST /dron/TestJDFolder: conectando a {os.getenv('JD_REMOTE_FOLDER')} con usuario {os.getenv('JD_REMOTE_FOLDER_USERNAME')}")
        DronService.connect_to_share_folder(os.getenv('JD_REMOTE_FOLDER'), os.getenv('JD_REMOTE_FOLDER_USERNAME'), os.getenv('JD_REMOTE_FOLDER_PASSWORD'))
        logging.info("POST /dron/TestJDFolder: conexion exitosa")
        return "OK"
    except Exception as e:
        logging.error(f"POST /dron/TestJDFolder: Error de conexion - {str(e)}", exc_info=True)
        return jsonify({'Error': str(e)}), 500
    finally:
        DronService.disconnect_from_share_folder(os.getenv('JD_REMOTE_FOLDER'))

# ------------------------------------------------------------------------------
# Bloque de Ejecución Principal
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """
    El bloque principal del script que inicia el servidor Flask en el host
    '0.0.0.0' (todas las interfaces) y en el puerto configurado en .env
    """
    port = int(API_PORT)
    logging.info(f"Iniciando servidor en http://{API_HOST}:{API_PORT}")
    logging.info(f"Swagger UI disponible en http://{API_HOST}:{API_PORT}/apidocs")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False, use_debugger=False, threaded=True)
