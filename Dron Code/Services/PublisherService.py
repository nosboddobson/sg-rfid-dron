import requests
#import time
import os
import subprocess
import asyncio
from urllib.parse import urlparse
import glob
from datetime import datetime
import logging
import csv

class Globals:
    variable = None
    flag_archivos_validos = False
    archivos = []

async def check_ping(host, count=1, timeout=1):
    try:
        result = await asyncio.to_thread(
            subprocess.check_output,
            ["ping", "-c", str(count), "-W", str(timeout), host],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

async def send_file(url, nombre_archivo, max_intentos=3, tiempo_espera=5):
    """Función auxiliar para enviar un archivo individual"""
    for intento in range(max_intentos):
        try:
            with open(nombre_archivo, 'rb') as archivo_csv:
                archivos = {'file': (os.path.basename(nombre_archivo), archivo_csv)}
                # Usar to_thread para la operación bloqueante de requests
                respuesta = await asyncio.to_thread(
                    requests.post,
                    url,
                    files=archivos,
                    timeout=3
                )
                
                if respuesta.status_code == 200:
                    print(f'Archivo {nombre_archivo} enviado exitosamente.')
                    await asyncio.to_thread(os.remove, nombre_archivo)
                    print(f'Archivo {nombre_archivo} eliminado.')
                    return True
                else:
                    print(f'Error al enviar el archivo {nombre_archivo}: {respuesta.status_code} - {respuesta.text}')
                    
        except requests.exceptions.RequestException as e:
            msg = f'Error al enviar el archivo {nombre_archivo}: {e}'
            print(msg)
            logging.error(msg)
            
            if intento < max_intentos - 1:
                await asyncio.sleep(tiempo_espera)
                
    return False


def es_cabecera_valida(header):
    """
    Verifica si la cabecera del CSV tiene las columnas esperadas
    """
    # Ajusta estas columnas según tu estructura esperada
    columnas_esperadas = {
        'EPC',
        'Antenna ID',
        'Frequency (MHz)',
        'PC List',
        'RSSI List',
        'Read Count',
        'Timestamp',
        'Localtime'
    }
    
    flag = set(header) == columnas_esperadas
    
    if(flag):
        print('cabecera valida')
    else:
        print('cabecera invalida')

    return flag
 
def validar_y_filtrar_archivos(patron_csv):
    """
    Valida los archivos CSV y elimina los inválidos.
    Retorna la lista de archivos válidos.
    """
    todos_archivos = glob.glob(patron_csv)
    
    if Globals.flag_archivos_validos == True: return
    archivos_validos = []
    for archivo in todos_archivos:
        # Verificar si el archivo está vacío
        if os.path.getsize(archivo) == 0:
            try:
                os.remove(archivo)
                print(f"Archivo vacío eliminado: {archivo}")
                continue
            except Exception as e:
                print(f"Error al eliminar archivo vacío {archivo}: {e}")
                continue
        
        try:
            with open(archivo, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                
                # Leer la cabecera
                header = next(reader, None)
                if header is None:
                    csvfile.close()
                    os.remove(archivo)
                    print(f"Archivo sin contenido eliminado: {archivo}")
                    continue
                
                # Verificar si la cabecera es válida
                if not es_cabecera_valida(header):
                    csvfile.close()
                    os.remove(archivo)
                    print(f"Archivo con cabecera inválida eliminado: {archivo}")
                    continue
                
                # Verificar si hay datos después de la cabecera
                first_row = next(reader, None)
                if first_row is None:
                    csvfile.close()
                    os.remove(archivo)
                    print(f"Archivo con solo cabecera eliminado: {archivo}")
                    continue
                
                # El archivo es válido
                archivos_validos.append(archivo)
        
        except Exception as e:
            print(f"Error al procesar archivo {archivo}: {e}")
            continue
    Globals.flag_archivos_validos = True
    Globals.archivos = archivos_validos
    return archivos_validos

async def send_dron_csv():
    url = 'http://10.185.36.30:5100/upload'
    directorio = '/home/sg-sierra-dron/Documents/sierra-dron/sg-rfid-dron/files/'
    patron_csv = os.path.join(directorio, '*.csv')
    
    # Primero validamos los archivos
    if Globals.flag_archivos_validos == False:
        Globals.archivos = validar_y_filtrar_archivos(patron_csv)
    archivos_pendientes = 0
        
    archivos_validos = Globals.archivos  
    archivos = archivos_validos
    if not archivos:
        print("No hay archivos válidos para procesar.")
        return True, 0  # Éxito, sin archivos pendientes
    
    # Solo si hay archivos válidos, verificamos la conexión
    hostname = urlparse(url).hostname
    archivos_enviados = []
    archivos_con_error = []

    if await check_ping(hostname):
        # Crear y ejecutar tareas para cada archivo válido
        tareas = [send_file(url, archivo) for archivo in archivos]
        resultados = await asyncio.gather(*tareas, return_exceptions=True)
        
        # Procesar resultados
        for archivo, resultado in zip(archivos, resultados):
            if isinstance(resultado, Exception):
                print(f"Error procesando {archivo}: {resultado}")
                archivos_con_error.append(archivo)
            elif resultado:
                archivos_enviados.append(archivo)
            else:
                archivos_con_error.append(archivo)
                
        # Resumen de la operación
        if archivos_enviados:
            print(f"Se enviaron y eliminaron exitosamente {len(archivos_enviados)} archivos.")
        if archivos_con_error:
            print(f"No se pudieron enviar {len(archivos_con_error)} archivos.")
            
    else:
        msg = f"No hay conexión con {url}..."
        print(msg)
        logging.warning(msg)
        return False, archivos  # Fallo de conexión, todos los archivos quedan pendientes

    exito = len(archivos_enviados) > 0 and len(archivos_con_error) == 0
    print('archivos_pendientes: ', archivos_pendientes)
    return exito, archivos_pendientes  # Retorna éxito/fallo y archivos pendientes

# Para uso directo del script
if __name__ == '__main__':
    print('FileServices_main()')
    asyncio.run(send_dron_csv())