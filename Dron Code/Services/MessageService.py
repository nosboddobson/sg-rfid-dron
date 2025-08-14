# ==============================================================================
# Módulo: messageService.py
#
# Descripción:
# Este módulo contiene funciones para comunicarse con un servicio externo
# de mensajería o impresión a través de una API REST. La función principal
# `srv_printer` o heartBeat envía un mensaje HTTP POST a una URL específica, implementando
# una estrategia de reintentos robusta y manejo de excepciones para garantizar
# la fiabilidad de la comunicación.
# ==============================================================================

# ------------------------------------------------------------------------------
# Importaciones de Módulos
# ------------------------------------------------------------------------------
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

def srv_printer(msg: str) -> bool:
    """
    Envía un mensaje a un servicio de impresión/mensajería a través de una
    solicitud HTTP POST.

    Esta función configura una sesión de `requests` con una política de
    reintentos para manejar fallos de conexión temporales y errores del
    servidor. Se espera una respuesta con códigos de estado 200 (OK) o 201
    (Creado) para considerar el envío exitoso.

    Args:
        msg (str): El mensaje a enviar. Este se usa como parte de la URL
                   y como cuerpo de la solicitud.

    Returns:
        bool: `True` si el mensaje se envió y se recibió una respuesta exitosa
              (código 200 o 201), `False` en caso contrario.
    """
    flag = False
    url = f'http://10.185.36.30:5100/printer/{msg}'
    
    # --------------------------------------------------------------------------
    # Configuración de Reintentos y Sesión HTTP
    # --------------------------------------------------------------------------
    
    # Configurar la estrategia de reintentos para manejar fallos temporales
    retry_strategy = Retry(
        total=2,                         # Número total de reintentos
        backoff_factor=0.5,              # Tiempo de espera entre reintentos (0.5s, 1s)
        status_forcelist=[500, 502, 503, 504]  # Códigos de estado HTTP que disparan un reintento
    )
    
    # Crear una sesión para aplicar la configuración de reintentos
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # --------------------------------------------------------------------------
    # Lógica de la Solicitud HTTP
    # --------------------------------------------------------------------------
    try:
        # Enviar la solicitud POST con la sesión configurada y un timeout
        respuesta = session.post(
            url,
            data=msg,
            timeout=(3, 5)  # Timeout: 3s para conectar, 5s para leer la respuesta
        )
        
        # Validar la respuesta del servidor
        if respuesta.status_code == 201:
            flag = True
            logging.info(f"Solicitud recibida para enviar Inventario: {msg}")
        elif respuesta.status_code == 200:
            flag = True
            logging.info(f"Mensaje enviado exitosamente: {msg}")
        else:
            logging.error(f'Error al enviar el mensaje. Código: {respuesta.status_code}')
            flag = False
            
    # --------------------------------------------------------------------------
    # Manejo de Excepciones
    # --------------------------------------------------------------------------
    except requests.exceptions.ConnectTimeout:
        logging.error(f"Tiempo de conexión agotado al intentar conectar con {url}")
        flag = False
        
    except requests.exceptions.ReadTimeout:
        logging.error(f"Tiempo de lectura agotado mientras se esperaba la respuesta de {url}")
        flag = False
        
    except requests.exceptions.ConnectionError:
        logging.error(f"No se pudo establecer conexión con {url}")
        flag = False
        
    except Exception as e:
        logging.critical(f'MessageServices_exception: {str(e)}')
        flag = False
        
    finally:
        # Asegurar que la sesión se cierre para liberar recursos
        session.close()
        return flag