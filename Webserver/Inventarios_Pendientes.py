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

# Función para obtener los datos de los inventarios pendientes
def obtener_datos_inventarios_pendientes():
    conn = sqlite3.connect('..\\inventario.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ID, Fecha_Vuelo, N_Elementos FROM Inventario_Vuelos
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

st.title("Inventarios Patio Mina 2")

css_style = """
<style>
.stHorizontalBlock  {
    border-bottom: 1px solid #ccc;
}
</style>
"""

st.markdown(css_style, unsafe_allow_html=True)





    # Crear la página "Inventarios Pendientes"


with st.expander("Inventarios Pendientes",expanded=True):

    st.title("Inventarios Pendientes")
    # Mostrar el total de inventarios pendientes
    total_inventarios_pendientes = obtener_total_inventarios_pendientes()


    st.markdown(f"""
    <div style="background-color:green;padding:10px;border-radius:10px;text-align:center;width:150px;">
        <h1>{total_inventarios_pendientes}</h1>
        <p>Inventarios Pendientes</p>
    </div>
    """, unsafe_allow_html=True)


    # Mostrar la tabla de inventarios pendientes
    datos = obtener_datos_inventarios_pendientes()

    st.subheader("Detalles de Inventarios Pendientes")
    headers = st.columns([1, 2, 2, 2, 2, 2], gap="small", vertical_alignment="top")
    headers[0].write("ID")
    headers[1].write("Fecha de Vuelo")
    headers[2].write("Elementos Detectador")
    headers[3].write("Tipo Inventario")
    headers[4].write("Zona")
    headers[5].write("Acción")

    if datos:
        for inventario in datos:
            # Each row of the table
            col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 2,2, 2], gap="medium", vertical_alignment="center")

            # Column 1: ID Inventario
            col1.write(inventario[0])

            # Column 2: Fecha de Vuelo
            col2.write(inventario[1])

            # Column 3: Elementos Detectador
            col3.write(inventario[2])

            # Column 4: Tipo Inventario dropdown
            tipo_inventario = col4.selectbox("", ["Completo", "Parcial"], key=f"tipo_{inventario[0]}",label_visibility="collapsed")

            # Column 5: Zona dropdown
            zona = col5.selectbox("", ["PF1", "PF2", "PT"], key=f"zona_{inventario[0]}", label_visibility="collapsed")

            # Column 6: Acción button
            if col6.button("Iniciar Inventario", key=f"iniciar_{inventario[0]}", help="Enviar Inventario a JD Edwards"): #Si el boton es presionado entonces:
                # When the button is clicked, refer to the inventory update page
                with st.spinner("Loading..."):
                    try:
                        result = Generar_Inventario(f"http://127.0.0.1:5100/dron/actualizar-inventario?Tipo_Inventario={tipo_inventario}&Ubicacion={zona}&ID={inventario[0]}")
                        show_popup(result)
                        datos = obtener_datos_inventarios_pendientes() #Actualizar Tabla
                    except Exception as e:
                        st.error(f"Error Conectado a Servidor, por favor, intenta mas tarde!")
                
                
                #st.experimental_rerun(f"http://127.0.0.1:5100/actualizar-estado-inventario?sucursal={tipo_inventario}&Ubicacion={zona}&ID={inventario[0]}")

    else:
        st.write("No hay inventarios pendientes.")



#st.sidebar.title("Menú")
#st.sidebar.button("Inventarios Pendientes", on_click=lambda: st.experimental_rerun("/inventarios-pendientes"))
#st.sidebar.button("Inventarios Realizados", on_click=lambda: st.experimental_rerun("/inventarios-realizados"))
#st.sidebar.button("Resumen Inventario", on_click=lambda: st.experimental_rerun("/resumen-inventario"))