# streamlit run Inventarios_Pendientes.py

import pandas as pd
import requests
import streamlit as st
import sqlite3

# Función para obtener el total de inventarios pendientes
def obtener_total_inventarios_pendientes():
    conn = sqlite3.connect('..\\inventario.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) FROM Inventario_Vuelos
        WHERE Estado_Inventario = 'Pendiente'
    ''')

    total_inventarios_pendientes = cursor.fetchone()[0]
    conn.close()

    return total_inventarios_pendientes

def obtener_datos_inventarios_jde():
    conn = sqlite3.connect('..\\inventario.db')
    cursor = conn.cursor()

    # Query to fetch all data from the table
    cursor.execute('''
        SELECT j.ID, j.ID_Vuelo, v.Fecha_Vuelo, v.Tiempo_Vuelo, j.Fecha_Inventario, 
               j.Elementos_OK, j.Elementos_Faltantes, j.Elementos_Sobrantes, 
               j.Porcentaje_Lectura, j.NumeroConteo, j.Sucursal, j.Ubicacion, 
               j.TransactionId
        FROM Inventarios_JDE j
        JOIN Inventario_Vuelos v ON j.ID_Vuelo = v.ID
        ORDER BY j.ID DESC
    ''')

    # Fetch all rows
    data = cursor.fetchall()

    # Close the connection
    conn.close()

    return data
# Función para obtener los datos de los inventarios pendientes
def obtener_datos_inventarios_pendientes():
    conn = sqlite3.connect('..\\inventario.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ID, Fecha_Vuelo, N_Elementos, Tiempo_Vuelo FROM Inventario_Vuelos
        WHERE Estado_Inventario = 'Pendiente'
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
            st.experimental_rerun(url=f"http://127.0.0.1:5100/actualizar-estado-inventario?sucursal={tipo_inventario}&Ubicacion={zona}&ID={row['ID Inventario']}")
            # Actualizar los datos de la tabla
            datos = obtener_datos_inventarios_pendientes()
            st.table(datos)

def obtener_elementos_jde(id_inventario):
    conn = sqlite3.connect('..\\inventario.db')
    cursor = conn.cursor()
    
    query = '''SELECT EPC, Resultado, Ubicacion, CodigoArticulo 
               FROM Elementos_JDE 
               WHERE ID_Inventario = ?'''
    
    cursor.execute(query, (id_inventario,))
    elementos = cursor.fetchall()
    
    conn.close()
    return elementos

def Generar_Inventario(url):
  """Consumes the specified URL and returns the response."""
  response = requests.post(url)
  if response.status_code == 200:
    return "Inventario procesado con éxito por JD Edwards"
  else:
    raise Exception(f"Error procesando Inventario con JD Edwards")

def show_popup(result):
  """Shows a popup with the result."""
  st.success(result)


#Inicio Creacion de la Pagina ----------------------------------------------
st.set_page_config(layout="wide")

# Create two columns for the logo and title
col1, col2 = st.columns([1, 4])  # Adjust the ratios as necessary
# Add logo
with col1:
    
    st.image('images/SG_Logo.png', width=250)  # Adjust the width as necessary
# Add title in the second column
with col2:
    #st.title("Inventarios Patio Mina 2")
    st.markdown("<h1 style='text-align: center;'>Inventarios Patio Mina 2</h1>", unsafe_allow_html=True)


css_style = """
<style>
.stHorizontalBlock2  {
    border-bottom: 1px solid #ccc;
}
</style>
"""

st.markdown(css_style, unsafe_allow_html=True)

# Initialize session state for the expanders
if 'expand_resumen_inventario' not in st.session_state:
    st.session_state.expand_resumen_inventario = False
if 'selected_inventario_id' not in st.session_state:
    st.session_state.selected_inventory = None


    # Crear la página "Inventarios Pendientes"


with st.expander("Inventarios Pendientes",expanded=True):

    st.title("Inventarios Pendientes")
   
    #Obtener inventarios pendientes
    datos = obtener_datos_inventarios_pendientes()
    total_seconds =sum(row[3] for row in datos)
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    #
     # Mostrar el total de inventarios pendientes
    

    st.markdown(f"""
    <div style="display: flex; align-items: center;">
    <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
        <h1>{len(datos)}</h1>
        <p>Inventarios Pendientes</p>
    </div>

    <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
        <h1>{sum(row[2] for row in datos)}</h1>
        <p>Elementos Detectados</p>
    </div>

    <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
        <h1>{minutes:02}:{seconds:02}</h1>
        <p>Tiempo de Vuelo</p>
    </div>
    </div>

    """, unsafe_allow_html=True)





    # Mostrar la tabla de inventarios pendientes
    

    st.subheader("Detalles de Inventarios Pendientes")
    headers = st.columns([1, 2, 2, 2, 2, 2,2], gap="small", vertical_alignment="top")
    headers[0].write("ID")
    headers[1].write("Fecha de Vuelo")
    headers[2].write("Elementos Detectados")
    headers[3].write("Tiempo de Vuelo[s]")
    headers[4].write("Tipo Inventario")
    headers[5].write("Zona")
    headers[6].write("Acción")

    if datos:
        for inventario in datos:
            # Each row of the table
            col1, col2, col3, col4, col5, col6,col7 = st.columns([1, 2, 2, 2,2, 2,2], gap="medium", vertical_alignment="center")

            # Column 1: ID Inventario
            col1.write(inventario[0])

            # Column 2: Fecha de Vuelo
            col2.write(inventario[1])

            # Column 3: Elementos Detectador
            col3.write(inventario[2])
            # Column 3: Elementos Detectador

            col4.write(inventario[3])


            # Column 4: Tipo Inventario dropdown
            tipo_inventario = col5.selectbox("", ["Parcial", "Completo"], key=f"tipo_{inventario[0]}",label_visibility="collapsed")

            zona_disabled = True if tipo_inventario == "Completo" else False
            # Column 5: Zona dropdown
            zona = col6.selectbox("", ["PF1", "PF2", "PT"], key=f"zona_{inventario[0]}", label_visibility="collapsed",disabled=zona_disabled)

            # Column 6: Acción button
            if col7.button("Iniciar Inventario", key=f"iniciar_{inventario[0]}", help="Enviar Inventario a JD Edwards"): #Si el boton es presionado entonces:
                # When the button is clicked, refer to the inventory update page
                 # Disable the button
                st.session_state.button_disabled = True
                with st.spinner("Procesando..."):
                    try:
                        result = Generar_Inventario(f"http://127.0.0.1:5100/dron/actualizar-inventario?Tipo_Inventario={tipo_inventario}&Ubicacion={zona}&ID={inventario[0]}")
                        show_popup(result)
                        datos = obtener_datos_inventarios_pendientes() #Actualizar Tabla
                         # Disable the button
                        
                    except Exception as e:
                        st.error(f"Error Conectado a Servidor, por favor, intenta mas tarde!")
                        st.session_state.button_disabled = False
                
                
                #st.experimental_rerun(f"http://127.0.0.1:5100/actualizar-estado-inventario?sucursal={tipo_inventario}&Ubicacion={zona}&ID={inventario[0]}")

    else:
        st.write("No hay inventarios pendientes.")


with st.expander("Inventarios Realizados",expanded=False):

        
        st.title("Inventarios Realizados")
        st.subheader("Patio 2 Mina")
        # Get the data
        datosJDE = obtener_datos_inventarios_jde()
        # Create a Pandas DataFrame to easily display it in a table
        df = pd.DataFrame(datosJDE, columns=[
            "ID", "ID_Vuelo", "Fecha_Vuelo", "Tiempo_Vuelo", "Fecha_Inventario", 
            "Elementos_OK", "Elementos_Faltantes", "Elementos_Sobrantes", 
            "Porcentaje_Lectura", "NumeroConteo", "Sucursal", "Ubicacion", 
            "TransactionId"
        ])

        pt_rows = df[df['Ubicacion'] == "PT"]
         #Obtener inventarios pendientes
        average_porcentaje = df['Porcentaje_Lectura'].mean()

    #
     # Mostrar el total de inventarios pendientes
    

        st.markdown(f"""
        <div style="display: flex; align-items: center;">
        <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
            <h1>{len(datosJDE)}</h1>
            <p>Inventarios Realizados</p>
        </div>

        <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
            <h1>{len(pt_rows)}</h1>
            <p>Inventaros Completos</p>
        </div>

        <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
            <h1>{int(len(df)-len(pt_rows))}</h1>
            <p>Inventoarios Parciales</p>
        </div>
        <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
            <h1>{round(average_porcentaje,2)}%</h1>
            <p>Media de Lectura</p>
        </div>

  
        </div>

    """, unsafe_allow_html=True)
        

        # Pagination variables
        # Number of rows per page
        rows_per_page = 8
        if 'page' not in st.session_state:
            st.session_state.page = 0

        # Calculate total pages
        total_pages = (len(df) + rows_per_page - 1) // rows_per_page  # Ceiling division

        # Update start_row and end_row based on the current page
        start_row = st.session_state.page * rows_per_page
        end_row = start_row + rows_per_page

        # Show current page rows
        df_to_display = df.iloc[start_row:end_row]

        st.subheader("Detalles de Inventarios Realizados")

        headers = st.columns([2, 2, 2, 2, 2, 2, 2, 2, 2,1], gap="small", vertical_alignment="top")
        headers[0].write("Tipo Inventario")
        headers[1].write("Ubicación")
        headers[2].write("Fecha Inventario")
        headers[3].write("Fecha de Vuelo")
        headers[4].write("Tiempo de Vuelo[s]")
        headers[5].write("Correctos")
        headers[6].write("Faltantes")
        headers[7].write("Sobrantes")
        headers[8].write("Lectura [%]")
        headers[9].write("")
        

        if not df.empty:  # Check if the DataFrame is not empty
            for index, inventario in df_to_display.iterrows():  # Iterate over rows using iterrows()
                # Each row of the table
                col1, col2, col3, col4, col5, col6, col7, col8, col9,col10 = st.columns([2, 2, 2, 2, 2, 2, 2, 2, 2,1], gap="medium", vertical_alignment="center")

                # Determine Tipo_inventario based on Ubicacion
                Tipo_inventario = "Completo" if inventario["Ubicacion"] == "PT" else "Parcial"

               
                col1.write(Tipo_inventario)
                col2.write(inventario["Ubicacion"])
                col3.write(inventario["Fecha_Inventario"])
                col4.write(inventario["Fecha_Vuelo"])
                col5.write(inventario["Tiempo_Vuelo"])
                col6.write(inventario["Elementos_OK"])
                col7.write(inventario["Elementos_Faltantes"])
                col8.write(inventario["Elementos_Sobrantes"])
                col9.write(str(inventario["Porcentaje_Lectura"])+"%")

                # Botón de "Resumen"
                if col10.button("Ver", key=f"resumen_{inventario['ID']}"):
                    st.session_state.selected_inventory = inventario["ID"]
                    st.session_state.expand_resumen_inventario=True
             

        

        # Pagination buttons with center alignment
        # Pagination buttons with custom alignment
        col1, col2, col3 = st.columns([1, 2, 1])  # Create three columns with different widths

        with col3:  # Next button column (left)
            if st.button("Siguiente Página"):
                if st.session_state.page < total_pages - 1:
                    st.session_state.page += 1

        with col2:  # Page indicator column (center)
            st.write(f"Página {st.session_state.page + 1} de {total_pages}")

        with col1:  # Previous button column (right)
            if st.button("Página Anterior"):
                if st.session_state.page > 0:
                    st.session_state.page -= 1
      

with st.expander("Resumen Inventario",expanded=st.session_state.expand_resumen_inventario):

    st.title("Resumen Inventario")

    if st.session_state.selected_inventory:          
        resumen_inventario = obtener_elementos_jde(int(st.session_state.selected_inventory))

        # Mostrar detalles del inventario
        st.write("OK")



#st.sidebar.title("Menú")
#st.sidebar.button("Inventarios Pendientes", on_click=lambda: st.experimental_rerun("/inventarios-pendientes"))
#st.sidebar.button("Inventarios Realizados", on_click=lambda: st.experimental_rerun("/inventarios-realizados"))
#st.sidebar.button("Resumen Inventario", on_click=lambda: st.experimental_rerun("/resumen-inventario"))



