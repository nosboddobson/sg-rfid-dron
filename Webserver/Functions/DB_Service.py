import datetime
import os
import re
import pandas as pd
import requests
import streamlit as st
import pyodbc
from dotenv import load_dotenv
import time


# Load environment variables
load_dotenv(override=True)

# Connection details from .env file
DB_SERVER = os.getenv('DB_DRON_SERVER')
DB_DATABASE = os.getenv('DB_DRON_DATABASE')
DB_USERNAME = os.getenv('DB_DRON_USERNAME')
DB_PASSWORD = os.getenv('DB_DRON_PASSWORD')
DRON_FOLDER_PATH = os.getenv('DRON_FOLDER')

# Function to establish a connection to the MS SQL Server
def get_connection():
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"UID={DB_USERNAME};"
        f"PWD={DB_PASSWORD}"
    )
    return conn

def toggle_content_advanced():
        st.session_state.show_content_advanced = not st.session_state.show_content_advanced


def seconds_to_hhmmss(seconds):
  """Converts seconds to a string in HH:MM:SS format."""
  try:
    return str(datetime.timedelta(seconds=seconds))
  except ValueError:
    # Handle potential errors, such as negative seconds
    return "Invalid input"
  
  
# Function to get the total number of pending inventories
def obtener_total_inventarios_pendientes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) FROM Inventario_Vuelos
        WHERE Estado_Inventario = 'Pendiente'
    ''')

    total_inventarios_pendientes = cursor.fetchone()[0]
    conn.close()

    return total_inventarios_pendientes

# Function to get data from Inventarios_JDE and related Inventario_Vuelos
def obtener_datos_inventarios_jde():
    conn = get_connection()
    cursor = conn.cursor()

    # Query to fetch all data from the table
    cursor.execute('''
        SELECT TOP (100) j.ID, j.ID_Vuelo, v.Fecha_Vuelo, v.Tiempo_Vuelo, j.Fecha_Inventario, 
               j.Elementos_OK, j.Elementos_Faltantes, 
               j.Porcentaje_Lectura, j.NumeroConteo, j.Sucursal, j.Ubicacion, 
               j.TransactionId, (v.N_elementos - j.Elementos_OK) AS Elementos_Sobrantes,
               v.N_elementos, j.Imagen_Vuelo, j.Video_Vuelo    
        FROM Inventarios_JDE j
        JOIN Inventario_Vuelos v ON j.ID_Vuelo = v.ID
        ORDER BY j.ID DESC
    ''')

    columns = [column[0] for column in cursor.description]

    # Obtener resultados como una lista de tuplas
    results = cursor.fetchall()

    # Crear DataFrame solo si hay resultados
    df = pd.DataFrame([list(row) for row in results], columns=columns) if results else pd.DataFrame(columns=columns)

    # Close the connection
    conn.close()

    return df

# Function to get data of pending inventories
def obtener_datos_inventarios_pendientes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ID, Fecha_Vuelo, N_Elementos, Tiempo_Vuelo FROM Inventario_Vuelos
        WHERE Estado_Inventario = 'Pendiente' AND N_Elementos >0 ORDER BY ID DESC
    ''')

    datos = cursor.fetchall()
    conn.close()

    return datos

def crear_fila_interactiva(index, row):
    with st.form(key=f"form_{index}"):
        tipo_inventario = st.selectbox("Tipo Inventario", ["Completo", "Parcial"], key=f"tipo_inventario_{index}")
        zona = st.selectbox("Zona", ["PF1", "PF2", "PT"], key=f"zona_{index}")
        if st.form_submit_button("Iniciar Inventario"):
            # Actualizar el estado del inventario (simulando la llamada a la API)
            st.rerun(url=f"http://127.0.0.1:5100/actualizar-estado-inventario?sucursal={tipo_inventario}&Ubicacion={zona}&ID={row['ID Inventario']}")
            # Actualizar los datos de la tabla
            datos = obtener_datos_inventarios_pendientes()
            st.table(datos)

# Function to retrieve JDE elements by inventory ID
def obtener_elementos_jde(id_inventario):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = '''SELECT EPC, Resultado, Ubicacion, CodigoArticulo 
               FROM Elementos_JDE 
               WHERE ID_Inventario = ?'''
    
    cursor.execute(query, (id_inventario,))
    elementos = cursor.fetchall()
    #print(elementos)
    df_resumen_columns = ["Número de etiqueta", "Resultado", "Ubicación", "Código artículo"]
    #df_resumen = pd.DataFrame(elementos)

    df = pd.DataFrame([list(row) for row in elementos], columns=df_resumen_columns) if elementos else pd.DataFrame(columns=elementos)
    
    
    conn.close()
    return df

def Generar_Inventario(url):
    """Consumes the specified URL and returns the response."""

    response = requests.post(url)
    if response.status_code == 200:
        return "Inventario procesado con éxito por JD Edwards"
    else:
        raise Exception(f"Error procesando Inventario con JD Edwards _ " + str(url))
    
def Eliminar_Inventario(url):
    """Consumes the specified URL and returns the response."""
    response = requests.post(url)
    if response.status_code == 200:
        return "Inventario Eliminado con éxito"
    else:
        raise Exception(f"Error eliminando Inventario")

def show_popup(result):
    """Shows a popup with the result."""
    st.success(result)

def split_frame(input_df, rows):
    df = [input_df.loc[i: i + rows - 1, :] for i in range(0, len(input_df), rows)]
    return df

@st.dialog("Eliminar Inventario")
def eliminar_inventario_dialog(inventario):
    st.markdown(""" ### ¿Estas seguro que quieres eliminar el inventario?""")
    # Confirmation buttons
    cole1, cole2 = st.columns(2)
    
    with cole1:
        if st.button("Si"):
            try:
                result = Eliminar_Inventario(f"http://127.0.0.1:5100/dron/eliminar-inventario?ID={inventario}")
                show_popup(result)
                time.sleep(2)
                #datos = obtener_datos_inventarios_pendientes() #Actualizar Tabla
                st.rerun()
                # Disable the button
                
            except Exception as e:
                st.error(f"dbs Error Conectado a Servidor, por favor, intenta mas tarde!")

    with cole2:
        if st.button("No"):
            st.rerun()

# Function to get data of pending inventories
def obtener_datos_inventarios_pendientes():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ID, Fecha_Vuelo, N_Elementos, Tiempo_Vuelo FROM Inventario_Vuelos
        WHERE Estado_Inventario = 'Pendiente' AND N_Elementos >0 ORDER BY ID DESC
    ''')

    datos = cursor.fetchall()
    conn.close()

    return datos


def obtener_datos_Log_Vuelos():
    conn = get_connection()
    cursor = conn.cursor()

    

    cursor.execute('''
        SELECT TOP 300 ID,Nombre_Archivo, Fecha_Vuelo, N_Elementos, Tiempo_Vuelo, Estado_Inventario 
        FROM Inventario_Vuelos
        ORDER BY Fecha_Vuelo DESC
    ''')

    columns = [column[0] for column in cursor.description]

    # Obtener resultados como una lista de tuplas
    results = cursor.fetchall()

    # Crear DataFrame solo si hay resultados
    df = pd.DataFrame([list(row) for row in results], columns=columns) if results else pd.DataFrame(columns=columns)

    # Join DRON_FOLDER_PATH with Nombre_Archivo
    if not df.empty:
        df['Nombre_Archivo'] = df['Nombre_Archivo'].apply(
            lambda x: os.path.join(DRON_FOLDER_PATH, x) if x else x
        )

    
    # Close the connection
    conn.close()

    return df

def seconds_to_hhmmss(seconds):
  """Converts seconds to a string in HH:MM:SS format."""
  try:
    return str(datetime.timedelta(seconds=seconds))
  except ValueError:
    # Handle potential errors, such as negative seconds
    return "Invalid input"


def format_seconds_HHMMSS(seconds):
    """Formats seconds into HH:MM:SS, always showing two digits for hours."""
    td = datetime.timedelta(seconds=seconds)
    total_seconds = td.total_seconds()
    hours = int(total_seconds // 3600)  # Integer division for hours
    minutes = int((total_seconds % 3600) // 60) # Modulo and integer division for minutes
    seconds = int(total_seconds % 60) #Modulo for seconds

    try:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except ValueError:
    # Handle potential errors, such as negative seconds
        return "Invalid input"
    

def format_date(date_string):
    
    timestamp = pd.Timestamp(date_string)
    formatted_date = timestamp.strftime('%d/%m/%Y')
        # We don't need the time part for formatting to dd/mm/yyyy.
    try:
        if formatted_date:
            return formatted_date
        else: 
            return None
        
    except ValueError:
            return None #Handles invalid date values (like 30th of February)
 

def format_time(date_string):
    
    timestamp = pd.Timestamp(date_string)
    formatted_date = timestamp.strftime('%H:%M')
        # We don't need the time part for formatting to dd/mm/yyyy.
    try:
        if formatted_date:
            return formatted_date
        else: 
            return None
        
    except ValueError:
            return None #Handles invalid date values (like 30th of February)
    
def format_datetime(date_string):
    
    timestamp = pd.Timestamp(date_string)
    formatted_date = timestamp.strftime('%d/%m/%Y %H:%M')
        # We don't need the time part for formatting to dd/mm/yyyy.
    try:
        if formatted_date:
            return formatted_date
        else: 
            return None
        
    except ValueError:
            return None #Handles invalid date values (like 30th of February)
def add_seconds_to_timestamp_string(timestamp_str, seconds_str):
    """Adds seconds to a timestamp string and returns the time in HH:MM format.

    Args:
        timestamp_str: A string representing the timestamp (YYYY-MM-DD HH:MM:SS).
        seconds_str: A string representing the number of seconds to add.

    Returns:
        A string representing the new time in HH:MM format, or None if error.
    """
    try:
        # 1. Create a Pandas Timestamp object from the string
        timestamp = pd.Timestamp(timestamp_str)

        # 2. Convert seconds_str to an integer
        seconds_to_add = int(seconds_str)

        # 3. Create a timedelta object
        delta = datetime.timedelta(seconds=seconds_to_add)

        # 4. Add the timedelta
        new_timestamp = timestamp + delta

        # 5. Format the new timestamp as HH:MM
        new_time_str = new_timestamp.strftime("%H:%M")

        return new_time_str
    except (ValueError, TypeError):
        return None
    
def Dron_SET_Boton_Envio_Datos_Hora(ID_Usuario):
    try :
        conn = get_connection()
        cursor = conn.cursor()

        now = datetime.datetime.now()
        #print (str(now))
        query = '''
                INSERT INTO Dron_Stop_Button (USUARIO, Fecha)
                VALUES (?, ?)
            '''
        
        cursor.execute(query, (ID_Usuario,str(now)))
        conn.commit()
      
        conn.close()
        return True
        
    except (ValueError, TypeError):
        return None
    
def get_last_heartbeat_and_compare():
    """
    Retrieves the last heartbeat from the Dron_Heartbeats table, compares its timestamp
    with the current time, and returns True if the difference is within 60 seconds,
    False otherwise.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Get the last heartbeat
        cursor.execute("SELECT TOP 1 HeartbeatTime FROM Dron_Heartbeats ORDER BY HeartbeatTime DESC")
        last_heartbeat_row = cursor.fetchone()

        if last_heartbeat_row:
            last_heartbeat_time = last_heartbeat_row[0]  # Extract the datetime object
            current_time = datetime.datetime.now()

            time_difference = abs((current_time - last_heartbeat_time).total_seconds())

            return time_difference <= 60
        else:
            # No heartbeats found
            return False

    except pyodbc.Error as db_err:
        print(f"Heartbeat Database error occurred: {db_err}")
        return False

    except Exception as e:
        print(f"Heartbeat An unexpected error occurred: {e}")
        return False

    finally:
        if conn:
            cursor.close()
            conn.close()