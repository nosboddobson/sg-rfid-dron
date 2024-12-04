import os
import pyodbc
import pandas as pd
import json
from dotenv import load_dotenv
from Services import DronService, LogService  # Assuming these modules are already defined
#import DronService, LogService
# Load environment variables from .env
load_dotenv(override=True)

# Connection function using credentials from .env
def get_db_connection():
    server = os.getenv('DB_DRON_SERVER')
    database = os.getenv('DB_DRON_DATABASE')
    username = os.getenv('DB_DRON_USERNAME')
    password = os.getenv('DB_DRON_PASSWORD')

    conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}')
    return conn

def Contar_Numero_de_Elementos(filename):
    Ultimo_Archivo_Dron = os.path.join(os.getenv('DRON_FOLDER'), filename)
    
    if Ultimo_Archivo_Dron:
        Ultimo_Archivo_Dron_data = pd.read_csv(Ultimo_Archivo_Dron)
        if 'EPC' in Ultimo_Archivo_Dron_data.columns:
            Ultimo_Archivo_Dron_data['EPC'] = Ultimo_Archivo_Dron_data['EPC'].str.replace(' ', '').str.lower()  # Normalize EPC
            Ultimo_Archivo_Dron_data = Ultimo_Archivo_Dron_data[Ultimo_Archivo_Dron_data['EPC'] != '00 00 00']  # Filter out rows without a valid tag
            Ultimo_Archivo_Dron_data = Ultimo_Archivo_Dron_data.drop_duplicates(subset=['EPC'])  # Remove duplicates
            

            numero_de_epc = Ultimo_Archivo_Dron_data['EPC'].count()
            return numero_de_epc
        return 0
    else:
        return 0

def Obtener_duracion_Vuelo(filename):
    Ultimo_Archivo_Dron = os.path.join(os.getenv('DRON_FOLDER'), filename)

    
    if Ultimo_Archivo_Dron:
        try:
            df = pd.read_csv(Ultimo_Archivo_Dron)
            if len(df) >2:
                df['Localtime'] = pd.to_datetime(df['Localtime'])
                time_diff = df['Localtime'].max() - df['Localtime'].min()
                return int(time_diff.total_seconds())
        except Exception as e:
            print(f"Error Obtener_duracion_Vuelo: {e}")
            return 0
    else:
        return 0

def insertar_datos_inventario_vuelos(filename):
    Fecha_Vuelo = LogService.Extraer_Fecha_Hora_Desde_Archivo(filename)
    if Fecha_Vuelo==0:
            Fecha_Vuelo = LogService.Extraer_Fecha_Hora_Desde_Nombre_Archivo(filename)
    
    Tiempo_Vuelo = Obtener_duracion_Vuelo(filename)
    if not Tiempo_Vuelo :
        Tiempo_Vuelo=0
    #print ("Tiempo de vuelo: " + str(Tiempo_Vuelo))
    Numero_Elementos = Contar_Numero_de_Elementos(filename)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = '''
            INSERT INTO Inventario_Vuelos (Nombre_Archivo, Fecha_Vuelo, N_elementos, Tiempo_Vuelo, Estado_Inventario)
            VALUES (?, ?, ?, ?, ?)
        '''
        data = (filename, Fecha_Vuelo, int(Numero_Elementos), Tiempo_Vuelo, 'Pendiente')
        cursor.execute(insert_query, data)

        conn.commit()
        print("Datos insertados correctamente.")
    except pyodbc.Error as e:
        print(f"Error en la inserción: {e}")
    finally:
        conn.close()

def Actuaizar_Estado_inventario_vuelos(ID):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        update_query = '''
            UPDATE Inventario_Vuelos
            SET Estado_Inventario = 'OK'
            WHERE ID = ?
        '''
        cursor.execute(update_query, (ID,))
        conn.commit()
        print("Estado actualizado correctamente.")
    except pyodbc.Error as e:
        print(f"Error en la actualización: {e}")
    finally:
        conn.close()

def Resumen_de_Conteo_desde_Json(inventario_json):
    if isinstance(inventario_json, str):
        try:
            data = json.loads(inventario_json)
        except json.JSONDecodeError:
            return {"Error": "Invalid JSON format"}
    else:
        data = inventario_json

    if 'ARRAY_INPUT' not in data or not isinstance(data['ARRAY_INPUT'], list):
        return {"Error": "'ARRAY_INPUT' key missing or not a list"}

    rows = data['ARRAY_INPUT']
    total_rows = len(rows)
    faltante_count = 0
    ok_count = 0
    other_count = 0

    for row in rows:
        if isinstance(row, dict):
            resultado = row.get('ResultadoConteo', None)
            if resultado == "FALTANTE":
                faltante_count += 1
            elif resultado == "OK":
                ok_count += 1
            else:
                other_count += 1
        else:
            other_count += 1

    percentage_ok = (ok_count / total_rows) * 100 if total_rows > 0 else 0

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
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = '''
            INSERT INTO Inventarios_JDE (ID_Vuelo, Fecha_Inventario, Elementos_OK, Elementos_Faltantes,
                                         Elementos_Sobrantes, Porcentaje_Lectura, NumeroConteo, 
                                         Sucursal, Ubicacion, TransactionId)
            OUTPUT INSERTED.ID  -- This line retrieves the ID of the newly inserted row
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        data = (ID_Vuelo, Fecha_Inventario, int(Elementos_OK), int(Elementos_Faltantes), 
                int(Elementos_Sobrantes), float(Porcentaje_Lectura), int(NumeroConteo), 
                Sucursal, Ubicacion, TransactionId)

        cursor.execute(insert_query, data)
        
        # Fetch the inserted ID
        inserted_id = cursor.fetchone()[0]  # Get the first column from the fetched row
        
        conn.commit()
        print("Inventario JDE insertado correctamente.")
        return inserted_id  # Return the inserted ID
    except pyodbc.Error as e:
        print(f"Error en la inserción: {e}")
        return None  # Return None if there is an error
    finally:
        conn.close()
        
def insertar_elementos_jde(id_inventario, inventario_json):
    if isinstance(inventario_json, str):
        try:
            data = json.loads(inventario_json)
        except json.JSONDecodeError:
            return {"Error": "Invalid JSON format"}
    else:
        data = inventario_json

    if 'ARRAY_INPUT' not in data or not isinstance(data['ARRAY_INPUT'], list):
        return {"Error": "'ARRAY_INPUT' key missing or not a list"}

    rows = data['ARRAY_INPUT']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = '''
            INSERT INTO Elementos_JDE (EPC, Resultado, ID_Inventario, Ubicacion, CodigoArticulo)
            VALUES (?, ?, ?, ?, ?)
        '''

        for elemento in rows:
            epc = elemento.get("NumeroEtiqueta", "").strip().upper() if elemento.get("NumeroEtiqueta") is not None else ""
            resultado = elemento.get('ResultadoConteo').capitalize()
            ubicacion = elemento.get('Ubicacion').strip().upper()
            codigo_articulo = elemento.get("CodigoArticulo").strip().upper()

            cursor.execute(insert_query, (epc, resultado, id_inventario, ubicacion, codigo_articulo))

        conn.commit()
        print(f"Inserted {len(rows)} rows into Elementos_JDE table.")
    except pyodbc.Error as e:
        return {"Error": f"An error occurred: {e}"}
    finally:
        conn.close()

    return {"Success": f"Inserted {len(rows)} rows into Elementos_JDE table."}


def delete_inventario_vuelo_row(id_to_delete):

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # SQL query to delete a row based on the ID
        sql_query = "DELETE FROM Inventario_Vuelos WHERE ID = ?"
        
        # Execute the query
        cursor.execute(sql_query, (id_to_delete,))
        
        # Commit the transaction
        conn.commit()

        print(f"Fila con ID {id_to_delete} ha sido eliminada exitosamente.")
        return True

    except pyodbc.Error as e:
        #return {"Error": f"An error occurred: {e}"}
        return False
    finally:
        conn.close()

def obtener_nombre_archivo(ID):
    
    conn = get_db_connection()
    cursor = conn.cursor()

    query='''
        SELECT Nombre_Archivo  FROM Inventario_Vuelos
        WHERE ID=?'''
    
    cursor.execute(query, (ID,))

    result = cursor.fetchone()

    if result:
        Nombre_Archivo = result[0]
        conn.close()
        return Nombre_Archivo
    else:
        conn.close()
        return None
    
if __name__ == "__main__":

    print("OK")
    print (obtener_nombre_archivo(135))

   # with open("output_inventario.json", "r") as file:
   #     json_content = file.read()
    
    #print("OK")
    #print(insertar_elementos_jde(2, json_content))
