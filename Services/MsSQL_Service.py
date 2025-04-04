import datetime
import os
import pyodbc
import pandas as pd
import json
from dotenv import load_dotenv
from Services import LogService  # Assuming these modules are already defined

#import LogService
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

def insertar_ruta_video_inventario_jde(ID_Vuelo, ruta_video):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

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
        conn.close()

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
        cursor = conn.cursor()

        
        # 4. Read the SQL Server table into a Pandas DataFrame (for efficient matching)
        
        sql_query  = '''SELECT EPC, ID_Inventario, Fecha_Lectura FROM Elementos_JDE Where ID_Inventario = ?'''
        df_sql = pd.read_sql_query(sql_query, conn, params=(id_inventario,))  # Parameterize the query


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
        conn.close()
        #print("Update Complete")

    
        return True
    except Exception as e:
        print(f"Error Actualizando estdo Inventario. Error: {e}")
        return None


def Exportar_Elementos_JED_a_csv(id_inventario):

    try:
        # 3. Establish a connection to the SQL Server database
        conn = get_db_connection()
        cursor = conn.cursor()

        
        # 4. Read the SQL Server table into a Pandas DataFrame (for efficient matching)
        
        sql_query  = '''SELECT * FROM Elementos_JDE Where ID_Inventario = ? and Resultado='Ok' ORDER BY Fecha_lectura asc  '''
        df_sql = pd.read_sql_query(sql_query, conn, params=(id_inventario,))  # Parameterize the query

        df_sql.to_csv(str(id_inventario) + "_Elementos_JDE.csv",index=False,sep=";", encoding="utf-8", decimal=",")

       
        conn.close()
        #print("Update Complete")

    
        return (str(id_inventario) + "_Elementos_JDE.csv")
    except Exception as e:
        print(f"Error Obteniendo  Inventario. Error: {e}")
        return None



def Exportar_Elementos_JED_a_df(id_inventario):

    try:
        # 3. Establish a connection to the SQL Server database
        conn = get_db_connection()
        cursor = conn.cursor()

        
        # 4. Read the SQL Server table into a Pandas DataFrame (for efficient matching)
        
        sql_query  = '''SELECT * FROM Elementos_JDE Where ID_Inventario = ? and Resultado='Ok' ORDER BY Fecha_lectura asc  '''
        df_sql = pd.read_sql_query(sql_query, conn, params=(id_inventario,))  # Parameterize the query

        conn.close()
        #print("Update Complete")

    
        return df_sql
    except Exception as e:
        print(f"Error Obteniendo  Inventario. Error: {e}")
        return None
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
    

def Dron_GET_Boton_Envio_Datos():
    
    time_to_wait=60

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query='''
        SELECT TOP 1  FORMAT(Fecha,'yyyy-MM-dd HH:mm:ss.ff') as Fecha FROM Dron_Stop_Button ORDER BY Fecha desc'''
        
        cursor.execute(query)
        
        result = cursor.fetchone()
        conn.close()
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
        cursor = conn.cursor()

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
            cursor.close()
            conn.close()
    


def obtener_datos_inventarios_jde(ID_Vuelo):
    
    conn = get_db_connection() #Get the connection.
    if conn is None:
        return False #exit if connection failed.

    try:
        cursor = conn.cursor()
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
            cursor.close()
            conn.close()


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
