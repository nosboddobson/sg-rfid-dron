import requests
import time
import os
import subprocess
import asyncio
from urllib.parse import urlparse
import glob
from datetime import datetime
import logging
import csv
import fcntl
import errno
from task_manager import pending_files_to_send # Importación corregida

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

def es_archivo_seguro_procesar(ruta_archivo):
    """
    Verifica si es seguro procesar un archivo (no está en uso y no es muy reciente)
    """
    try:
        # Verificar si fue modificado recientemente (últimos 10 segundos)
        tiempo_modificacion = os.path.getmtime(ruta_archivo)
        tiempo_actual = time.time()
        if (tiempo_actual - tiempo_modificacion) < 10:
            return False, "Archivo modificado recientemente"
        
        # Verificar si está siendo usado
        with open(ruta_archivo, 'r+') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        
        return True, "OK"
        
    except (IOError, OSError) as e:
        if e.errno == errno.EAGAIN or e.errno == errno.EACCES:
            return False, "Archivo en uso"
        return False, f"Error: {e}"

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

def pending_files():
    """
    Cuenta los archivos CSV pendientes y devuelve información detallada
    """
    directorio = '/home/sg-sierra-dron/Documents/sierra-dron/sg-rfid-dron/files/'

    try:
        # Obtener lista de archivos en el directorio
        archivos = os.listdir(directorio)
        
        # Filtrar solo archivos CSV (sin distinguir mayúsculas/minúsculas)
        archivos_csv = [archivo for archivo in archivos if archivo.lower().endswith('.csv')]
        
        print(f"Número de archivos CSV encontrados: {len(archivos_csv)}")
        
        # Mostrar los nombres de los archivos CSV con su cantidad de líneas
        if archivos_csv:
            print("Archivos CSV encontrados:")
            info_detallada = []
            
            for archivo in archivos_csv:
                ruta_completa = os.path.join(directorio, archivo)
                try:
                    with open(ruta_completa, 'r', encoding='utf-8') as f:
                        lineas = sum(1 for _ in f)
                    print(f"  - {archivo}: {lineas} líneas")
                    info_detallada.append(f"{archivo}({lineas})")
                except Exception as e:
                    print(f"  - {archivo}: Error al leer ({str(e)})")
                    info_detallada.append(f"{archivo}(error)")
            
            # Crear string compacto con la información
            info_string = f"CSVs[{len(archivos_csv)}]: {', '.join(info_detallada)}"
            print(f"\nResumen: {info_string}")
            
            return len(archivos_csv), info_string
        else:
            return 0, "No se encontraron archivos CSV"
        
    except FileNotFoundError:
        print(f"Error: El directorio {directorio} no existe")
        return 999, "Error: Directorio no encontrado"
    except PermissionError:
        print(f"Error: No tienes permisos para acceder al directorio {directorio}")
        return 999, "Error: Sin permisos"
    except Exception as e:
        print(f"Error inesperado: {e}")
        return 999, f"Error: {str(e)}"

def validar_y_filtrar_archivos(patron_csv):
    """
    Valida los archivos CSV y elimina los inválidos.
    Retorna la lista de archivos válidos.
    """
    todos_archivos = glob.glob(patron_csv)
    
    if Globals.flag_archivos_validos == True: 
        return Globals.archivos
        
    archivos_validos = []
    
    for archivo in todos_archivos:
        # VERIFICACIÓN DE SEGURIDAD ANTES DE PROCESAR
        seguro, razon = es_archivo_seguro_procesar(archivo)
        if not seguro:
            print(f"Saltando archivo {archivo}: {razon}")
            continue
            
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
    
    # Creamos una copia de la lista global para iterar de forma segura
    archivos_a_procesar = list(pending_files_to_send) 
    
    if not archivos_a_procesar:
        print("send_dron_csv: No hay archivos pendientes para procesar.")
        return True, 0

    hostname = urlparse(url).hostname
    
    if not await check_ping(hostname):
        msg = f"No hay conexión con {url}..."
        print(msg)
        logging.warning(msg)
        # Si no hay conexión, la lista no se modifica
        return False, len(pending_files_to_send)
        
    archivos_enviados = []
    archivos_con_error = []
    
    # Procesar archivos uno por uno
    for archivo in archivos_a_procesar:
        if not isinstance(archivo, str) or not os.path.exists(archivo):
            logging.error(f"Valor inválido o archivo no encontrado en la lista de pendientes: {archivo}")
            # Eliminamos el archivo inválido de la lista original
            try:
                pending_files_to_send.remove(archivo)
            except ValueError:
                pass
            continue

        try:
            exito_envio = await send_file(url, archivo)
            if exito_envio:
                archivos_enviados.append(archivo)
                # CRÍTICO: Eliminar el archivo del disco y de la lista SOLO si el envío fue exitoso
                os.remove(archivo)
                pending_files_to_send.remove(archivo)
                logging.info(f"Archivo enviado y eliminado: {archivo}")
            else:
                archivos_con_error.append(archivo)
        except Exception as e:
            logging.error(f"Error procesando {archivo}: {e}")
            archivos_con_error.append(archivo)

    # Resumen de la operación
    if archivos_enviados:
        print(f"Se enviaron y eliminaron exitosamente {len(archivos_enviados)} archivos.")
    if archivos_con_error:
        print(f"No se pudieron enviar {len(archivos_con_error)} archivos.")
        
    exito = len(archivos_con_error) == 0
    #print('archivos_pendientes: ', len(pending_files_to_send))
    return exito, len(pending_files_to_send)
# Función auxiliar para check_init() si la necesitas
def ping_reader():
    """
    Placeholder para la función ping_reader
    Ajusta según tu implementación
    """
    # Implementa aquí tu lógica de ping al lector
    return True  # Por ahora retorna True

def check_init(): 
    """
    Función para verificar el estado inicial del sistema
    """
    # Realizar el ping y enviar el mensaje si es exitoso
    message = ""
    files_count, files_info = pending_files()  # Desempaquetar la tupla
    
    if ping_reader():
        message = (  
            "HOLA!! Sierra Dron encendido\n"
            "Lector de tags OK\n"
            f"Archivos pendientes de enviar: {files_count}\n"
            f"Detalle: {files_info}\n"
            f"Hora de sistema: {time.strftime('%H:%M:%S')}\n")
    else:
        message = (  
            "HOLA!! Sierra Dron con problemas\n"
            "Lector de tags no detectado\n"
            f"Archivos pendientes de enviar: {files_count}\n"
            f"Detalle: {files_info}\n"
            f"Hora de sistema: {time.strftime('%H:%M:%S')}\n")
    
    return message

# Para uso directo del script
if __name__ == '__main__':
    print('FileServices_main()')
    asyncio.run(send_dron_csv())