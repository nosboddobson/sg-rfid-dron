import requests
from Services import FileService as fs

def send_dron_csv():
    flag = False
    url = 'http://10.185.36.30:5000/upload'
    nombre_archivo = 'C:\\Users\\patri\\source\\repos\\rfid-patio\\files\\epc_records.csv'
    # Enviar el archivo CSV a un servidor remoto
    with open(nombre_archivo, 'rb') as archivo_csv:
        archivos = {'file': (nombre_archivo, archivo_csv)}
        respuesta = requests.post(url, files=archivos)
        if respuesta.status_code == 200:
            print(f'Archivo {nombre_archivo} enviado exitosamente.')
            fs.make_csv()
            flag = True
        else:
            print(f'Error al enviar el archivo: {respuesta.status_code}')
            flag = False
    
    return flag

if __name__ == '__main__':
    print('FileServices_main()')
    send_dron_csv()