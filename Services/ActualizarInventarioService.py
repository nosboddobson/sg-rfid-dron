import datetime
import json
import os

from dotenv import load_dotenv
import pandas as pd

load_dotenv()


"""
    Function to retrieve the most recent CSV file in the specified folder.
    Returns the path of the latest CSV file found.
"""
def Obtener_Ultimo_Archivo():
    # Obtener la lista de archivos en la carpeta
    folder =  os.getenv('Dron_Folder') 
    #print (folder)
    archivos = os.listdir(folder)
    #print (archivos)
    # Filtrar solo los archivos de csv
    archivos_csv = [archivo for archivo in archivos if archivo.endswith(".csv")]
    
    if not archivos_csv:
        print("No se encontraron archivos de Registros en la carpeta " & folder)
        return None

    # Encontrar el archivo más reciente
    ultimo_archivo = None
    fecha_ultimo_archivo = None
    for archivo in archivos_csv:
        ruta_completa = os.path.join(folder, archivo)
        fecha_creacion = datetime.datetime.fromtimestamp(os.path.getctime(ruta_completa))
        if fecha_ultimo_archivo is None or fecha_creacion > fecha_ultimo_archivo:
            ultimo_archivo = archivo
            fecha_ultimo_archivo = fecha_creacion

    #print("fecha_ultimo_archivo : ", fecha_ultimo_archivo)
    print("Ruta Ultimo Archivo : ", os.path.join(folder, ultimo_archivo))
    return os.path.join(folder, ultimo_archivo)



def actualizar_estado_inventario(json_entrada):
    
    Ultimo_Archivo_Dron = Obtener_Ultimo_Archivo()
    
    #buscar ultimo archivo y limpiarlo
    if Ultimo_Archivo_Dron:
        Ultimo_Archivo_Dron_data = pd.read_csv(Ultimo_Archivo_Dron )
    
    Ultimo_Archivo_Dron_data = Ultimo_Archivo_Dron_data[Ultimo_Archivo_Dron_data['EPC'] != '00 00 00'] #eliminar filas sin lectura de tag
    Ultimo_Archivo_Dron_data = Ultimo_Archivo_Dron_data.drop_duplicates(subset=['EPC']) # eliminar filas duplicadas
    Ultimo_Archivo_Dron_data['EPC'] = Ultimo_Archivo_Dron_data['EPC'].str.replace(' ', '').str.lower() # llevar todo a minusculas

    
    #Buscar coincidencias de tags en inventario y actualizar json de entrada con existencias
    for item in json_entrada['Inventario']:     
        match = Ultimo_Archivo_Dron_data[Ultimo_Archivo_Dron_data['EPC'] == str(item['NumeroEtiqueta']).replace(" ", "").lower()]
        if not match.empty:    
            item['Existe']="Si"
            #print (item)
        else:
            item['Existe']="No"
            
                 
        return json_entrada
    else: 
        return None
    

if __name__ == "__main__":

    #test();
    #Obtener_Ultimo_Archivo()
    file_path="jsonout.json"
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    actualizar_estado_inventario(data)