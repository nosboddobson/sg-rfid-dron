import socket
import MessageTran as mt
import RealTimeInventoryResponse as invResponse
import time
from EpcTranslator import EpcTranslator

# Crear un diccionario para almacenar los EPC y su contador
epc_counts = {}

def calculate_frequency_and_antenna(value):
       # Convertir el entero en bytes
    bytes_data = value.to_bytes(2, byteorder='big')

    # Convertir bytes_data a un entero
    int_data = int.from_bytes(bytes_data, byteorder='big')

    # Obtener el parámetro de frecuencia y el ID de la antena
    freq_param = (int_data >> 2) & 0b111111  # Obtener los 6 bits más altos
    antenna_id = int_data & 0b11  # Obtener los 2 bits más bajos

    # Calcular la frecuencia en MHz y ajustarla según sea necesario
    freq_mhz = 860 + (freq_param)

    return freq_mhz, antenna_id

def rssi_data(rssi):
    r = rssi
    return r*-1

def pc_data(bytes_data):
    # Convertir los bytes a una cadena hexadecimal
    hex_str = bytes_data.hex()

    # Separar la cadena hexadecimal en grupos de dos caracteres
    formatted_str = ' '.join([hex_str[i:i+2] for i in range(0, len(hex_str), 2)])

    return formatted_str


def send_message(btAryTranData):
    # Configuración de la conexión al lector
    ip = '192.168.1.200'  # Dirección IP del lector
    port = 4001           # Puerto del lector
    buffer_size = 4096    # Tamaño del buffer de recepción

    # Crear un socket TCP/IP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Conectar al lector
        client_socket.connect((ip, port))

        # Enviar los datos al lector
        client_socket.sendall(btAryTranData)

        # Recibir la respuesta del lector
        response = client_socket.recv(buffer_size)

        # Procesar la respuesta (código de respuesta, datos, etc.)
        # En este ejemplo, simplemente se devuelve la respuesta como está
        return response

    finally:
        # Cerrar la conexión
        client_socket.close()

if __name__ == '__main__':
    print("main")
    while 1==1:
        # Ejemplo de uso
        btReadId = 0xFF
        btCmd = 0x89
        btAryData = [0x01, 0x02, 0x03, 0x04]

        msgTran = mt.MessageTran(btReadId, btCmd, btAryData)
        time.sleep(0.5)
        result = send_message(msgTran.AryTranData)
        if len(result) <= 10:  # Comprobar si la longitud es menor que 4 bytes
            print("Paquete de datos incompleto. Continuando con la próxima iteración.")
            continue
        try:
            # Crear una instancia de RealTimeInventoryResponse con el resultado recibido
            response = invResponse.RealTimeInventoryResponse(result)

            # Acceder a los campos interpretados de la respuesta
            print("btPacketType:", response.btPacketType)
            print("btDataLen:", response.btDataLen)
            print("btReadId:", response.btReadId)
            print("btCmd:", hex(response.btCmd))
            value = response.freq_ant_list[0]  # Ejemplo de valor entero que representa los bytes
            freq_mhz, antenna_id = calculate_frequency_and_antenna(value)
            print(f"Frecuencia en MHz: {freq_mhz}, ID de Antena: {antenna_id+1}")
            print("PC List:",  pc_data(response.pc_list[0])) #"response.pc_list"
        
            epc = EpcTranslator.getData(response.epc_list[0])
            print("EPC List:", epc)
            print("RSSI List:", rssi_data(response.rssi_list[0]))
            print("-------")

            # Incrementar el contador del EPC en el diccionario
            if epc in epc_counts:
                epc_counts[epc] += 1
            else:
                epc_counts[epc] = 1
            if epc == "00":
                a = 1
            # Imprimir el contador actualizado del EPC
            print(f"Veces leído: {epc_counts[epc]}")
        except IndexError:
            print("Ocurrió un IndexError. Continuando con la próxima iteración.")
            continue
 