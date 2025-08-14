import csv
import os
import pytz
from datetime import datetime

class AsyncFileWriter:
    @staticmethod
    def create_new_file():
        try:
            # Crear el directorio data si no existe
            data_dir = 'data'
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # Crear nombre de archivo con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(data_dir, f'lecturas_{timestamp}.csv')
            
            # Crear el archivo con headers
            fieldnames = ['EPC', 'Antenna ID', 'Frequency (MHz)', 'PC List', 'RSSI List', 'Read Count', 'Timestamp', 'LocalTime']
            with open(log_file, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
            
            print(f"Archivo creado: {log_file}")
            return AsyncFileWriter(log_file)
        except Exception as e:
            print(f"Error creando archivo: {e}")
            return None

    def __init__(self, log_file):
        self.log_file = log_file
        self.fieldnames = ['EPC', 'Antenna ID', 'Frequency (MHz)', 'PC List', 'RSSI List', 'Read Count', 'Timestamp', 'LocalTime']

    async def write_file(self, epc, freq_mhz, antenna_id, pc_list, rssi, read_count):
        try:
            data = {
                'EPC': epc,
                'Antenna ID': antenna_id,
                'Frequency (MHz)': freq_mhz,
                'PC List': pc_list,
                'RSSI List': rssi,
                'Read Count': read_count,
                'Timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'LocalTime': datetime.now(pytz.timezone('America/Santiago')).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(self.log_file, 'a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writerow(data)
            print(f"Datos escritos para EPC: {epc}")
            return True
        except Exception as e:
            print(f"Error escribiendo en archivo: {e}")
            return False

    async def close(self):
        # No es necesario cerrar explícitamente ya que abrimos/cerramos en cada escritura
        pass

def local_time():
    utc_now = datetime.now()
    chile_tz = pytz.timezone('America/Santiago')
    local_time = utc_now.astimezone(chile_tz)
    return local_time.strftime('%Y-%m-%d %H:%M:%S')

def utc_timestamp():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')