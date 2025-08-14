# ==============================================================================
# Módulo: publisherService.py
#
# Descripción:
# Este módulo se encarga de la gestión y publicación de archivos de inventario
# en formato CSV a un servidor central. Utiliza programación asíncrona (`asyncio`)
# para manejar operaciones de E/S de red y disco de manera eficiente. Las
# funcionalidades clave incluyen la validación de archivos CSV, la verificación
# de la conectividad de red y el envío de archivos con una estrategia de reintentos.
# ==============================================================================

# ------------------------------------------------------------------------------
# Importaciones de Módulos
# ------------------------------------------------------------------------------
import requests
import os
import subprocess
import asyncio
from urllib.parse import urlparse
import glob
import logging
import csv

class Globals:
    """
    Clase contenedora para variables globales del módulo.

    Esta clase almacena el estado de los archivos procesados para evitar
    re-validaciones innecesarias en ciclos posteriores.

    Attributes:
        variable: Una variable de uso general. Actualmente sin uso específico.
        flag_archivos_validos (bool): Indica si los archivos ya han sido validados.
        archivos (list): Una lista de las rutas de los archivos CSV válidos.
    """
    variable = None
    flag_archivos_validos = False
    archivos = []

async def check_ping(host: str, count: int = 1, timeout: int = 1) -> bool:
    """
    Verifica la conectividad de red a un host específico utilizando el comando ping.

    Ejecuta el comando ping en un hilo separado (`asyncio.to_thread`) para
    evitar bloquear el bucle de eventos de asyncio.

    Args:
        host (str): La dirección IP o nombre de host a verificar.
        count (int, optional): El número de paquetes ping a enviar. Por defecto, 1.
        timeout (int, optional): El tiempo de espera en segundos para la respuesta.
                                 Por defecto, 1.

    Returns:
        bool: `True` si el ping es exitoso, `False` en caso de fallo.
    """
    try:
        result = await asyncio.to_thread(
            subprocess.check_output,
            ["ping", "-c", str(count), "-W", str(timeout), host],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        logging.info(f"Ping exitoso a {host}")
        return True
    except subprocess.CalledProcessError:
        logging.warning(f"Fallo de ping a {host}")
        return False

async def send_file(url: str, nombre_archivo: str, max_intentos: int = 3, tiempo_espera: int = 5) -> bool:
    """
    Envía un archivo individual a una URL a través de una solicitud HTTP POST.

    Esta función implementa una lógica de reintentos en caso de fallos de red.
    Si el archivo se envía exitosamente (código 200), se elimina del disco local.
    La operación de `requests.post` se realiza en un hilo separado.

    Args:
        url (str): La URL del servidor al que se enviará el archivo.
        nombre_archivo (str): La ruta completa del archivo CSV a enviar.
        max_intentos (int, optional): Número máximo de intentos de envío. Por defecto, 3.
        tiempo_espera (int, optional): Tiempo en segundos entre reintentos. Por defecto, 5.

    Returns:
        bool: `True` si el archivo se envió y eliminó exitosamente, `False` en caso contrario.
    """
    for intento in range(max_intentos):
        try:
            with open(nombre_archivo, 'rb') as archivo_csv:
                archivos = {'file': (os.path.basename(nombre_archivo), archivo_csv)}
                respuesta = await asyncio.to_thread(
                    requests.post,
                    url,
                    files=archivos,
                    timeout=3
                )
            
            if respuesta.status_code == 200:
                logging.info(f'Archivo {nombre_archivo} enviado exitosamente.')
                await asyncio.to_thread(os.remove, nombre_archivo)
                logging.info(f'Archivo {nombre_archivo} eliminado.')
                return True
            else:
                logging.error(f'Error al enviar el archivo {nombre_archivo}: {respuesta.status_code} - {respuesta.text}')
                
        except requests.exceptions.RequestException as e:
            logging.error(f'Error de solicitud al enviar el archivo {nombre_archivo}: {e}')
        
        if intento < max_intentos - 1:
            logging.warning(f"Reintentando el envío de {nombre_archivo} en {tiempo_espera} segundos...")
            await asyncio.sleep(tiempo_espera)
            
    return False

def es_cabecera_valida(header: list) -> bool:
    """
    Verifica si la cabecera de un archivo CSV tiene las columnas esperadas.

    Args:
        header (list): Una lista de cadenas que representan las columnas del CSV.

    Returns:
        bool: `True` si la cabecera coincide con el conjunto de columnas
              esperadas, `False` en caso contrario.
    """
    columnas_esperadas = {
        'EPC', 'Antenna ID', 'Frequency (MHz)', 'PC List', 'RSSI List',
        'Read Count', 'Timestamp', 'Localtime'
    }
    
    flag = set(header) == columnas_esperadas
    if flag:
        logging.debug('Cabecera válida.')
    else:
        logging.warning(f'Cabecera inválida. Esperado: {columnas_esperadas}, Encontrado: {set(header)}')
    
    return flag
 
def validar_y_filtrar_archivos(patron_csv: str) -> list:
    """
    Encuentra, valida y filtra los archivos CSV en una ruta dada.

    Elimina archivos que están vacíos, no tienen contenido o tienen una
    cabecera no válida. Almacena la lista de archivos válidos en la clase
    `Globals` para evitar re-procesamientos.

    Args:
        patron_csv (str): Un patrón de ruta para buscar archivos CSV
                          (ej. '/ruta/a/los/archivos/*.csv').

    Returns:
        list: Una lista de las rutas de los archivos CSV que son válidos.
    """
    todos_archivos = glob.glob(patron_csv)
    
    if Globals.flag_archivos_validos:
        return Globals.archivos
        
    archivos_validos = []
    for archivo in todos_archivos:
        if os.path.getsize(archivo) == 0:
            try:
                os.remove(archivo)
                logging.info(f"Archivo vacío eliminado: {archivo}")
            except Exception as e:
                logging.error(f"Error al eliminar archivo vacío {archivo}: {e}")
            continue
            
        try:
            with open(archivo, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader, None)
                if header is None:
                    csvfile.close()
                    os.remove(archivo)
                    logging.warning(f"Archivo sin contenido eliminado: {archivo}")
                    continue
                
                if not es_cabecera_valida(header):
                    csvfile.close()
                    os.remove(archivo)
                    logging.warning(f"Archivo con cabecera inválida eliminado: {archivo}")
                    continue
                
                first_row = next(reader, None)
                if first_row is None:
                    csvfile.close()
                    os.remove(archivo)
                    logging.warning(f"Archivo con solo cabecera eliminado: {archivo}")
                    continue
                
                archivos_validos.append(archivo)
        
        except Exception as e:
            logging.error(f"Error al procesar archivo {archivo}: {e}")
            
    Globals.flag_archivos_validos = True
    Globals.archivos = archivos_validos
    return archivos_validos

async def send_dron_csv() -> tuple[bool, list]:
    """
    Función principal para orquestar el envío de archivos CSV de inventario.

    1. Valida los archivos CSV existentes en un directorio predefinido.
    2. Verifica la conectividad de red con el servidor de destino.
    3. Si hay conexión, envía cada archivo válido de forma asíncrona.
    4. Procesa los resultados, eliminando los archivos enviados con éxito.

    Returns:
        tuple[bool, list]: Una tupla con un booleano que indica si el proceso fue
                           exitoso y una lista de los archivos que no pudieron
                           ser enviados (pendientes).
    """
    url = 'http://10.185.36.30:5100/upload'
    directorio = '/home/sg-sierra-dron/Documents/sierra-dron/sg-rfid-dron/files/'
    patron_csv = os.path.join(directorio, '*.csv')
    
    archivos = validar_y_filtrar_archivos(patron_csv)
    
    if not archivos:
        logging.info("No hay archivos válidos para procesar.")
        return True, []
    
    hostname = urlparse(url).hostname
    archivos_enviados = []
    archivos_con_error = []

    if await check_ping(hostname):
        tareas = [send_file(url, archivo) for archivo in archivos]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        
        for archivo, resultado in zip(archivos, resultados):
            if isinstance(resultado, Exception):
                logging.error(f"Error procesando {archivo}: {resultado}")
                archivos_con_error.append(archivo)
            elif resultado:
                archivos_enviados.append(archivo)
            else:
                archivos_con_error.append(archivo)
                
        if archivos_enviados:
            logging.info(f"Se enviaron y eliminaron exitosamente {len(archivos_enviados)} archivos.")
        if archivos_con_error:
            logging.warning(f"No se pudieron enviar {len(archivos_con_error)} archivos.")
            
        exito = len(archivos_con_error) == 0
        return exito, archivos_con_error
    else:
        logging.warning(f"No hay conexión con {url}. Archivos pendientes: {len(archivos)}")
        return False, archivos

if __name__ == '__main__':
    """
    Bloque de ejecución principal del script para pruebas.
    """
    logging.basicConfig(level=logging.INFO)
    print('Iniciando el servicio de publicación de archivos...')
    asyncio.run(send_dron_csv())
    print('Finalizado.')