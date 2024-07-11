import socket
import MessageTran as mt
import RealTimeInventoryResponse as invResponse
import time
import pandas as pd

from Services import MessageService as Sender
from EpcTranslator import EpcTranslator
from Services import FileService as files
from Services import PublisherService as publisher

import logging
import threading

# Configuración básica del logging
logging.basicConfig(
    filename='log/mi_programa.log',  # Ruta al archivo de log
    level=logging.DEBUG,                  # Nivel de logging (puede ser DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s %(levelname)s:%(message)s'  # Formato del log
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

def send_message(btAryTranData):
    # Connection settings to the reader
    ip = '192.168.1.200'  # Reader's IP address
    port = 4001           # Reader's port
    buffer_size = 1024#4096    # Receive buffer size
    timeout = 3
    retries = 3
    delay = 1#0.5
    
    for attempt in range(retries):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(timeout)


        try:
            # Adquirir el bloqueo antes de conectar
            with socket_lock:
                # Conectar al lector
                client_socket.connect((ip, port))
                # Enviar los datos al lector
                client_socket.sendall(btAryTranData)
                # Recibir la respuesta del lector
                response = client_socket.recv(buffer_size)
                # Devolver la respuesta si se recibe correctamente
                return response


        except socket.timeout as st:
            logging.error("Intento %d: socket timeout %s", attempt + 1, st.strerror)
            msg = f"socket.timeout: Intento {attempt + 1}: Error de socket {str(st)}. Reintentando en {delay} segundos..."
            print(msg)
            Sender.srv_printer(msg)
            time.sleep(delay)

        except socket.error as e:
            logging.error("Intento %d: error de socket %s", attempt + 1, e)
            msg = f"socket.error Intento {attempt + 1}: Error de socket {e}. Reintentando en {delay} segundos..."
            print(msg)
            Sender.srv_printer(msg)
            time.sleep(delay)

        finally:
            client_socket.close()

    # Si se alcanzan todos los intentos y aún no hay respuesta, devuelve None
    logging.error("Se han agotado todos los intentos de conexión.")
    print("Se han agotado todos los intentos de conexión.")
    return None
def get_reads():

    while True:
        # Example usage
        btReadId = 0xFF
        btCmd = 0x89
        btAryData = [0x01, 0x02, 0x03, 0x04]
        message = ""
        msgTran = mt.MessageTran(btReadId, btCmd, btAryData)
        time.sleep(1)
        result = send_message(msgTran.AryTranData)
        if(result is None): continue
        if len(result) <= 11:  # Check if the length is less than 4 bytesx 
            print("Incomplete data packet. Continuing with the next iteration.")
            continue

        try:
            # Create an instance of RealTimeInventoryResponse with the received result
            response = invResponse.RealTimeInventoryResponse(result)
            if response.epc_list[0] == b'\x00\x00\x00':
                message = "Valor epc_list contiene b'\\x00\\x00\\x00'. Continuando con la siguiente iteración."
                print(message)
                Sender.srv_printer(message)
                continue
            # Access interpreted fields of the response
            value = response.freq_ant_list[0]  # Example integer value representing bytes
            freq_mhz, antenna_id = calculate_frequency_and_antenna(value)
            pc_list = pc_data(response.pc_list[0])

            epc = EpcTranslator.getData(response.epc_list[0])
            rssi = rssi_data(response.rssi_list[0])

            # Update the EPC data in the dictionary
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


            files.write_file(epc, freq_mhz, antenna_id + 1, pc_list, rssi,  epc_data[epc]['Read Count'])

        except IndexError:
            print("An IndexError occurred. Continuing with the next iteration.")
            
        
        except NameError as e:
            print("send_message>", e)

        except Exception as t:    
            print("send_message>", t)

        # Example of how to end the loop and display the stored data as a table
        if len(epc_data) >= 1:  # You can change this condition as needed
            df = pd.DataFrame.from_dict(epc_data, orient='index')
            #message = df.to_json()
            Sender.srv_printer("Lecturas ok")
            print(df)
            #break

if __name__ == '__main__':
    print("main")
    logging.info('Suscriber Reader start')
    publisher.send_dron_csv()        
    get_reads()
    


    
