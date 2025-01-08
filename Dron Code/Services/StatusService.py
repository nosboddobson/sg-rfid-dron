import subprocess
import re
import platform
import socket
import time 
def get_time():

        message = f"Hora de sistema: {time.strftime('%H:%M:%S')}"
        return message

def get_network_info():
    try:
        # Obtener nombre de la red WiFi
        wifi_name = subprocess.check_output(["iwgetid", "-r"]).decode("utf-8").strip()
        
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Conecta a Google DNS (no envía datos realmente)
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

def get_wifi_name():
    try:
        result = subprocess.check_output(["iwgetid", "-r"]).decode("utf-8").strip()
        if result:
            return "Wifi: " + result, True
    
        return "No se pudo determinar la red Wi-Fi", False
    except Exception as t:    
        return "No se pudo determinar la red Wi-Fi", False
    

if __name__ == "__main__":
    wifi_name = get_wifi_name()
    print(f"Estás conectado a la red Wi-Fi: {wifi_name}")