# ==============================================================================
# Módulo principal para el proyecto "Inventario Dron"
#
# Descripción: Este script orquesta el sistema de inventario RFID, gestionando la
# comunicación con un lector RFID, el procesamiento de datos, el almacenamiento
# en archivos CSV, y la comunicación con servicios externos como un servidor
# central y Telegram. Utiliza programación asíncrona (asyncio) para manejar
# múltiples tareas concurrentes de forma eficiente.
# ==============================================================================

# ------------------------------------------------------------------------------
# Importaciones de Módulos Estándar
# ------------------------------------------------------------------------------
import asyncio
import csv
import logging
import os
import threading
from datetime import datetime

# ------------------------------------------------------------------------------
# Importaciones de Módulos de Terceros
# ------------------------------------------------------------------------------
import pandas as pd

# ------------------------------------------------------------------------------
# Importaciones de Módulos del Proyecto 
# ------------------------------------------------------------------------------
from EpcTranslator import EpcTranslator
from RealTimeInventoryResponse import RealTimeInventoryResponse
from Services import FileService as files
from Services import MessageService as Sender
from Services import PublisherService as publisher
from Services import StatusService as status
from Services import TelegramService as telegram
from Services.FileService import AsyncFileWriter
from MessageTran import MessageTran as mt

# ------------------------------------------------------------------------------
# Configuración Global y Logging
# ------------------------------------------------------------------------------

# Configuración básica del logging para registrar eventos en un archivo.
logging.basicConfig(
    filename='/home/sg-sierra-dron/Documents/sierra-dron/sg-rfid-dron/log/mi_programa.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Diccionario para almacenar los datos de las etiquetas EPC leídas.
epc_data = {}

# Bloqueos de sincronización para acceso a recursos compartidos.
socket_lock = asyncio.Lock()  # Bloqueo asíncrono para el socket.
threading_lock = threading.Lock() # Bloqueo para operaciones de hilos (si aplica).

# ------------------------------------------------------------------------------
# Funciones de Utilidad y Transformación de Datos
# ------------------------------------------------------------------------------

def calculate_frequency_and_antenna(value: int) -> tuple[float, int]:
    """
    Calcula la frecuencia y el ID de la antena a partir de un valor entero.

    Args:
        value: El valor entero recibido del lector RFID.

    Returns:
        Una tupla con la frecuencia en MHz y el ID de la antena.
    """
    bytes_data = value.to_bytes(2, byteorder='big')
    int_data = int.from_bytes(bytes_data, byteorder='big')
    
    freq_param = (int_data >> 2) & 0b111111
    antenna_id = int_data & 0b11
    
    freq_mhz = 860 + freq_param
    
    return freq_mhz, antenna_id

def rssi_data(rssi: int) -> int:
    """
    Convierte el valor RSSI (fuerza de la señal) a un formato legible.
    
    Args:
        rssi: El valor RSSI recibido.
        
    Returns:
        El valor RSSI en formato legible.
    """
    return rssi * -1

def pc_data(bytes_data: bytes) -> str:
    """
    Formatea los datos PC (Protocol Control) de una etiqueta RFID.
    
    Args:
        bytes_data: Los datos PC en bytes.
        
    Returns:
        Una cadena formateada con los datos PC en hexadecimal.
    """
    hex_str = bytes_data.hex()
    formatted_str = ' '.join([hex_str[i:i+2] for i in range(0, len(hex_str), 2)])
    return formatted_str

# ------------------------------------------------------------------------------
# Lógica de Comunicación con el Lector RFID
# ------------------------------------------------------------------------------

async def send_message(bt_ary_tran_data: bytes) -> bytes | None:
    """
    Envía un mensaje al lector RFID y espera una respuesta.
    
    Implementa un mecanismo de reintentos con un bloqueo asíncrono para
    garantizar que solo una tarea a la vez acceda al socket.

    Args:
        bt_ary_tran_data: La trama de datos en bytes para enviar.
        
    Returns:
        La respuesta en bytes del lector o None si falla.
    """
    ip = '192.168.1.200'
    port = 4001
    buffer_size = 1024
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
                    writer.write(bt_ary_tran_data)
                    await writer.drain()
                    response = await reader.read(buffer_size)
                    return response
                finally:
                    writer.close()
                    await writer.wait_closed()
        except asyncio.TimeoutError:
            logging.error(f"Intento {attempt + 1}: Timeout del socket.")
        except ConnectionError as e:
            logging.error(f"Intento {attempt + 1}: Error de conexión: {e}")
        except Exception as e:
            logging.error(f"Intento {attempt + 1}: Error inesperado: {e}")
            
        await asyncio.sleep(delay)
        
    logging.error("Se han agotado todos los intentos de conexión.")
    return None

async def write_to_csv(csv_path: str, fieldnames: list[str], data: dict) -> bool:
    """
    Escribe una fila de datos en un archivo CSV de forma asíncrona.
    
    Utiliza una clase auxiliar (`AsyncFileWriter`) para manejar la
    operación de E/S de archivos en un hilo separado, evitando bloquear el
    bucle de eventos principal.

    Args:
        csv_path: La ruta completa del archivo CSV.
        fieldnames: Una lista con los nombres de las columnas.
        data: Un diccionario con los datos a escribir.
        
    Returns:
        True si la escritura fue exitosa, False en caso de error.
    """
    try:
        async with AsyncFileWriter(csv_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            await asyncio.to_thread(writer.writerow, data)
        logging.info(f"Datos escritos exitosamente en CSV para EPC: {data['EPC']}")
        return True
    except Exception as e:
        logging.error(f"Error escribiendo en CSV: {e}")
        return False

async def get_reads():
    """
    Tarea principal para leer etiquetas RFID y procesar sus datos.
    
    Esta función se ejecuta en un bucle infinito, comunicándose con el lector
    RFID, traduciendo los datos de las etiquetas y escribiéndolos en un archivo
    CSV.
    """
    logging.info("Iniciando get_reads...")
    
    flag_first_reader = 0
    read_tags = set()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'files')
    os.makedirs(data_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = os.path.join(data_dir, f'sierradron_lecturas_{timestamp}.csv')
    fieldnames = ['EPC', 'Antenna ID', 'Frequency (MHz)', 'PC List', 'RSSI List', 'Read Count', 'Timestamp', 'Localtime']
    
    while True:
        try:
            bt_read_id = 0xFF
            bt_cmd = 0x89
            bt_ary_data = [0x01, 0x02, 0x03, 0x04]
            msg_tran = mt(bt_read_id, bt_cmd, bt_ary_data)
            
            result = await send_message(msg_tran.AryTranData)
            
            if not result or len(result) <= 11:
                await asyncio.sleep(1)
                continue
            
            response = RealTimeInventoryResponse(result)
            epc_list = response.epc_list
            pc_list = response.pc_list
            rssi_list = response.rssi_list
            freq_ant_list = response.freq_ant_list
            
            for i in range(len(epc_list)):
                epc_bytes = epc_list[i]
                if (epc_bytes == b'\x00\x00\x00' or 
                    len(epc_bytes) < 12 or 
                    len(epc_bytes) > 16):
                    continue
                
                epc = EpcTranslator.getData(epc_bytes)
                freq_mhz, antenna_id = calculate_frequency_and_antenna(freq_ant_list[i])
                pc_list_str = pc_data(pc_list[i])
                rssi = rssi_data(rssi_list[i])
                
                if epc not in read_tags:
                    read_tags.add(epc)
                    logging.info(f"Nueva lectura detectada - EPC: {epc}")
                    
                    if epc not in epc_data:
                        epc_data[epc] = {
                            "Frequency (MHz)": freq_mhz,
                            "Antenna ID": antenna_id + 1,
                            "PC List": pc_list_str,
                            "RSSI List": [rssi],
                            "Read Count": 1
                        }
                    else:
                        epc_data[epc]['Read Count'] += 1
                        epc_data[epc]['RSSI List'].append(rssi)
                    
                    data_to_write = {
                        'EPC': epc,
                        'Antenna ID': epc_data[epc]['Antenna ID'],
                        'Frequency (MHz)': epc_data[epc]['Frequency (MHz)'],
                        'PC List': epc_data[epc]['PC List'],
                        'RSSI List': epc_data[epc]['RSSI List'],
                        'Read Count': epc_data[epc]['Read Count'],
                        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Localtime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                    if flag_first_reader == 0:
                        try:
                            with open(csv_path, 'w', newline='') as f:
                                writer = csv.DictWriter(f, fieldnames=fieldnames)
                                writer.writeheader()
                            logging.info(f"Archivo CSV creado en: {csv_path}")
                            flag_first_reader = 1
                        except Exception as e:
                            logging.error(f"Error creando archivo CSV: {e}")
                    
                    await write_to_csv(csv_path, fieldnames, data_to_write)
                else:
                    if epc in epc_data:
                        epc_data[epc]['Read Count'] += 1
                        epc_data[epc]['RSSI List'].append(rssi)

            if len(epc_data) >= 1:
                df = pd.DataFrame.from_dict(epc_data, orient='index')
                logging.debug("DataFrame de lecturas:\n%s", df.to_string())

        except Exception as e:
            logging.error(f"Error en ciclo principal: {e}")
            await asyncio.sleep(1)

# ------------------------------------------------------------------------------
# Lógica de Servicios y Sistema
# ------------------------------------------------------------------------------

class AsyncFileWriter:
    """
    Clase de contexto asíncrona para manejar la escritura en archivos.

    Esta clase permite que las operaciones de E/S de archivos se realicen en un
    hilo separado (`asyncio.to_thread`), evitando bloquear el bucle de eventos
    de asyncio.

    Args:
        filename: La ruta del archivo a abrir.
        mode: El modo de apertura del archivo (ej. 'w', 'a').
        **kwargs: Argumentos adicionales para la función `open()`.
    """
    def __init__(self, filename, mode='w', **kwargs):
        self.filename = filename
        self.mode = mode
        self.kwargs = kwargs
        self.file = None

    async def __aenter__(self):
        """Abre el archivo en un hilo separado."""
        await asyncio.to_thread(self._open_file)
        return self.file

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cierra el archivo en un hilo separado."""
        await asyncio.to_thread(self._close_file)

    def _open_file(self):
        """Función interna para abrir el archivo de forma síncrona."""
        self.file = open(self.filename, self.mode, **self.kwargs)

    def _close_file(self):
        """Función interna para cerrar el archivo de forma síncrona."""
        if self.file:
            self.file.close()

async def check_network_status():
    """
    Verifica el estado actual de la red Wi-Fi.

    Returns:
        Una tupla con el nombre de la red Wi-Fi y la información de la red.
    """
    wifi_info = await asyncio.to_thread(status.get_wifi_name)
    network_info = await asyncio.to_thread(status.get_network_info)
    return wifi_info, network_info

async def send_heartbeat():
    """
    Envía un mensaje de 'heartbeat' a través del servicio de mensajes.
    """
    await asyncio.to_thread(Sender.srv_printer, "hb_sierra_dron")

async def send_periodic_message():
    """
    Tarea asíncrona para enviar mensajes de estado periódicamente.
    
    Envía un heartbeat, verifica el estado de la red (cada 5 minutos) y
    procesa los archivos pendientes, enviando un mensaje de estado a Telegram.
    """
    network_check_interval = 300
    heartbeat_interval = 30
    last_network_check = 0
    archivos_pendientes = None
    while True:
        try:
            current_time = datetime.now().timestamp()
            
            if current_time - last_network_check >= network_check_interval:
                network_task = asyncio.create_task(check_network_status())
                last_network_check = current_time
            
            await send_heartbeat()

            result, archivos_pendientes = await publisher.send_dron_csv()
            
            msg_ = (f"send_dron_csv: {str(result)} - "
                    f"{'Sin' if not archivos_pendientes else len(archivos_pendientes)} "
                    f"archivos pendientes").replace(" ", "_")
            
            await asyncio.to_thread(Sender.srv_printer, msg_)

        except Exception as e:
            logging.error(f"error_ send_periodic_message:{e}")
        
        await asyncio.sleep(heartbeat_interval)

async def initialize_system() -> bool:
    """
    Inicializa el sistema verificando el estado de la red y enviando un
    mensaje de inicio a través de Telegram.
    
    Returns:
        True si la inicialización fue exitosa, False en caso contrario.
    """
    try:
        txt, wifi_check = status.get_wifi_name()
        info = status.get_network_info()
        system_hour = status.get_time()
        
        red_wifi = f"Red WiFi: {info['wifi']}"
        ip_wifi = f"Direccion IP: {info['ip']}"
        
        await asyncio.gather(
            asyncio.to_thread(Sender.srv_printer, red_wifi.replace(" ", "_")),
            asyncio.to_thread(Sender.srv_printer, ip_wifi.replace(" ", "_")),
            asyncio.to_thread(Sender.srv_printer, system_hour.replace(" ", "_"))
        )
        return True
    except Exception as e:
        logging.error(f"Error en inicialización: {e}")
        return False

async def main():
    """
    Función principal que orquesta la ejecución de todas las tareas asíncronas.
    
    Llama a la función de inicialización del sistema y luego ejecuta las
    tareas principales de forma concurrente, gestionando cualquier cancelación
    o error.
    """
    logging.info("Iniciando sistema...")
    
    init_success = await initialize_system()
    if not init_success:
        logging.error("Fallo en la inicialización del sistema")
        return
    
    try:
        task1 = asyncio.create_task(send_periodic_message())
        task2 = asyncio.create_task(get_reads())
        
        await asyncio.gather(task2, task1)
        
    except asyncio.CancelledError:
        logging.info("Tareas canceladas")
    except Exception as e:
        logging.error(f"Error en las tareas principales: {e}")
    finally:
        for task in asyncio.all_tasks():
            if task is not asyncio.current_task():
                task.cancel()
        
    logging.info("Finalizando programa...")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logging.critical(f"Error crítico en el bucle principal: {e}")