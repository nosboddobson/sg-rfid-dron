import datetime
import os
import pandas as pd
import requests
import streamlit as st
import pyodbc
from dotenv import load_dotenv
import time
from streamlit_ldap_authenticator import Authenticate, Connection, UserInfos
from typing import Optional
from streamlit_modal import Modal


# Load environment variables
load_dotenv(override=True)

# Connection details from .env file
DB_SERVER = os.getenv('DB_DRON_SERVER')
DB_DATABASE = os.getenv('DB_DRON_DATABASE')
DB_USERNAME = os.getenv('DB_DRON_USERNAME')
DB_PASSWORD = os.getenv('DB_DRON_PASSWORD')

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
        SELECT j.ID, j.ID_Vuelo, v.Fecha_Vuelo, v.Tiempo_Vuelo, j.Fecha_Inventario, 
               j.Elementos_OK, j.Elementos_Faltantes, 
               j.Porcentaje_Lectura, j.NumeroConteo, j.Sucursal, j.Ubicacion, 
               j.TransactionId, (v.N_elementos - j.Elementos_OK) AS Elementos_Sobrantes
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
        raise Exception(f"Error procesando Inventario con JD Edwards")
    
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
                st.error(f"Error Conectado a Servidor, por favor, intenta mas tarde!")

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
        SELECT TOP 300 ID, Fecha_Vuelo, N_Elementos, Tiempo_Vuelo, Estado_Inventario 
        FROM Inventario_Vuelos
        ORDER BY Fecha_Vuelo DESC
    ''')

    columns = [column[0] for column in cursor.description]

    # Obtener resultados como una lista de tuplas
    results = cursor.fetchall()

    # Crear DataFrame solo si hay resultados
    df = pd.DataFrame([list(row) for row in results], columns=columns) if results else pd.DataFrame(columns=columns)

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
  