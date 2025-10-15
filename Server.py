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
import uuid
from dotenv import load_dotenv
from flask import Flask, jsonify, request
import jsonschema
import pandas as pd
from Services import JDService, LogService as SaveExecutions
from Services import DronService
from Services import MsSQL_Service as dbService
from Services import Video_Service 
import os
import datetime
import logging

# ------------------------------------------------------------------------------
# Configuración de la Aplicación
# ------------------------------------------------------------------------------
# Crear una instancia de la aplicación Flask.
app = Flask(__name__)

# Cargar variables de entorno desde un archivo .env.
# La opción `override=True` permite sobrescribir variables de entorno existentes.
load_dotenv(override=True)
# Configuración del logger
log_file_path = os.getenv('DRON_API_LOG_PATH', 'd:/logs/Sierra_dron_api.txt')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Log al iniciar el servidor
logging.info("Servidor Flask iniciado.")

# Log para cada request
@app.before_request
def log_request_info():
    logging.info(f"Ruta accedida: {request.path} | Método: {request.method} | IP: {request.remote_addr}")

@app.after_request
def log_response_info(response):
    status = "Success" if response.status_code < 400 else "Error"
    logging.info(f"Ruta accedida: {request.path} | Status: {response.status_code} ({status})")
    return response
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
    
    Registra la ejecución en un archivo CSV.
    
    Returns:
        str: Un mensaje de prueba.
    """
    start_time = time.time()
    end_time = time.time()
    SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "test", 200)
    return '¡Prueba de Api Exitosa!'

@app.route('/dron/actualizar-estado-inventario', methods=['POST'])
def actualizar_estado_inventario():
    """
    Endpoint para actualizar el estado del inventario basado en los datos del dron.
    
    Recibe un JSON con la estructura del inventario, lo valida contra un esquema
    predefinido y luego llama a un servicio para procesar los datos.

    JSON Schema:
    - Espera un objeto con una clave "Inventario".
    - "Inventario" debe ser un array de objetos.
    - Cada objeto del array debe contener campos específicos como "BatchNumber",
      "Sequence", "NumeroConteo", etc., todos de tipo string o integer.
      
    Returns:
        tuple: Una tupla con un objeto JSON y un código de estado HTTP.
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
    
    try:
        # Validar el JSON entrante contra el esquema.
        jsonschema.validate(instance=archivo_json, schema=json_schema)
        
        # Procesar el inventario si la validación es exitosa.
        archivo_json = DronService.actualizar_estado_inventario(archivo_json)
        
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-estado-inventario", 200)
        return jsonify(archivo_json), 200
        
    except jsonschema.exceptions.ValidationError as e:
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-estado-inventario", 404)
        return jsonify({'error': 'Esquema de Archivo no Valido!', 'Campos necesarios': json_schema["properties"]["Inventario"]["items"]["required"]}), 404
    except Exception as e:
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-estado-inventario", 500)
        return jsonify({'Error': str(e)}), 500

@app.route('/dron/actualizar-inventario', methods=['POST'])
def actualizar_inventario():
    """
    Endpoint para orquestar el proceso completo de actualización de inventario.
    
    - Recibe parámetros de sucursal, ubicación, ID y tipo de inventario.
    - Conecta y limpia carpetas compartidas.
    - Llama a la API de JD Edwards para generar un archivo de inventario.
    - Compara el inventario del dron con el de JD Edwards.
    - Guarda el resultado en un archivo CSV.
    - Retorna los datos actualizados a JD Edwards.
    - Genera un reporte y un video 3D del inventario.
    - Actualiza el estado en la base de datos local.
    
    Returns:
        tuple: Una tupla con un objeto JSON y un código de estado HTTP.
    """
    start_time = time.time()
    
    Sucursal = request.args.get('Sucursal', "SGMINA")
    Ubicacion = request.args.get('Ubicacion', "PT")
    ID = request.args.get('ID')
    Tipo_Inventario = request.args.get('Tipo_Inventario')

    if Tipo_Inventario == "Completo":
        Ubicacion = "PT"
    
    try:
        # Conectar y limpiar la carpeta compartida de JD.
        DronService.connect_to_share_folder(os.getenv('JD_REMOTE_FOLDER'), os.getenv('JD_REMOTE_FOLDER_USERNAME'), os.getenv('JD_REMOTE_FOLDER_PASSWORD'))
        DronService.borrar_archivos_en_carpeta(os.getenv('JD_REMOTE_FOLDER'))
        
        # Generar el conteo en JD Edwards.
        if JDService.Generar_Conteo(Sucursal, Ubicacion) is not None:
            time.sleep(40) # Esperar a que el archivo se genere.

            if JDService.Archivo_Conteo_Generado_Nuevo(start_time):
                # Comparar y obtener el inventario actualizado.
                inventario_json, NumeroConteo, TransactionId = DronService.actualizar_estado_inventario(ID)
                
                if inventario_json:
                    # Guardar el resultado del inventario en un CSV.
                    DronService.Guardar_json_como_csv(inventario_json, os.getenv('DRON_FOLDER_RESULTS'), Ubicacion)

                    # Devolver el inventario actualizado a JD Edwards.
                    if JDService.Retorno_Datos_Conteo(inventario_json):
                        # Generar reporte y cerrar el conteo en JD.
                        JDService.Generar_Reporte_Conteo(NumeroConteo)
                        
                        end_time = time.time()
                        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 200)

                        if ID:
                            # Actualizar la base de datos local.
                            dbService.Actuaizar_Estado_inventario_vuelos(int(ID))
                            resumen = dbService.Resumen_de_Conteo_desde_Json(inventario_json)
                            ahora = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            Inventario_jed_id = dbService.insertar_inventario_jde(ID, ahora, resumen['OK Count'], resumen['FALTANTE Count'], resumen['Other Count'], resumen['Percentage OK'], NumeroConteo, Sucursal, Ubicacion, TransactionId)
                            dbService.insertar_elementos_jde(Inventario_jed_id, inventario_json)
                            dbService.insertar_Fecha_Vuelo_Elementos_JED(ID, Inventario_jed_id)
                            
                            elementos_jed_df = dbService.Exportar_Elementos_JED_a_df(Inventario_jed_id)
                            
                            if elementos_jed_df is not None:
                                ruta_video = Video_Service.create_dron_video_3d(elementos_jed_df, Inventario_jed_id)
                                if ruta_video is not None:
                                    dbService.insertar_ruta_video_inventario_jde(Inventario_jed_id, ruta_video)
                                    
                        return jsonify({'OK': 'Inventario en JD Actualizado con Éxito'}), 200
                    else:
                        end_time = time.time()
                        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 404)
                        return jsonify({'error': 'No fue posible Enviar Inventario a JD'}), 404 
                else:
                    end_time = time.time()
                    SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 404)
                    return jsonify({'error': 'No fue posible Obtener Inventario desde JD'}), 404
            else:
                end_time = time.time()
                SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 404)
                return jsonify({'error': 'Archivo desde JD No Generado'}), 404 
        else:
            end_time = time.time()
            SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 404)
            return jsonify({'error': 'No fue posible Obtener Inventario desde JD'}), 404
            
    except Exception as e:
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "actualizar-inventario", 500)
        print ({'Error General': str(e)})
        return jsonify({'Error General': str(e)}), 500
    finally:
        # Asegurar la desconexión del recurso compartido.
        DronService.disconnect_from_share_folder(os.getenv('JD_REMOTE_FOLDER'))

@app.route('/dron/eliminar-inventario', methods=['POST'])
def eliminar_inventario():
    """
    Endpoint para eliminar un registro de inventario de vuelo de la base de datos.

    Recibe el ID del inventario como parámetro de la URL.
    
    Returns:
        tuple: Una tupla con un objeto JSON y un código de estado HTTP.
    """
    start_time = time.time()
    
    ID = request.args.get('ID')
    if ID and int(ID) > 0:
        try:
            Eliminar_inventario_id = dbService.delete_inventario_vuelo_row(ID)
            
            if Eliminar_inventario_id:
                end_time = time.time()
                SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "eliminar-inventario", 200)
                return jsonify({'OK': 'Inventario eliminado con Éxito'}), 200 
            else:
                end_time = time.time()
                SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "eliminar-inventario", 404)
                return jsonify({'error': 'No fue posible Eliminar Inventario'}), 404 
        except Exception as e:
            end_time = time.time()
            SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "eliminar-inventario", 500)
            return jsonify({'Error': str(e)}), 500
    else:
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "elimimar-inventario", 404)
        return jsonify({'error': 'No fue posible Obtener ID de Inventario'}), 404

@app.route('/api/data', methods=['POST'])
def post_data():
    """
    Endpoint genérico para recibir datos JSON.
    
    Returns:
        tuple: Una tupla con un objeto JSON y un código de estado HTTP 201 (Created).
    """
    new_data = request.json
    return jsonify(new_data), 201

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint para recibir y procesar archivos CSV del dron.
    
    - Valida que se haya subido un archivo.
    - Genera un nombre de archivo único con un UUID y una marca de tiempo.
    - Guarda el archivo en la carpeta de drones.
    - Actualiza los registros de la base de datos y los logs.
    
    Returns:
        tuple: Una tupla con un objeto JSON y un código de estado HTTP.
    """
    start_time = time.time()

    if 'file' not in request.files:
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "Upload_File", 400)
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "Upload_File", 500)
        return jsonify({'error': 'No selected file'}), 400
    

    if file:

        df = pd.read_csv(file.stream, sep=',', dtype=str)

        # Llamar a la función Limpiar_Archivos_Dron para obtener la lista de archivos
        archivos_creados = DronService.Limpiar_Archivos_Dron(df,os.getenv('DRON_FOLDER'))
    
      
        for filename in archivos_creados:
            # --- Código original que se ejecutaba con 'file' ---
            # unique_id = str(uuid.uuid4()) # Ya no es necesario generar un nuevo UUID
            # filename = utc_time() + "_" + unique_id + "_epc_records.csv" # Ya no es necesario generar un nuevo nombre
            # file.save(os.path.join(os.getenv('DRON_FOLDER'), filename)) # Ya no se guarda porque ya está guardado en Limpiar_Archivos_Dron

            SaveExecutions.Guardar_Recepcion_Archivos_Dron_a_csv(filename)
            dbService.insertar_datos_inventario_vuelos(filename)
            
        end_time = time.time()
        SaveExecutions.Guardar_Ejecucion_a_csv(start_time, end_time, "Upload_File", 200)
        return jsonify({'message': 'File successfully uploaded', 'filename': filename}), 200

@app.route('/printer/<msg>', methods=['POST'])
def show_message(msg):
    """
    Endpoint de 'Keep Alive' para que el dron verifique la conectividad con el servidor.
    
    También verifica si se ha presionado un botón en la interfaz web para
    solicitar al dron que envíe los datos.
    - Retorna 200 si solo es un 'keep alive'.
    - Retorna 201 si el botón de 'envío de datos' ha sido presionado.
    
    Returns:
        tuple: Una tupla con un objeto JSON y un código de estado HTTP.
    """
    try:
        client_ip = request.remote_addr
        dbService.insert_client_ip_to_heartbeats(client_ip)
        
        if dbService.Dron_GET_Boton_Envio_Datos(): 
            return jsonify({'message': 'ok'}), 201
        else:
            return jsonify({'message': 'ok'}), 200
            
    except Exception as e:
        return jsonify({'Error': str(e)}), 500

@app.route('/dron/TestJDFolder', methods=['POST'])
def TestJDFolder():
    """
    Endpoint de prueba para verificar la conexión a la carpeta compartida de JD.
    
    Conecta a la carpeta compartida utilizando las credenciales de las
    variables de entorno.
    
    Returns:
        tuple: Una tupla con un mensaje de estado o un objeto JSON de error
               y su código de estado HTTP.
    """
    try:
        print("connecting to: " + os.getenv('JD_REMOTE_FOLDER') + " with user " + os.getenv('JD_REMOTE_FOLDER_USERNAME'))
        DronService.connect_to_share_folder(os.getenv('JD_REMOTE_FOLDER'), os.getenv('JD_REMOTE_FOLDER_USERNAME'), os.getenv('JD_REMOTE_FOLDER_PASSWORD'))
        return "OK"
    except Exception as e:
        print({'Error': str(e)})
        return jsonify({'Error': str(e)}), 500
    finally:
        DronService.disconnect_from_share_folder(os.getenv('JD_REMOTE_FOLDER'))

# ------------------------------------------------------------------------------
# Bloque de Ejecución Principal
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    """
    El bloque principal del script que inicia el servidor Flask en el host
    '0.0.0.0' y en el puerto 5100.
    """
    app.run(host='0.0.0.0', port=5100)
