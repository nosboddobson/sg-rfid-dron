import requests
import subprocess
import platform
import time
import os

BOT_TOKEN = "7318540437:AAEhw66qJhjOUWNHCXwYirSA1QbNZoZxP7Y"
CHAT_ID = "-1002179215730"  # Reemplaza esto con tu chat_id real

def ping_reader():
    """
    Returns True if host responds to a ping request
    """
    host = "192.168.1.200"
    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def pending_files():
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

def send_telegram_message(message):
    try:
        bot_token = BOT_TOKEN
        chat_id = CHAT_ID
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        print(url)
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as t:    
        return f"{t}"
    
   



def check_init(): 
    # Realizar el ping y enviar el mensaje si es exitoso
    message = ""
    _, files_info = pending_files()  # Solo usar la información detallada
    
    if ping_reader():
        message = (  
            "HOLA!! Sierra Dron encendido\n"
            "Lector de tags OK\n"
            f"Archivos pendientes: {files_info}\n"
            f"Hora de sistema: {time.strftime('%H:%M:%S')}\n")
    else:
        message = (  
            "HOLA!! Sierra Dron con problemas\n"
            "Lector de tags no detectado\n"
            f"Archivos pendientes: {files_info}\n"
            f"Hora de sistema: {time.strftime('%H:%M:%S')}\n")
    

    result = send_telegram_message(message)
    print(result)