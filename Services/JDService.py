import datetime
import time
from typing import Tuple
import requests
import json
import os

from dotenv import load_dotenv
import pandas as pd



load_dotenv(override=True)

'''
Generar_Conteo function performs a count generation operation for a specific warehouse location.
Parameters:
- Sucursal: Represents the warehouse for the count (Mina or Planta).
- Ubicacion: Corresponds to the rack, shelf, or patio.
Response:

{
    "ServiceRequest1": {
        "reportName": "R5541411",
        "reportVersion": "SG0002",
        "jobNumber": 23289,
        "executionServer": "KWJDEAPP61"
    }
}

Returns:
- "OK" if the count generation is successful, None otherwise.
'''
def Generar_Conteo (Sucursal: str,Ubicacion: str)  -> Tuple[str, str]:

    #Sucursal Representa la Bodeha para realizar el conteo Mina o Planta
    #Ubicacion cooresponde al rack, estanteria o Patio.

    max_retries=3

    # Obtener la fecha y hora actual
    ahora = datetime.datetime.now()

    # Formatear la fecha y hora en el formato deseado: "año+mes+día+hora+minuto+segundo" + Dron como id de la sesion
    TransactionId = str(ahora.strftime("%Y%m%d%H%M%S") + '_Dron')

    #url = "http://kwjdeais60:99/jderest/v3/orchestrator/ORCH_Generacion_Conteo_Dron"

    payload = json.dumps({
    "TransactionId": TransactionId,
    "Sucursal": Sucursal,
    "Ubicacion": Ubicacion
    })

    #print (payload)

    headers = {
    'Content-Type': 'application/json',
    'Authorization': os.getenv('JD_AUTHORIZATION') ,
    }

    

    for attempt in range(max_retries):
        try:
            response = requests.request("POST", os.getenv('JD_URL_GENERACION_CONTEO'), headers=headers, data=payload)
            if response.status_code == 200:
                # Guardar los valores en variables
                #respuesta_dict = response.json()
                #service_request = respuesta_dict['ServiceRequest1']
                #job_number = service_request['jobNumber']
                
                print('Éxito Ejecutando la Api de Conteo de JD')
               # print (response.json())
                return  "OK"       
            else:
                print(f"Error en Api de Conteo de JD, Solicitud termina con el codigo {response.status_code} en el intento {attempt + 1}")
        except requests.exceptions.RequestException as e:
            print(f"Error Ejecutando la Api de Conteo de JD: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
    return None


def Retorno_Datos_Conteo (resultado:json):


    max_retries=5

    payload = resultado

    headers = {
    'Content-Type': 'application/json',
    'Authorization': os.getenv('JD_AUTHORIZATION') ,
    }




    for attempt in range(max_retries):
        try:
            response = requests.request("POST", os.getenv('JD_URL_RETORNO_CONTEO'), headers=headers, json=payload)
            if response.status_code == 200:
                # Guardar los valores en variables
                
                print('Éxito Actualizando Inventario en JD')
                print (response.json())

                return  "OK"        
            else:
                print(f"Error en Api de Retorno Conteo de JD, Solicitud termina con el codigo {response.status_code}  en el intento {attempt + 1}")
                #print(f"Error en Api de Retorno Conteo de JD, Solicitud termina con el codigo {response.status_code} y mensaje  {response.json().get('message', 'No message found')} en el intento {attempt + 1}")

        except requests.exceptions.RequestException as e:
            print(f"Error Ejecutando la Api de Retorno Conteo de JD: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff

    return None


def Generar_Reporte_Conteo (NumeroConteo:str):

    max_retries=3

    payload = {
    "Estado": " ",
    "NumC": NumeroConteo
    }

    headers = {
    'Content-Type': 'application/json',
    'Authorization': os.getenv('JD_AUTHORIZATION') ,
    }

    print ("Número de Conteo : " + NumeroConteo )

    for attempt in range(max_retries):
        try:
            response = requests.request("POST", os.getenv('JD_URL_REPORTE_CONTEO'), headers=headers, json=payload)
                    
            if response.status_code == 200:
                # Guardar los valores en variables
                
                print('Éxito Solicitando Reporte en Inventario en JD con NumC=' + NumeroConteo)
                print (response.json())

                return  "OK"        
            else:
                print(f"Error en Api de Solicitud Reporte Conteo de JD, Solicitud termina con el codigo {response.status_code} en el intento {attempt + 1}")
                print(response.json())
                time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.RequestException as e:
            print(f"Error Ejecutando la Api deSolicitud Reporte Conteo de JD: {e}")
           

    return None







def Archivo_Conteo_Generado_Nuevo(start_time:time):
    
    ruta_Archivo_JD = os.path.join(os.getenv('JD_DRON_FOLDER'), os.getenv('JD_DRON_FILE'))
    #obtenemos la fecha de creacion del archivo jsonout disponible
    fecha_creacion_jsonout = datetime.datetime.fromtimestamp(os.path.getmtime(ruta_Archivo_JD))

    #Revisar si se la fecha del archivo disponoble es actual (> a la hora de inicio de ejecucion del codigo)
    if fecha_creacion_jsonout > datetime.datetime.fromtimestamp(start_time):
        return "OK"
    else:
        return None


if __name__ == "__main__":

    #test();
    #Obtener_Ultimo_Archivo()

    Generar_Conteo("SGMINA","PT")
    
    #print (job_number)
    #Generar_Reporte_Conteo("10938")

    '''
    Primero definir un transaction ID (TransactionId) unico para esa ejecucion para poder hacer trasabilidad en JD. ejemplo fecha + Dron Update algo asi

    Al generar el conteo en JD. 
    
    
    La respuesta para actualizar el Inventario es:
    BatchNumber
    NumeroConteo
    ResultadoConteo
    Bodega
    Ubicacion
    NumeroEtiqueta
    Sequence
    CodigoArticulo
    TransactionId

    POST http://kwjdeais60:99/jderest/v3/orchestrator/ORCH_RetornoDatosConteo_Dron


    
    Para enviar un resumen de toda la transaccion via email, consumir Api
    POST http://kwjdeais60:99/jderest/v3/orchestrator/ORCH_EndRetornoConteo_Dron 
    Cyuerpo
    {Estado:"" y NumC :"#NumerodeConteo"}



    '''