import socket
import requests

def srv_printer(msg):
    flag = False
    url = 'http://10.185.36.30:5100/printer/'+msg
    # Enviar el archivo CSV a un servidor remoto
    try:
        a = 1
        respuesta = requests.post(url, msg, timeout=3)
        if respuesta.status_code == 200:
            flag = True
        else:
            print(f'Error al enviar el archivo: {respuesta.status_code}')
            flag = False
    except Exception as e:
        print('catch except___', e)

    finally:
        print('srv_printer')