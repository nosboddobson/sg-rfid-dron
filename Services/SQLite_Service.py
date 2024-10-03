import os
import sqlite3
import time
from Services import LogService
#import LogService
from dotenv import load_dotenv
import pandas as pd

load_dotenv(override=True)


def Contar_Numero_de_Elementos (filename):

    Ultimo_Archivo_Dron =os.path.join(os.getenv('DRON_FOLDER'), filename)
    
    #buscar ultimo archivo y limpiarlo
    if Ultimo_Archivo_Dron:
        Ultimo_Archivo_Dron_data = pd.read_csv(Ultimo_Archivo_Dron )
    
        Ultimo_Archivo_Dron_data = Ultimo_Archivo_Dron_data[Ultimo_Archivo_Dron_data['EPC'] != '00 00 00'] #eliminar filas sin lectura de tag
        Ultimo_Archivo_Dron_data = Ultimo_Archivo_Dron_data.drop_duplicates(subset=['EPC']) # eliminar filas duplicadas
        Ultimo_Archivo_Dron_data['EPC'] = Ultimo_Archivo_Dron_data['EPC'].str.replace(' ', '').str.lower() # llevar todo a minusculas

        numero_de_epc=Ultimo_Archivo_Dron_data['EPC'].count()
        #print (numero_de_epc)
        return numero_de_epc
    else:
        return None





def insertar_datos_inventario_vuelos(filename):
    """Inserta datos de ejemplo en la tabla 'Inventario_Vuelos'."""

    Fecha_Vuelo= LogService.Extraer_Fecha_Hora_Desde_Nombre_Archivo(filename)
    Numero_Elementos= Contar_Numero_de_Elementos(filename)
    #print (Numero_Elementos)

    # Conectar a la base de datos
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()

    # Insertar datos de ejemplo
    datos = [
        (filename, Fecha_Vuelo, int(Numero_Elementos), 'Pendiente')
    ]

    cursor.executemany('''
        INSERT INTO Inventario_Vuelos (Nombre_Archivo, Fecha_Vuelo, N_elementos, Estado_Inventario)
        VALUES (?, ?, ?, ?)
    ''', datos)

    # Guardar los cambios y cerrar la conexión
    conn.commit()
    conn.close()

# Llamar a la función para insertar los datos





if __name__ == "__main__":

    insertar_datos_inventario_vuelos('sierradron_lecturas_20240923_183258.csv')
    #Contar_Numero_de_Elementos('sierradron_lecturas_20240923_183258.csv')