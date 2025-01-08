import requests
import subprocess
import platform
import time

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
        #response = requests.post(url, json=payload)
        #return response.json()
    except Exception as t:    
        return f"{t}"
    
   



def check_init(): 
    # Realizar el ping y enviar el mensaje si es exitoso
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



    result = send_telegram_message(message)
    print(result)