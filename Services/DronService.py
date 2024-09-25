import datetime
import glob
import json
import os

from dotenv import load_dotenv
import pandas as pd

load_dotenv(override=True)


"""
    Function to retrieve the most recent CSV file in the specified folder.
    Returns the path of the latest CSV file found.
    
    examples:
    folder ="d:\\archivos"
    extension = "csv"

"""
def Obtener_Ultimo_Archivo_csv(folder,extension="csv"):

    #print (folder)
    archivos = os.listdir(folder)
    #print (archivos)
    # Filtrar solo los archivos de csv
    archivos_csv = [archivo for archivo in archivos if archivo.endswith("." +extension )]
    
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



def actualizar_estado_inventario():
    
    Ultimo_Archivo_Dron = Obtener_Ultimo_Archivo_csv(os.getenv('Dron_Folder'),"csv" )
    
    #buscar ultimo archivo y limpiarlo
    if Ultimo_Archivo_Dron:
        Ultimo_Archivo_Dron_data = pd.read_csv(Ultimo_Archivo_Dron )
    
    Ultimo_Archivo_Dron_data = Ultimo_Archivo_Dron_data[Ultimo_Archivo_Dron_data['EPC'] != '00 00 00'] #eliminar filas sin lectura de tag
    Ultimo_Archivo_Dron_data = Ultimo_Archivo_Dron_data.drop_duplicates(subset=['EPC']) # eliminar filas duplicadas
    Ultimo_Archivo_Dron_data['EPC'] = Ultimo_Archivo_Dron_data['EPC'].str.replace(' ', '').str.lower() # llevar todo a minusculas

    #abrimon archivo generado por JD
    ruta_Archivo_JD = os.path.join(os.getenv('JD_DRON_FOLDER'), os.getenv('JD_DRON_FILE'))
    with open(ruta_Archivo_JD, 'r') as f:
        json_entrada = json.load(f)

    
    #Buscar coincidencias de tags en inventario y actualizar json de entrada con existencias
    
    if json_entrada['Inventario']:
        for item in json_entrada['Inventario']:     
            match = Ultimo_Archivo_Dron_data[Ultimo_Archivo_Dron_data['EPC'] == str(item['NumeroEtiqueta']).replace(" ", "").lower()]
            del item['CoordenadaX']
            del item['CoordenadaY']
            del item['CoordenadaZ']
            if not match.empty:    
                item['ResultadoConteo']="OK"
                #print (item)
            else:
                item['ResultadoConteo']="FALTANTE"
        
        NumeroConteo=str(item['NumeroConteo'])
        #remover archivo de inventario ya utilizado para que no se sume con la siguiente llamada
        borrar_archivos_en_carpeta(os.getenv('JD_DRON_FOLDER'))

        return json_entrada,NumeroConteo
    else:
        return None


def Guardar_Json(json_entrada,folder,Prefix):


    try :
        with open(os.path.join(folder, datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')+ "-"+Prefix +".json"), 'w') as outfile:
            json.dump(json_entrada, outfile, indent=4)
            print("Archivo "+ datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')+ "-"+Prefix +".json"+ " creado con éxito")
            return "Archivo Json Creado con exito"
        
    except Exception as e:
        return None

def Guardar_json_como_csv(json_entrada,folder,Prefix):


    try :

        data_list = []
        for item in json_entrada['Inventario']:  # Adjust based on your JSON structure
            data_list.append(item)

        df = pd.DataFrame(data_list)
        df.to_csv(os.path.join(folder, datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')+ "-"+Prefix +".csv"), index=False)
        print("Archivo "+ datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')+ "-"+Prefix +".csv"+ " creado con éxito")
        return "Archivo Creado  CSV  con exito"
        
    except Exception as e:
        return None

def borrar_archivos_en_carpeta(carpeta):
    """
    Elimina todos los archivos en la carpeta especificada.

    :param carpeta: Ruta a la carpeta de la cual se eliminarán los archivos.
    """
    # Asegúrate de que la carpeta existe
    if not os.path.isdir(carpeta):
        print(f"La carpeta {carpeta} no existe.")
        return

    # Obtener la lista de todos los archivos en la carpeta
    archivos = glob.glob(os.path.join(carpeta, '*'))

    # Eliminar cada archivo
    for archivo in archivos:
        try:
            if os.path.isfile(archivo):  # Verificar si es un archivo
                os.remove(archivo)
                print(f"Archivo eliminado: {archivo}")
        except Exception as e:
            print(f"No se pudo eliminar el archivo {archivo}. Error: {e}")



    
if __name__ == "__main__":

    #test();
    #Obtener_Ultimo_Archivo()
    file_path="jdbkp\\jsonout.txt"
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    actualizar_estado_inventario(data)