import datetime
import json
import os
import sqlite3
import time
from Services import DronService, LogService
#import LogService,DronService
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



def Obtener_duracion_Vuelo (filename):

    Ultimo_Archivo_Dron =os.path.join(os.getenv('DRON_FOLDER'), filename)
    
    #buscar ultimo archivo y limpiarlo
    if Ultimo_Archivo_Dron:
        try:
            # Read the CSV file into a DataFrame
            df = pd.read_csv(Ultimo_Archivo_Dron )

            # Ensure 'Timestamp' column is in datetime format
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])

            # Calculate the difference between the first and last Timestamp
            time_diff = df['Timestamp'].max() - df['Timestamp'].min()
            #print ("Segundos:" + int(time_diff.total_seconds()))

            return int(time_diff.total_seconds())
    
        except Exception as e:
            print(f"Error: {e}")  # Log the error if needed
            return 0  # Return default value in case of error
    else:
        return 0





def insertar_datos_inventario_vuelos(filename):
    """Inserta datos de ejemplo en la tabla 'Inventario_Vuelos'."""

    Fecha_Vuelo= LogService.Extraer_Fecha_Hora_Desde_Nombre_Archivo(filename)
    Tiempo_Vuelo=Obtener_duracion_Vuelo(filename)
    Numero_Elementos= Contar_Numero_de_Elementos(filename)
    #print (Numero_Elementos)

    # Conectar a la base de datos
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()

    # Insertar datos de ejemplo
    datos = [
        (filename, Fecha_Vuelo, int(Numero_Elementos), int(Tiempo_Vuelo),'Pendiente')
    ]

    cursor.executemany('''
        INSERT INTO Inventario_Vuelos (Nombre_Archivo, Fecha_Vuelo, N_elementos, Tiempo_Vuelo,Estado_Inventario)
        VALUES (?, ?, ?, ?,?)
    ''', datos)

    # Guardar los cambios y cerrar la conexión
    conn.commit()
    conn.close()

# Llamar a la función para insertar los datos



def Actuaizar_Estado_inventario_vuelos(ID):
    """Inserta datos de ejemplo en la tabla 'Inventario_Vuelos'."""

    try:
        # Connect to the SQLite database
        
        conn = sqlite3.connect('inventario.db')
        cursor = conn.cursor()

        cursor.execute('''
                UPDATE Inventario_Vuelos
                SET Estado_Inventario = 'OK'
                WHERE ID = ?
            ''', (ID,))
        # Guardar los cambios y cerrar la conexión
        conn.commit()

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
    # Close the connection
        if conn:
            conn.close()


# Llamar a la función para insertar los datos


def Resumen_de_Conteo_desde_Json(inventario_json):
    # Parse the JSON if it's a string
      # Parse the JSON if it's a string
    if isinstance(inventario_json, str):
        try:
            data = json.loads(inventario_json)
        except json.JSONDecodeError:
            return {"Error": "Invalid JSON format"}
    else:
        data = inventario_json

    # Check if 'ARRAY_INPUT' exists and is a list
    if 'ARRAY_INPUT' not in data or not isinstance(data['ARRAY_INPUT'], list):
        return {"Error": "'ARRAY_INPUT' key missing or not a list"}

    # Extract the rows from 'ARRAY_INPUT'
    rows = data['ARRAY_INPUT']


    # Initialize counters
    total_rows = len(rows)
    faltante_count = 0
    ok_count = 0
    other_count = 0

    # Loop through each row in the JSON
    for row in rows:
        if isinstance(row, dict):  # Ensure each row is a dictionary
            resultado = row.get('ResultadoConteo', None)  # Get the 'ResultadoConteo' value
            if resultado == "FALTANTE":
                faltante_count += 1
            elif resultado == "OK":
                ok_count += 1
            else:
                other_count += 1
        else:
            other_count += 1  # Count rows that aren't dictionaries

    # Calculate the percentage of "OK" rows
    percentage_ok = (ok_count / total_rows) * 100 if total_rows > 0 else 0

    # Return a dictionary with the summary
    return {
        "Total Rows": total_rows,
        "FALTANTE Count": faltante_count,
        "OK Count": ok_count,
        "Other Count": other_count,
        "Percentage OK": round(percentage_ok, 2)
    }


def insertar_inventario_jde(ID_Vuelo, Fecha_Inventario, Elementos_OK, Elementos_Faltantes, 
                            Elementos_Sobrantes, Porcentaje_Lectura, NumeroConteo, 
                            Sucursal, Ubicacion, TransactionId):
    try:
        # Connect to the SQLite database
        
        conn = sqlite3.connect('inventario.db')
        cursor = conn.cursor()

        # Prepare the SQL insert statement
        insert_query = '''
            INSERT INTO Inventarios_JDE (ID_Vuelo, Fecha_Inventario, Elementos_OK, Elementos_Faltantes,
                                        Elementos_Sobrantes, Porcentaje_Lectura, NumeroConteo, 
                                        Sucursal, Ubicacion, TransactionId)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        data  = (ID_Vuelo, Fecha_Inventario, int(Elementos_OK), int(Elementos_Faltantes), 
                                    int(Elementos_Sobrantes), float(Porcentaje_Lectura), int(NumeroConteo), 
                                    Sucursal, Ubicacion, TransactionId)
        print (data)
        # Execute the insert statement with the passed data
        cursor.execute(insert_query, data)

        # Commit the changes and close the connection
        conn.commit()
     
        print("Inventario JDE insertado correctamente.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")

    finally:
    # Close the connection
        if conn:
            conn.close()


def insertar_elementos_jde(id_inventario, inventario_json):
    # Check if the input is a string and attempt to parse it as JSON
    if isinstance(inventario_json, str):
        try:
            data = json.loads(inventario_json)
        except json.JSONDecodeError:
            return {"Error": "Invalid JSON format"}
    else:
        data = inventario_json

    # Check if 'ARRAY_INPUT' exists and is a list
    if 'ARRAY_INPUT' not in data or not isinstance(data['ARRAY_INPUT'], list):
        return {"Error": "'ARRAY_INPUT' key missing or not a list"}

    # Extract the rows from 'ARRAY_INPUT'
    rows = data['ARRAY_INPUT']

    # Connect to the SQLite database
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()

    # Prepare the SQL insert statement
    insert_query = '''
        INSERT INTO Elementos_JDE (EPC, Resultado, ID_Inventario, Ubicacion, CodigoArticulo)
        VALUES (?, ?, ?, ?, ?)
    '''

    try:
        # Loop through each row in the JSON array
        for elemento in rows:
            
            epc = elemento.get("NumeroEtiqueta", "").strip().upper() if elemento.get("NumeroEtiqueta") is not None else ""
            resultado = elemento.get('ResultadoConteo').capitalize()  # Convert ResultadoConteo to capital case
            ubicacion = elemento.get('Ubicacion').strip().upper()
            codigo_articulo = elemento.get("CodigoArticulo").strip().upper()

            # Execute the insert query with data for each element
            cursor.execute(insert_query, (epc, resultado, id_inventario, ubicacion, codigo_articulo))

        # Commit the transaction
        conn.commit()
        print(f"Inserted {len(rows)} rows into Elementos_JDE table.")

    except sqlite3.Error as e:
        
        return {"Error": f"An error occurred: {e}"}

    finally:
        # Close the connection
        if conn:
            conn.close()
    
    return {"Success": f"Inserted {len(rows)} rows into Elementos_JDE table."}




if __name__ == "__main__":

    #insertar_datos_inventario_vuelos('sierradron_lecturas_20240923_183258.csv')
    
    #Contar_Numero_de_Elementos('sierradron_lecturas_20240923_183258.csv')
    print ("OK")
    #Actuaizar_Estado_inventario_vuelos('10')
    #inventario_json,NumeroConteo,TransactionId= DronService.actualizar_estado_inventario()
    #print (inventario_json)
    #print(insertar_elementos_jde(3,inventario_json))