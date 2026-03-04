import datetime
import os
import pyodbc
import pandas as pd
import json
import logging
from dotenv import load_dotenv
from Services import LogService  # Assuming these modules are already defined
import warnings

# Suprimir advertencias de pandas sobre SQLAlchemy
warnings.filterwarnings('ignore', message='.*pandas only supports SQLAlchemy connectable.*')

# Load environment variables from .env
load_dotenv(override=True)

# Variables globales para almacenar la conexión y el engine
_db_engine = None
_use_sqlalchemy = False
_active_connection = None

def get_db_connection():
    """
    Obtiene una conexión a la base de datos.
    Intenta usar SQLAlchemy primero, si falla usa pyodbc.
    Retorna siempre una conexión compatible (pyodbc-like) no un Engine.
    
    Returns:
        pyodbc.Connection: Una conexión que funciona tanto con SQLAlchemy como pyodbc
    """
    global _db_engine, _use_sqlalchemy, _active_connection
    
    server = os.getenv('DB_DRON_SERVER')
    database = os.getenv('DB_DRON_DATABASE')
    username = os.getenv('DB_DRON_USERNAME')
    password = os.getenv('DB_DRON_PASSWORD')
    
    # Intentar usar SQLAlchemy primero (solo en el primer llamado)
    if _db_engine is None and not _use_sqlalchemy:
        try:
            from sqlalchemy import create_engine
            
            # Construir la cadena de conexión para SQLAlchemy
            connection_string = f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver=SQL+Server'
            _db_engine = create_engine(connection_string)
            
            # Probar la conexión obteniendo una conexión real del Engine
            with _db_engine.connect() as test_conn:
                pass
            
            _use_sqlalchemy = True
            print("[INFO] Usando SQLAlchemy para conexión a base de datos")
            
        except Exception as e:
            print(f"[WARNING] No se pudo usar SQLAlchemy: {e}")
            print("[INFO] Fallback a pyodbc")
            _use_sqlalchemy = False
            _db_engine = None
    
    # Si SQLAlchemy está disponible, obtener una conexión del Engine
    if _use_sqlalchemy and _db_engine is not None:
        try:
            # Obtener una conexión del Engine (pyodbc Connection envuelta)
            raw_conn = _db_engine.raw_connection()
            return raw_conn
        except Exception as e:
            print(f"[WARNING] Error obteniendo conexión de SQLAlchemy Engine: {e}")
            _use_sqlalchemy = False
    
    # Usar pyodbc como fallback
    try:
        conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}')
        return conn
    except Exception as e:
        print(f"[ERROR] Error al conectar con pyodbc: {e}")
        raise

def execute_sql_query(sql_query, conn, params=None):
    """
    Ejecuta una query SQL SELECT y retorna un DataFrame.
    Funciona transparentemente con conexiones de SQLAlchemy o pyodbc.
    
    Args:
        sql_query (str): La query SQL
        conn: Conexión pyodbc (compatible con ambos)
        params (tuple): Parámetros para la query
    
    Returns:
        pd.DataFrame: Resultado de la query
    """
    try:
        if params:
            return pd.read_sql_query(sql_query, conn, params=params)
        else:
            return pd.read_sql_query(sql_query, conn)
    except Exception as e:
        print(f"[ERROR] Error ejecutando query: {e}")
        raise

def get_cursor_from_connection(conn):
    """
    Obtiene un cursor desde una conexión pyodbc.
    
    Args:
        conn: Conexión pyodbc
    
    Returns:
        cursor: Un cursor pyodbc
    """
    return conn.cursor()

def close_connection(conn):
    """
    Cierra una conexión pyodbc.
    
    Args:
        conn: Conexión pyodbc
    """
    try:
        if conn and hasattr(conn, 'close'):
            conn.close()
    except Exception as e:
        print(f"[WARNING] Error al cerrar conexión: {e}")

def execute_update_query(sql_query, conn, params=None):
    """
    Ejecuta una query UPDATE/INSERT/DELETE.
    
    Args:
        sql_query (str): La query SQL
        conn: Conexión pyodbc
        params (tuple): Parámetros para la query
    
    Returns:
        bool: True si la operación fue exitosa
    """
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql_query, params)
        else:
            cursor.execute(sql_query)
        conn.commit()
        return True
            
    except Exception as e:
        print(f"[ERROR] Error ejecutando update query: {e}")
        try:
            conn.rollback()
        except:
            pass
        raise

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
        cursor = get_cursor_from_connection(conn)

        insert_query = '''
            INSERT INTO Inventario_Vuelos (Nombre_Archivo, Fecha_Vuelo, N_elementos, Tiempo_Vuelo, Estado_Inventario)
            VALUES (?, ?, ?, ?, ?)
        '''
        data = (filename, Fecha_Vuelo, int(Numero_Elementos), Tiempo_Vuelo, 'Pendiente')
        cursor.execute(insert_query, data)

        conn.commit()
        print("Datos insertados correctamente.")
    except Exception as e:
        print(f"Error en la inserción: {e}")
    finally:
        close_connection(conn)

def Actuaizar_Estado_inventario_vuelos(ID):
    try:
        conn = get_db_connection()
        cursor = get_cursor_from_connection(conn)

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
        close_connection(conn)

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
        cursor = get_cursor_from_connection(conn)

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
        close_connection(conn)

def insertar_ruta_video_inventario_jde(ID_Vuelo, ruta_video):
    try:
        conn = get_db_connection()
        cursor = get_cursor_from_connection(conn)

        update_query = '''
            UPDATE Inventarios_JDE
            SET Video_Vuelo = ?
            WHERE ID = ?
        '''
        cursor.execute(update_query, (ruta_video,ID_Vuelo))
        conn.commit()

        return True  # Return the inserted ID
    except pyodbc.Error as e:
        print(f"Error en la inserción: {e}")
        return None  # Return None if there is an error
    finally:
        close_connection(conn)
        
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
        cursor = get_cursor_from_connection(conn)

        insert_query = '''
            INSERT INTO Elementos_JDE (EPC, Resultado, ID_Inventario, Ubicacion, CodigoArticulo)
            VALUES (?, ?, ?, ?, ?)
        '''

        for elemento in rows:

            epc = elemento.get("NumeroEtiqueta", "").strip().upper() if elemento.get("NumeroEtiqueta") is not None else "SIN ETIQUETA"
            resultado = elemento.get('ResultadoConteo').capitalize()
            ubicacion = elemento.get('Ubicacion').strip().upper()
            codigo_articulo = elemento.get("CodigoArticulo").strip().upper()

            cursor.execute(insert_query, (epc, resultado, id_inventario, ubicacion, codigo_articulo))

        conn.commit()
        print(f"Inserted {len(rows)} rows into Elementos_JDE table.")
    except pyodbc.Error as e:
        return {"Error": f"An error occurred: {e}"}
    finally:
        close_connection(conn)

    return {"Success": f"Inserted {len(rows)} rows into Elementos_JDE table."}

def insertar_Fecha_Vuelo_Elementos_JED(id_vuelo,id_inventario):

    Ultimo_Archivo_Dron=obtener_nombre_archivo(id_vuelo)
    try :
        #buscar ultimo archivo 
        if Ultimo_Archivo_Dron:
            Ultimo_Archivo_Dron_data = pd.read_csv(os.path.join(os.getenv('Dron_Folder'),Ultimo_Archivo_Dron ))
         # 2. Clean the EPC column in the CSV (lowercase and remove spaces)
        Ultimo_Archivo_Dron_data['EPC'] = Ultimo_Archivo_Dron_data['EPC'].str.lower().str.replace(' ', '')
        Ultimo_Archivo_Dron_data['Timestamp'] = pd.to_datetime(Ultimo_Archivo_Dron_data['Timestamp']) #Convert to datetime

        # 3. Establish a connection to the SQL Server database
        conn = get_db_connection()
        cursor = get_cursor_from_connection(conn)

        
        # 4. Read the SQL Server table into a Pandas DataFrame (for efficient matching)
        
        sql_query  = '''SELECT EPC, ID_Inventario, Fecha_Lectura FROM Elementos_JDE Where ID_Inventario = ?'''
        df_sql = execute_sql_query(sql_query, conn, params=(id_inventario,))  # Parameterize the query


        # 5. Clean the EPC column in the SQL Server DataFrame (lowercase and remove spaces)
        df_sql['EPC'] = df_sql['EPC'].str.lower().str.replace(' ', '')

        # 6. Merge the DataFrames based on the cleaned EPC column
        merged_df = pd.merge(df_sql, Ultimo_Archivo_Dron_data, on='EPC', how='left')

        # 7. Update the SQL Server table in batches for efficiency
        batch_size = 100  # Adjust batch size as needed

        for i in range(0, len(merged_df), batch_size):
            batch = merged_df[i:i + batch_size]
            for _, row in batch.iterrows():
                epc = row['EPC']
                id_inventario = row['ID_Inventario']
                fecha_lectura = row['Timestamp']

                if pd.notna(fecha_lectura):  # Only update if Timestamp is not NaN
                    try:
                        update_query = f"""
                            UPDATE Elementos_JDE
                            SET Fecha_Lectura = ?
                            WHERE EPC = ? AND ID_Inventario = ?
                        """
                        cursor.execute(update_query, fecha_lectura, epc, id_inventario)
                        conn.commit()  # Commit after each batch
                    except Exception as e:
                        print(f"Error updating row: EPC={epc}, ID_Inventario={id_inventario}, Error: {e}")
                        conn.rollback() #Rollback in case of error
                        # Optionally break here if you want to stop on the first error
                        # break
        close_connection(conn)
        #print("Update Complete")

    
        return True
    except Exception as e:
        print(f"Error Actualizando estdo Inventario. Error: {e}")
        return None


def Exportar_Elementos_JED_a_csv(id_inventario):

    try:
        # 3. Establish a connection to the SQL Server database
        conn = get_db_connection()
        
        # 4. Read the SQL Server table into a Pandas DataFrame (for efficient matching)
        
        sql_query  = '''SELECT * FROM Elementos_JDE Where ID_Inventario = ? and Resultado='Ok' ORDER BY Fecha_lectura asc  '''
        df_sql = execute_sql_query(sql_query, conn, params=(id_inventario,))  # Parameterize the query

        df_sql.to_csv(str(id_inventario) + "_Elementos_JDE.csv",index=False,sep=";", encoding="utf-8", decimal=",")

       
        close_connection(conn)
        #print("Update Complete")

    
        return (str(id_inventario) + "_Elementos_JDE.csv")
    except Exception as e:
        print(f"Error Obteniendo  Inventario. Error: {e}")
        return None



def Exportar_Elementos_JED_a_df(id_inventario):

    try:
        # 3. Establish a connection to the SQL Server database
        conn = get_db_connection()
        
        # 4. Read the SQL Server table into a Pandas DataFrame (for efficient matching)
        
        sql_query  = '''SELECT * FROM Elementos_JDE Where ID_Inventario = ? and Resultado='Ok' ORDER BY Fecha_lectura asc  '''
        df_sql = execute_sql_query(sql_query, conn, params=(id_inventario,))  # Parameterize the query

        close_connection(conn)
        #print("Update Complete")

    
        return df_sql
    except Exception as e:
        print(f"Error Obteniendo  Inventario. Error: {e}")
        return None
def delete_inventario_vuelo_row(id_to_delete):

    try:
        conn = get_db_connection()
        cursor = get_cursor_from_connection(conn)

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
        close_connection(conn)

def obtener_nombre_archivo(ID):
    
    conn = get_db_connection()
    cursor = get_cursor_from_connection(conn)

    query='''
        SELECT Nombre_Archivo  FROM Inventario_Vuelos
        WHERE ID=?'''
    
    cursor.execute(query, (ID,))

    result = cursor.fetchone()

    if result:
        Nombre_Archivo = result[0]
        close_connection(conn)
        return Nombre_Archivo
    else:
        close_connection(conn)
        return None
    

def Dron_GET_Boton_Envio_Datos():
    
    time_to_wait=20

    try:
        conn = get_db_connection()
        cursor = get_cursor_from_connection(conn)

        query='''
        SELECT TOP 1  FORMAT(Fecha,'yyyy-MM-dd HH:mm:ss.ff') as Fecha FROM Dron_Stop_Button ORDER BY Fecha desc'''
        
        cursor.execute(query)
        
        result = cursor.fetchone()
        close_connection(conn)
        if result:
            Hora = datetime.datetime.strptime(str(result[0]),'%Y-%m-%d %H:%M:%S.%f')
            now = datetime.datetime.now()
            #print (Hora)
            time_difference = abs((now - Hora).total_seconds())
            #print (time_difference)
            
            return time_difference <= time_to_wait
        else:
            
            return False
    except:
        print ('Error')
        return False

def insert_client_ip_to_heartbeats(client_ip):
    """Inserts the client IP into the Dron_Heartbeats table."""

    conn = get_db_connection() #Get the connection.
    if conn is None:
        return False #exit if connection failed.

    try:
        cursor = get_cursor_from_connection(conn)

        query = '''
            INSERT INTO Dron_Heartbeats (Source)
            VALUES (?)
        '''

        cursor.execute(query, client_ip)
        conn.commit()

        print(f"Client IP '{client_ip}' Insertado correctamente")
        return True

    except pyodbc.Error as db_err:
        print(f"Error insertando Heartbeat: {db_err}")
        if conn:
            conn.rollback()
        return False

    except Exception as e:
        print(f"Exception insertando Heartbeat {e}")
        return False

    finally:
        if conn:
            close_connection(conn)
    


def obtener_datos_inventarios_jde(ID_Vuelo):
    
    conn = get_db_connection() #Get the connection.
    if conn is None:
        return False #exit if connection failed.

    try:
        cursor = get_cursor_from_connection(conn)
            # Query to fetch all data from the table
        query = '''
             SELECT TOP 1 j.ID, j.ID_Vuelo,  v.Tiempo_Vuelo, j.Fecha_Inventario,
                CAST(FORMAT(v.Fecha_Vuelo, 'dd/MM/yyyy') AS VARCHAR(16)) AS Fecha_Vuelo,
                CAST(FORMAT(v.Fecha_Vuelo, 'HH:mm') AS VARCHAR(16)) AS Hora_Vuelo,
                CAST(FORMAT(DATEADD(second, v.Tiempo_Vuelo, v.Fecha_Vuelo), 'HH:mm') AS VARCHAR(16)) AS Hora_Fin,
                RIGHT('0' + CONVERT(VARCHAR, Tiempo_Vuelo / 3600), 2) + ':' + RIGHT('0' + CONVERT(VARCHAR, (Tiempo_Vuelo % 3600) / 60), 2) AS Tiempo_Vuelo_Formateado,
                j.Elementos_OK, j.Elementos_Faltantes, 
                j.Porcentaje_Lectura, j.NumeroConteo, j.Sucursal, j.Ubicacion,
                (v.N_elementos - j.Elementos_OK) AS Elementos_Sobrantes 
            FROM Inventarios_JDE j
            JOIN Inventario_Vuelos v ON j.ID_Vuelo = v.ID
            WHERE j.ID=?
            '''
        cursor.execute(query, (ID_Vuelo,) )

        columns = [column[0] for column in cursor.description]

        # Obtener resultados como una lista de tuplas
        results = cursor.fetchall()

        # Crear DataFrame solo si hay resultados
        df = pd.DataFrame([list(row) for row in results], columns=columns) if results else pd.DataFrame(columns=columns)

        # Close the connection
        #print (df)

        return df
    
    except Exception as e:
            print(f"Error obteniendo informacion de vuelo : {e}")
            return False

    finally:
        if conn:
            close_connection(conn)


if __name__ == "__main__":

    print("OK")
    #print (obtener_datos_inventarios_jde(46))
    #print (obtener_nombre_archivo(135))
    #insertar_Fecha_Vuelo_Elementos_JED(1167,35)
    #Exportar_Elementos_JED_a_csv(46                             )
    #now = datetime.datetime.now()
    #print (now)
    #dron=Dron_GET_Boton_Envio_Datos()
    #print (dron)
    #if now > dron:
    #    print("OK")

   # with open("output_inventario.json", "r") as file:
   #     json_content = file.read()
    
    #print("OK")
    #print(insertar_elementos_jde(2, json_content))


def predict_inventory_zone(id_inventario):
    """
    Predice la zona de un inventario basado en el análisis del archivo CSV original.
    
    Flujo:
    1. Obtener nombre del archivo desde Inventario_Vuelos usando ID_Inventario
    2. Abrir el archivo CSV desde Dron_Folder (.env)
    3. Extraer EPCs (limpiar espacios, convertir a mayúsculas)
    4. Para cada EPC, buscar en Elementos_JDE para obtener Ubicacion
    5. Calcular distribución de zonas
    6. Predecir zona basado en porcentajes
    
    Reglas de predicción:
    1. Si una zona tiene >60% de los EPCs → retorna esa zona
    2. Si múltiples zonas con 20-60% de distribución → retorna 'PT' (todas las zonas)
    3. Si ninguna zona cumple criterios → retorna None (Unknown)
    
    Args:
        id_inventario (int): ID del inventario a analizar
    
    Returns:
        dict: {
            'zone': 'PF1'|'PF2'|'PF5'|'PT'|None,
            'confidence': float (porcentaje de la zona más alta, 0-100),
            'breakdown': dict (desglose de porcentajes por zona),
            'total_elements': int (total de EPCs analizados)
        }
    
    Ejemplo:
        >>> predict_inventory_zone(46)
        {
            'zone': 'PF2',
            'confidence': 83.5,
            'breakdown': {'PF1': 5.0, 'PF2': 83.5, 'PF5': 11.5},
            'total_elements': 200
        }
    """
    try:
        conn = get_db_connection()
        
        # Paso 1: Obtener el nombre del archivo desde Inventario_Vuelos
        sql_get_filename = 'SELECT Nombre_Archivo FROM Inventario_Vuelos WHERE ID = ?'
        df_filename = execute_sql_query(sql_get_filename, conn, params=(id_inventario,))
        
        if df_filename is None or len(df_filename) == 0:
            return {
                'zone': None,
                'confidence': 0,
                'breakdown': {},
                'total_elements': 0,
                'error': f'Inventory ID {id_inventario} not found in Inventario_Vuelos'
            }
        
        filename = df_filename.iloc[0]['Nombre_Archivo']
        
        # Paso 2: Construir ruta del archivo y abrirlo
        dron_folder = os.getenv('Dron_Folder')
        if not dron_folder:
            close_connection(conn)
            return {
                'zone': None,
                'confidence': 0,
                'breakdown': {},
                'total_elements': 0,
                'error': 'Dron_Folder not configured in .env'
            }
        
        file_path = os.path.join(dron_folder, filename)
        
        if not os.path.exists(file_path):
            close_connection(conn)
            return {
                'zone': None,
                'confidence': 0,
                'breakdown': {},
                'total_elements': 0,
                'error': f'File not found: {file_path}'
            }
        
        # Paso 3: Leer el archivo CSV y extraer EPCs
        try:
            df_file = pd.read_csv(file_path)
        except Exception as e:
            close_connection(conn)
            return {
                'zone': None,
                'confidence': 0,
                'breakdown': {},
                'total_elements': 0,
                'error': f'Error reading CSV file: {str(e)}'
            }
        
        # Verificar que existe la columna EPC
        if 'EPC' not in df_file.columns:
            close_connection(conn)
            return {
                'zone': None,
                'confidence': 0,
                'breakdown': {},
                'total_elements': 0,
                'error': 'EPC column not found in CSV file'
            }
        
        # Limpiar EPCs: convertir a string, eliminar espacios y convertir a mayúsculas
        epcs_from_file = (df_file['EPC']
            .astype(str)  # Convertir a string (convierte NaN a 'nan')
            .str.strip()  # Remover espacios al inicio/final
            .str.upper()  # Convertir a mayúsculas
            .str.replace(' ', '')  # Remover espacios internos
            .tolist())
        
        # Filtrar valores inválidos: vacíos, 'NAN', '00 00 00', o muy cortos
        epcs_from_file = [
            epc for epc in epcs_from_file 
            if epc and epc != 'NAN' and epc != 'NONE' and len(epc.strip()) > 5
        ]
        
        if not epcs_from_file:
            close_connection(conn)
            return {
                'zone': None,
                'confidence': 0,
                'breakdown': {},
                'total_elements': 0,
                'error': 'No valid EPCs found in CSV file'
            }
        
        # Paso 4: OPTIMIZACIÓN - Buscar todos los EPCs de una sola vez (1 query en lugar de N queries)
        # Anterior: For loop hacía 1 query por EPC = extremadamente lento si hay 300+ EPCs
        # Nuevo: Una sola query con IN clause = muy rápido
        
        zone_counts = {}
        found_count = 0
        
        # Crear placeholders para SQL: ? por cada EPC
        placeholders = ','.join(['?' for _ in epcs_from_file])
        
        sql_find_all_epcs = f'''
            SELECT ej.EPC, ij.Ubicacion 
            FROM Elementos_JDE ej
            JOIN Inventarios_JDE ij ON ej.ID_Inventario = ij.ID
            WHERE ej.EPC IN ({placeholders})
        '''
        
        try:
            df_epc_locations = execute_sql_query(sql_find_all_epcs, conn, params=tuple(epcs_from_file))
            
            if df_epc_locations is not None and len(df_epc_locations) > 0:
                # Procesar resultados
                for idx, row in df_epc_locations.iterrows():
                    ubicacion = row['Ubicacion']
                    zone_counts[ubicacion] = zone_counts.get(ubicacion, 0) + 1
                    found_count += 1
        except Exception as e:
            logging.error(f"[PREDICT] Error in SQL query: {str(e)}")
            close_connection(conn)
            return {
                'zone': None,
                'confidence': 0,
                'breakdown': {},
                'total_elements': len(epcs_from_file),
                'error': f'Error querying EPCs: {str(e)}'
            }
        
        close_connection(conn)
        
        # Si no se encontraron EPCs en la BD
        if found_count == 0:
            return {
                'zone': None,
                'confidence': 0,
                'breakdown': {},
                'total_elements': len(epcs_from_file),
                'error': 'No EPCs from file found in Elementos_JDE'
            }
        
        # Paso 5: Calcular porcentajes por zona
        total_found = sum(zone_counts.values())
        
        breakdown = {}
        for zona, count in sorted(zone_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_found * 100)
            breakdown[zona] = round(percentage, 2)
        
        # Paso 6: Obtener la zona con mayor porcentaje
        top_zone = max(zone_counts.items(), key=lambda x: x[1])[0]
        top_percentage = breakdown[top_zone]
        
        # Paso 7: Aplicar reglas de predicción
        if top_percentage > 60:
            # Zona clara: una zona domina >60%
            predicted_zone = top_zone
            confidence = top_percentage
        else:
            # Verificar si es distribución mixta (múltiples zonas entre 20-60%)
            high_distribution_zones = [z for z, p in breakdown.items() if p >= 20]
            
            if len(high_distribution_zones) >= 2:
                # Distribución mixta: retornar PT (todas las zonas)
                predicted_zone = 'PT'
                confidence = None  # No hay confianza en distribución mixta
            else:
                # Ninguna zona clara, pero tampoco mixta
                predicted_zone = None
                confidence = top_percentage if top_percentage >= 20 else 0
        
        return {
            'zone': predicted_zone,
            'confidence': confidence,
            'breakdown': breakdown,
            'total_elements': total_found,
            'epcs_analyzed': len(epcs_from_file),
            'epcs_found': found_count,
            'file_analyzed': filename
        }
        
    except Exception as e:
        print(f"[ERROR] Error prediciendo zona de inventario: {e}")
        return {
            'zone': None,
            'confidence': 0,
            'breakdown': {},
            'total_elements': 0,
            'error': str(e)
        }

