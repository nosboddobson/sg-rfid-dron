import socket
import MessageTran as mt
import RealTimeInventoryResponse as invResponse
import time
import pandas as pd
import asyncio 
import csv
from datetime import datetime
import os
from Services import StatusService as status
from Services import TelegramService as telegram
from Services import MessageService as Sender
from EpcTranslator import EpcTranslator
from Services import FileService as files
from Services import PublisherService as publisher
from Services.FileService import AsyncFileWriter
import logging
import threading
from functools import partial
# Configuración básica del logging
logging.basicConfig(
    filename='/home/sg-sierra-dron/Documents/sierra-dron/sg-rfid-dron/log/mi_programa.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Crear un bloqueo global
socket_lock = threading.Lock()
# Create a dictionary to store EPC and its details
epc_data = {}

def calculate_frequency_and_antenna(value):
    # Convert the integer to bytes
    bytes_data = value.to_bytes(2, byteorder='big')

    # Convert bytes_data to an integer
    int_data = int.from_bytes(bytes_data, byteorder='big')

    # Get the frequency parameter and antenna ID
    freq_param = (int_data >> 2) & 0b111111  # Get the highest 6 bits
    antenna_id = int_data & 0b11  # Get the lowest 2 bits

    # Calculate the frequency in MHz and adjust as needed
    freq_mhz = 860 + freq_param

    return freq_mhz, antenna_id

def rssi_data(rssi):
    return rssi * -1

def pc_data(bytes_data):
    # Convert the bytes to a hexadecimal string
    hex_str = bytes_data.hex()

    # Separate the hexadecimal string into groups of two characters
    formatted_str = ' '.join([hex_str[i:i+2] for i in range(0, len(hex_str), 2)])

    return formatted_str

socket_lock = asyncio.Lock()

async def send_message(btAryTranData):
    # Connection settings to the reader
    ip = '192.168.1.200'  # Reader's IP address
    port = 4001           # Reader's port
    buffer_size = 1024    # Receive buffer size
    timeout = 3
    retries = 3
    delay = 0.3
    
    for attempt in range(retries):
        try:
            async with socket_lock:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=timeout
                )

                try:
                    writer.write(btAryTranData)
                    await writer.drain()
                    response = await reader.read(buffer_size)
                    return response

                finally:
                    writer.close()
                    await writer.wait_closed()

        except asyncio.TimeoutError as st:
            logging.error("Intento %d: socket timeout", attempt + 1)
            msg = f"asyncio.TimeoutError: Intento {attempt + 1}: Timeout. Reintentando en {delay} segundos..."
            print(msg)

        except ConnectionError as e:
            logging.error("Intento %d: error de conexión %s", attempt + 1, str(e))
            msg = f"ConnectionError: Intento {attempt + 1}: Error de conexión {str(e)}. Reintentando en {delay} segundos..."
            print(msg)

        except Exception as e:
            logging.error("Intento %d: error inesperado %s", attempt + 1, str(e))
            msg = f"Error inesperado: Intento {attempt + 1}: {str(e)}. Reintentando en {delay} segundos..."
            print(msg)

        await asyncio.sleep(delay)

    logging.error("Se han agotado todos los intentos de conexión.")
    print("Se han agotado todos los intentos de conexión.")
    return None

async def write_to_csv(csv_path, fieldnames, data):
    """Función asíncrona dedicada para escribir en el CSV"""
    try:
        async with AsyncFileWriter(csv_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            await asyncio.to_thread(writer.writerow, data)
        print(f"Datos escritos exitosamente en CSV para EPC: {data['EPC']}")
        return True
    except Exception as e:
        print(f"Error escribiendo en CSV: {e}")
        logging.error(f"Error escribiendo en CSV: {e}")
        return False

async def get_reads():
    print("Iniciando get_reads...")

    flag_first_reader = 0
    read_tags = set()
    
    # Configuración inicial del CSV
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'files')
    os.makedirs(data_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = os.path.join(data_dir, f'sierradron_lecturas_{timestamp}.csv')
    fieldnames = ['EPC', 'Antenna ID', 'Frequency (MHz)', 'PC List', 'RSSI List', 'Read Count', 'Timestamp', 'Localtime']
    
    # Escribir headers
    # Escribir headers
    
    
    while True:
        try:
            btReadId = 0xFF
            btCmd = 0x89
            btAryData = [0x01, 0x02, 0x03, 0x04]
            msgTran = mt.MessageTran(btReadId, btCmd, btAryData)
            
            result = await send_message(msgTran.AryTranData)
            if not result or len(result) <= 11:
                continue

            response = invResponse.RealTimeInventoryResponse(result)
            if (response.epc_list[0] == b'\x00\x00\x00' or 
                len(response.epc_list[0]) < 12 or 
                len(response.epc_list[0]) > 16):
                continue

            value = response.freq_ant_list[0]
            freq_mhz, antenna_id = calculate_frequency_and_antenna(value)
            pc_list = pc_data(response.pc_list[0])
            epc = EpcTranslator.getData(response.epc_list[0])
            rssi = rssi_data(response.rssi_list[0])

            if epc not in read_tags:
                read_tags.add(epc)
                print(f"Nueva lectura detectada - EPC: {epc}")
                
                # Actualizar epc_data
                if epc in epc_data:
                    epc_data[epc]['Read Count'] += 1
                    epc_data[epc]['RSSI List'] = rssi
                else:
                    epc_data[epc] = {
                        "Frequency (MHz)": freq_mhz,
                        "Antenna ID": antenna_id + 1,
                        "PC List": pc_list,
                        "RSSI List": rssi,
                        "Read Count": 1
                    }
                    tag = epc_data[epc]
                
                # Preparar datos para CSV
                data = {
                    'EPC': epc,
                    'Antenna ID': antenna_id + 1,
                    'Frequency (MHz)': freq_mhz,
                    'PC List': pc_list,
                    'RSSI List': rssi,
                    'Read Count': epc_data[epc]['Read Count'],
                    'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Localtime': datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Nueva columna
                }
                if(flag_first_reader==0):
                    try:
                        with open(csv_path, 'w', newline='') as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                        print(f"Archivo CSV creado en: {csv_path}")
                        flag_first_reader = 1
                    except Exception as e:
                        print(f"Error creando archivo CSV: {e}")
                        logging.error(f"Error creando archivo CSV: {e}")
                        
                # Escribir en CSV de manera asíncrona
                await write_to_csv(csv_path, fieldnames, data)
            else:
                epc_data[epc]['Read Count'] += 1
                epc_data[epc]['RSSI List'] = rssi

            if len(epc_data) >= 1:
                df = pd.DataFrame.from_dict(epc_data, orient='index')
                print(df)

        except Exception as e:
            print(f"Error en ciclo principal: {e}")
            logging.error(f"Error en ciclo principal: {e}")
            await asyncio.sleep(1)  # Evitar ciclos de error rápidos

# Clase auxiliar para manejar archivos de manera asíncrona
class AsyncFileWriter:
    def __init__(self, filename, mode='w', **kwargs):
        self.filename = filename
        self.mode = mode
        self.kwargs = kwargs
        self.file = None

    async def __aenter__(self):
        await asyncio.to_thread(self._open_file)
        return self.file

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.to_thread(self._close_file)

    def _open_file(self):
        self.file = open(self.filename, self.mode, **self.kwargs)

    def _close_file(self):
        if self.file:
            self.file.close()

async def check_network_status():
    """Función separada para verificar el estado de la red"""
    wifi_info = await asyncio.to_thread(status.get_wifi_name)
    network_info = await asyncio.to_thread(status.get_network_info)
    return wifi_info, network_info

async def send_heartbeat():
    """Función separada para enviar heartbeat"""
    await asyncio.to_thread(Sender.srv_printer, "hb_sierra_dron")

async def send_periodic_message():
    network_check_interval = 300  # Verificar red cada 5 minutos
    heartbeat_interval = 30       # Heartbeat cada 30 segundos
    last_network_check = 0
    archivos_pendientes = None
    while True:
        try:
            current_time = datetime.now().timestamp()
            
            # Verificar red solo cada 5 minutos
            if current_time - last_network_check >= network_check_interval:
                # Crear una tarea separada para la verificación de red
                network_task = asyncio.create_task(check_network_status())
                last_network_check = current_time
            
            # Enviar heartbeat
            await send_heartbeat()

            # Esta llamada ya es asíncrona y es tu operación principal
            result, archivos_pendientes = await publisher.send_dron_csv()
            
            # Preparar y enviar mensaje de resultado
            msg_ = (f"send_dron_csv: {str(result)} - "
                   f"{'Sin' if not archivos_pendientes else len(archivos_pendientes)} "
                   f"archivos pendientes").replace(" ", "_")
            print(msg_)
            
            # Enviar mensaje de forma asíncrona
            await asyncio.to_thread(Sender.srv_printer, msg_)

        except Exception as e:
            print(f"error_ send_periodic_message:{e}")
        
        await asyncio.sleep(heartbeat_interval)

async def initialize_system():
    """Función asíncrona para inicializar el sistema"""
    try:
        # Obtener información del sistema
        txt, wifi_check = status.get_wifi_name()
        info = status.get_network_info()
        system_hour = status.get_time()
        
        # Preparar mensajes
        red_wifi = f"Red WiFi: {info['wifi']}"
        ip_wifi = f"Direccion IP: {info['ip']}"
        
        # Enviar información inicial
        await asyncio.gather(
            asyncio.to_thread(Sender.srv_printer, red_wifi.replace(" ", "_")),
            asyncio.to_thread(Sender.srv_printer, ip_wifi.replace(" ", "_")),
            asyncio.to_thread(Sender.srv_printer, system_hour.replace(" ", "_"))
        )
        
        return True
    except Exception as e:
        print(f"Error en inicialización: {e}")
        return False

async def main():
    print("Iniciando sistema...")
    
    # Inicializar el sistema de manera asíncrona
    init_success = await initialize_system()
    if not init_success:
        print("Fallo en la inicialización del sistema")
        return
    
    try:
        # Crear y ejecutar las tareas principales
        task1 = asyncio.create_task(send_periodic_message())
        task2 = asyncio.create_task(get_reads())
        
        # Ejecutar las tareas en paralelo
        await asyncio.gather(task2, task1)
        
    except asyncio.CancelledError:
        print("Tareas canceladas")
    except Exception as e:
        print(f"Error en las tareas principales: {e}")
    finally:
        # Asegurar que las tareas se limpien adecuadamente
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()

if __name__ == '__main__':
    try:
        # Ejecutar el loop de eventos principal
        asyncio.run(main())
 
    except Exception as e:
        print(f"Error crítico: {e}")
    finally:
        # Limpiar recursos si es necesario
        print("Finalizando programa...")