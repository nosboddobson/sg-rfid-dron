# ==============================================================================
# Módulo: StatusService.py
#
# Descripción:
# Este módulo proporciona funciones para obtener información de estado del
# sistema y de la red. Las funciones aquí definidas permiten consultar la
# hora actual, el nombre de la red Wi-Fi a la que se está conectado y la
# dirección IP local del dispositivo.
# ==============================================================================

# ------------------------------------------------------------------------------
# Importaciones de Módulos
# ------------------------------------------------------------------------------
import subprocess
import socket
import time 

def get_time() -> str:
    """
    Obtiene la hora actual del sistema en un formato de cadena.

    Returns:
        str: Una cadena de texto con la hora del sistema en formato
             "Hora de sistema: HH:MM:SS".
    """
    message = f"Hora de sistema: {time.strftime('%H:%M:%S')}"
    return message

def get_network_info() -> dict:
    """
    Obtiene el nombre de la red Wi-Fi y la dirección IP local del dispositivo.

    Utiliza `subprocess` para ejecutar un comando de sistema para el nombre
    de la red y un `socket` para determinar la IP local.

    Returns:
        dict: Un diccionario con la siguiente información:
              - "wifi": El nombre de la red Wi-Fi o un mensaje de error.
              - "ip": La dirección IP local o un mensaje de error.
              - "success": Un booleano que indica si la operación fue exitosa.
    """
    try:
        # Obtener nombre de la red Wi-Fi
        wifi_name = subprocess.check_output(["iwgetid", "-r"]).decode("utf-8").strip()
        
        # Obtener la dirección IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Conecta a Google DNS para obtener la IP de la interfaz
        ip_address = s.getsockname()[0]
        s.close()
        
        return {
            "wifi": wifi_name,
            "ip": ip_address,
            "success": True
        }
        
    except Exception as e:
        return {
            "wifi": "No se pudo determinar la red Wi-Fi",
            "ip": "No se pudo determinar la IP",
            "success": False
        }

def get_wifi_name() -> tuple[str, bool]:
    """
    Obtiene el nombre de la red Wi-Fi del dispositivo.

    Ejecuta el comando `iwgetid -r` para obtener el SSID de la red.

    Returns:
        tuple[str, bool]: Una tupla que contiene:
                          - Una cadena de texto con el nombre de la red o un
                            mensaje de error.
                          - Un booleano que indica si la operación fue exitosa.
    """
    try:
        result = subprocess.check_output(["iwgetid", "-r"]).decode("utf-8").strip()
        if result:
            return "Wifi: " + result, True
    
        return "No se pudo determinar la red Wi-Fi", False
    except Exception as t:    
        return "No se pudo determinar la red Wi-Fi", False
    
# ------------------------------------------------------------------------------
# Bloque de Ejecución para Pruebas
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Bloque principal para ejecutar y probar las funciones del módulo
    cuando se ejecuta directamente.
    """
    print("--- Verificando estado del sistema ---")
    
    # Obtener y mostrar la hora del sistema
    print(get_time())
    
    # Obtener y mostrar la información de la red
    network_info = get_network_info()
    print(f"Información de la red: {network_info}")
    
    # Obtener y mostrar el nombre de la red Wi-Fi
    wifi_name_message, is_success = get_wifi_name()
    print(f"Estado de la conexión Wi-Fi: {wifi_name_message}")