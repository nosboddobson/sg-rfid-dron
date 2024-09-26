
import datetime
import os
import re
import time
from dotenv import load_dotenv
import pandas as pd

load_dotenv(override=True)
csv_Ejecuciones= "Api_Executions.csv"


def Guardar_Ejecucion_a_csv(start_time,end_time,Api,code):
    try:
        execution_time = end_time - start_time
        data = {'Api': Api, 'StartTime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)), 'ExecutionDuration': execution_time,'Code':code}
        df = pd.DataFrame(data, index=[0])
        df.to_csv(csv_Ejecuciones, index=False,mode='a', header=False)
    except Exception as e:
        print('Error Guardando registro de Ejecución: ' + str(e))


csv_Recepcion_Archivos_Dron= "Log_Lecturas_Dron.csv"


def Guardar_Recepcion_Archivos_Dron_a_csv(archivo):
    
    execution_time = Extraer_Fecha_Hora_Desde_Nombre_Archivo(archivo)
    
    try:
        data = {'Fecha_Medicion': execution_time, 'Fecha_Envio':time.strftime("%Y-%m-%d %H:%M:%S"), 'Archivo': archivo}
        print(data)
        df = pd.DataFrame(data, index=[0])
        df.to_csv(os.getenv('DRON_FOLDER')+"\\"+csv_Recepcion_Archivos_Dron, index=False,mode='a', header=False)
    except Exception as e:
        print('Error Actualizando registro de Ejecución {csv_Recepcion_Archivos_Dron}: ' + str(e))


def Extraer_Fecha_Hora_Desde_Nombre_Archivo (archivo:str):

    try:
        # Split the filename by underscores and extract date and time parts
        fecha_str = archivo.split('_')[-2]  # Extract 'YYYYMMDD'
        hora_str = archivo.split('_')[-1].replace(".csv", "")  # Extract 'HHMMSS'

        # Validate the lengths of the extracted parts
        if len(fecha_str) == 8 and len(hora_str) == 6:
            # Format to "YYYY-MM-DD HH:MM:SS"
            fecha = f"{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:]} {hora_str[:2]}:{hora_str[2:4]}:{hora_str[4:]}"
            return fecha
        else:
            return None
    except (IndexError, ValueError):
        return None

# Ejemplo de uso
if __name__ == "__main__":

    #start_time = time.time()
    #Api = "Ejemplo"
    #time.sleep(5)
    #end_time = time.time()
    #Guardar_Ejecucion_a_csv(start_time,end_time,Api)
    #print ("OK")

    archivo= "sierradron_lecturas_20240923_183258.csv"
    Guardar_Recepcion_Archivos_Dron_a_csv(archivo)