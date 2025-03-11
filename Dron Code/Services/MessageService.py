import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

def srv_printer(msg):
    flag = False
    url = f'http://10.185.36.30:5100/printer/{msg}'
    
    # Configurar la estrategia de reintentos
    retry_strategy = Retry(
        total=2,  # número total de reintentos
        backoff_factor=0.5,  # tiempo de espera entre reintentos
        status_forcelist=[500, 502, 503, 504]  # códigos HTTP para reintentar
    )
    
    # Crear una sesión con la configuración de reintentos
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    try:
        # Aumentar el timeout y usar la sesión configurada
        respuesta = session.post(
            url,
            data=msg,
            timeout=(3, 5)  # (tiempo para conectar, tiempo para leer)
        )
        if respuesta.status_code == 201:
            flag = True
            logging.info(f"Solicitud recibida de enviar Inventario Ahora: {msg}")

        if respuesta.status_code == 200:
            flag = True
            logging.info(f"Mensaje enviado exitosamente: {msg}")
        else:
            print(f'Error al enviar el mensaje. Código: {respuesta.status_code}')
            flag = False
            
    except requests.exceptions.ConnectTimeout:
        print(f"Tiempo de conexión agotado al intentar conectar con {url}")
        flag = False
        
    except requests.exceptions.ReadTimeout:
        print(f"Tiempo de lectura agotado mientras se esperaba la respuesta de {url}")
        flag = False
        
    except requests.exceptions.ConnectionError:
        print(f"No se pudo establecer conexión con {url}")
        flag = False
        
    except Exception as e:
        print(f'MessageServices_exception: {str(e)}')
        flag = False
        
    finally:
        session.close()
        return flag