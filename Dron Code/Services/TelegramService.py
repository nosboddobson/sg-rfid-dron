# ==============================================================================
# Módulo: TelegramService.py
#
# Descripción:
# Este módulo facilita la comunicación con un bot de Telegram para enviar
# mensajes de estado y alertas. Incluye funciones para verificar la
# conectividad de un lector RFID mediante un comando `ping` y para enviar
# mensajes a un chat de Telegram predefinido.
# ==============================================================================

# ------------------------------------------------------------------------------
# Importaciones de Módulos
# ------------------------------------------------------------------------------

import subprocess
import platform
import time
import logging

# ------------------------------------------------------------------------------
# Constantes de Configuración
# ------------------------------------------------------------------------------

# Token del bot de Telegram. Se recomienda mantener esto en un archivo de
# configuración o variable de entorno por seguridad.
BOT_TOKEN = "7318540437:AAEhw66qJhjOUWNHCXwYirSA1QbNZoZxP7Y"

# ID del chat de Telegram al que se enviarán los mensajes.
CHAT_ID = "-1002179215730"

def ping_reader() -> bool:
    """
    Verifica la conectividad con el lector RFID mediante un comando ping.

    Este método construye y ejecuta un comando de ping adaptado al sistema
    operativo (Windows o Linux) y verifica si la respuesta es exitosa.

    Returns:
        bool: `True` si el lector responde al ping, `False` en caso contrario.
    """
    host = "192.168.1.200"
    
    # Parámetro para el número de paquetes según el sistema operativo
    param = '-n' if platform.system().lower() == 'windows' else '-c'

    # Construir el comando. Ejemplo: "ping -c 1 192.168.1.200"
    command = ['ping', param, '1', host]

    # subprocess.call retorna 0 si el comando fue exitoso
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def send_telegram_message(message: str):
    """
    Envía un mensaje de texto a un chat de Telegram.

    Utiliza el token del bot y el ID del chat definidos en las constantes
    para construir la URL de la API de Telegram y enviar el mensaje.

    Args:
        message (str): El mensaje de texto a enviar.
    """
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }
        
        # Nota: La llamada a `requests.post` está comentada en el código
        # original. Si se habilita, la función enviará el mensaje
        # y retornará la respuesta de la API.
        # response = requests.post(url, json=payload)
        # logging.info(f"Mensaje de Telegram enviado. Respuesta: {response.json()}")
        # return response.json()
        
        # Simulación de la respuesta si la llamada está comentada
        logging.info(f"Simulando el envío de mensaje a Telegram: '{message}'")
        
    except Exception as t:    
        logging.error(f"Error al enviar el mensaje de Telegram: {t}")
        
    
def check_init(): 
    """
    Verifica el estado inicial del sistema y envía un mensaje de alerta.

    Esta función primero hace un ping al lector RFID. Si el ping es exitoso,
    construye un mensaje de estado "OK". Si falla, construye un mensaje de
    alerta. Finalmente, llama a `send_telegram_message` con el mensaje
    correspondiente.
    """
    message = ""
    if ping_reader():
        message = ( 
            "HOLA!! Sierra Dron encendido\n"
            "Lector de tags OK\n"
            f"Hora de sistema: {time.strftime('%H:%M:%S')}\n")
    else:
        message = ( 
            "HOLA!! Sierra Dron con problemas\n"
            "Lector de tags no detectado\n"
            f"Hora de sistema: {time.strftime('%H:%M:%S')}\n")

    send_telegram_message(message)

# ------------------------------------------------------------------------------
# Bloque de Ejecución para Pruebas
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Bloque principal para ejecutar el script directamente, con el fin de
    verificar la lógica de inicialización y envío de mensajes.
    """
    logging.basicConfig(level=logging.INFO)
    print("--- Verificando y enviando estado de inicialización ---")
    check_init()
    print("--- Finalizado ---")