
from time import sleep
import requests
import streamlit as st
import plotly.express as px
from menu import make_navbar
from Functions import DB_Service as DB
from Functions import Reuse_Service as Reuse




           
#Inicio Creacion de la Pagina -----------------------------------------------------------------------------------------

st.set_page_config(page_title="Log de Vuelos Sierra Gorda",layout="wide")

#make_sidebar()
make_navbar()

Reuse.Load_css('Functions/CSS_General.css')




with st.expander("Log de Vuelos",expanded=True):

    #st.title("Vuelos Realizados")
    
    #Obtener inventarios pendientes
    datos = DB.obtener_datos_Log_Vuelos()
    
    #
    # Mostrar el total de inventarios pendientes
    

    st.markdown(f"""
    <div style="display: flex; align-items: center;">
    <div style="display:inline-block;background-color:black;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
        <h1>{len(datos)}</h1>
        <p>Nº de Vuelos</p>
    </div>
    <div style="display:inline-block;background-color:black;padding:10px;border-radius:10px;text-align:center;width:600px;margin-right:10px;">
        <h1>{DB.format_datetime(datos.iloc[0]["Fecha_Vuelo"])}</h1>
        <p>Último Vuelo</p>
    </div>
    <div style="display:inline-block;background-color:black;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
        <h1>{datos[datos['Estado_Inventario'] == 'OK'].shape[0]}</h1>
        <p>Vuelos Procesados</p>
    </div>
    <div style="display:inline-block;background-color:black;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
        <h1>{datos[datos['N_Elementos'] == 0].shape[0]}</h1>
        <p>Vuelos Descartados</p>
    </div>
    <div style="display:inline-block;background-color:black;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
        <h1>{datos[datos['Estado_Inventario'] == 'Pendiente'].shape[0] }</h1>
        <p>Vuelos Pendientes</p>
    </div>

    </div>

    """, unsafe_allow_html=True)


    # Pagination variables
        # Number of rows per page
    rows_per_page = 50
    if 'page_Log' not in st.session_state:
        st.session_state.page_Log = 0

    # Calculate total pages
    total_pages = (len(datos) + rows_per_page - 1) // rows_per_page  # Ceiling division

    # Update start_row and end_row based on the current page
    start_row = st.session_state.page_Log * rows_per_page
    end_row = start_row + rows_per_page

    # Show current page rows
    df_to_display = datos.iloc[start_row:end_row]
    

    # Mostrar la tabla de inventarios pendientes
    


    st.subheader("Detalles de Vuelos")

    #selected_Limit=st.selectbox("Nº Elementos",["10","100","500","Todo"])


    headers = st.columns([1, 2, 2, 2,2,2], gap="small", vertical_alignment="center")
    headers[0].write("ID")
    headers[1].write("Fecha de Vuelo")
    headers[2].write("Elementos Detectados")
    headers[3].write("Tiempo de Vuelo[HH:MM:SS]")
    headers[4].write("Estado")
    headers[5].write("Acción")



    if not datos.empty:
        for index, inventario in df_to_display.iterrows():
            # Each row of the table
            col1, col2, col3, col4,col5,col6  = st.columns([1, 2, 2, 2,2,2], gap="medium", vertical_alignment="center")

            # Column 1: ID Inventario
            col1.write(inventario["ID"])

            # Column 2: Fecha de Vuelo
            col2.write(DB.format_datetime(inventario["Fecha_Vuelo"]))

            # Column 3: Elementos Detectador
            col3.write(inventario["N_Elementos"])
            # Column 3: Elementos Detectador
            #minutes = str(inventario["Tiempo_Vuelo"] // 60).zfill(2)
            #seconds = str(inventario["Tiempo_Vuelo"] % 60).zfill(2)
            #col4.write(minutes+":"+seconds)
            col4.write(DB.format_seconds_HHMMSS(inventario["Tiempo_Vuelo"]))
            if inventario["Estado_Inventario"]=="OK":
                col5.write("Procesado")
            elif inventario["N_Elementos"] == 0:
                col5.write("Descartado")
            else:
                col5.write("Pendiente")

            with col6:
                # Create a unique key for each button to avoid conflicts
                button_key = f"cargar_nuevamente_{inventario['ID']}_{index}"
                
                if st.button("Subir Nuevamente", key=button_key):
                    try:
                            # Read the file from the path specified in Nombre_Archivo
                            file_path = inventario["Nombre_Archivo"]
                            
                            # Check if file exists
                            with open(file_path, 'rb') as file:
                                files = {'file': (file_path.split('/')[-1], file, 'application/octet-stream')}
                                
                                
                            # Make the API call
                                response = requests.post(
                                    "http://127.0.0.1:5100/upload",
                                    files=files
                                )
                                
                                if response.status_code == 200:
                                    st.success(f"Archivo subido correctamente para ID {inventario['ID']}")
                                    sleep(2)
                                    st.rerun()
                                else:
                                    st.error(f"Error al subir archivo. Código: {response.status_code}")
                            
                    except FileNotFoundError:
                        st.error(f"Archivo no encontrado: {file_path}")
                    except Exception as e:
                        st.error(f"Error al subir archivo: {str(e)}")

             
            st.write('')    
                #st.experimental_rerun(f"http://127.0.0.1:5100/actualizar-estado-inventario?sucursal={tipo_inventario}&Ubicacion={zona}&ID={inventario[0]}")

        col0,col1, col2, col3,col4 = st.columns([5,2, 2, 2,1])  # Create three columns with different widths

        with col3:  # Next button column (left)
            if st.button("Siguiente Página"):
                if st.session_state.page_Log < (total_pages - 1):
                    st.session_state.page_Log += 1

        with col2:  # Page indicator column (center)
            st.markdown(f"<p style='text-align: center;'>Página {st.session_state.page_Log + 1} de {total_pages}</p>", unsafe_allow_html=True)

        with col1:  # Previous button column (right)
            if st.button("Página Anterior"):
                if st.session_state.page_Log > 0:
                    st.session_state.page_Log -= 1
        st.write('')

    else:
        st.write("No hay vuelos registrados.")
        st.write('')

     # Pagination buttons with center alignment
        # Pagination buttons with custom alignment
    
        # Mostrar detalles del inventario
        #st.write("OK")



#st.sidebar.title("Menú")
#st.sidebar.button("inicio", on_click=lambda: st.experimental_rerun("/inventarios-pendientes"))
#st.sidebar.button("Patio Mina 2", on_click=lambda: st.experimental_rerun("/inventarios_Pendientes"))



#eliminar inventario; fondo gris fuera de los expander, colocar tiempo de vuelo promedio en vez de vuelo, crear api de eliminacion, desplegar tiempo de vuelo en MM:SS, eliminar PT, reemplazar zona por Ubicacion, Agregar numero de Contero en Listado de Inventarios

