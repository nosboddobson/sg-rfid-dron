

import os
import time
import pandas as pd
import streamlit as st
import plotly.express as px

import extra_streamlit_components as stx

from Functions import DB_Service as DB
from Functions import Reuse_Service as Reuse


#Inicio Creacion de la Pagina -----------------------------------------------------------------------------------------
st.set_page_config(page_title="Inventario Sierra Gorda",layout="wide")
from menu import make_sidebar
make_sidebar()
cookie_manager = stx.CookieManager()


st.markdown("<h1 style='text-align: center;'>Inventarios Pendientes Patio Mina 2</h1>", unsafe_allow_html=True)

Reuse.Load_css('Functions/CSS_General.css')



# Initialize session state for the expanders
if 'expand_resumen_inventario' not in st.session_state:
    st.session_state.expand_resumen_inventario = False
# Initialize session state for the expanders
if 'expand_inventario_Realizado' not in st.session_state:
    st.session_state.expand_inventario_Realizado = False
if 'expand_plano' not in st.session_state:
    st.session_state.expand_plano = False
if 'selected_inventory' not in st.session_state:
    st.session_state.selected_inventory = None
if 'show_popup_eliminar' not in st.session_state:
    st.session_state['show_popup_eliminar'] = False
if "show_content_advanced" not in st.session_state:
            st.session_state.show_content_advanced = True
if 'page' not in st.session_state:
            st.session_state.page = 0
            print ("st.session_state.page = 0")

if 'run_button' in st.session_state and st.session_state.run_button == True:
    st.session_state.running = True
else:
    st.session_state.running = False
    # Crear la página "Inventarios Pendientes"



####Comunicacion y estado de Dron
Dron_Status = DB.get_last_heartbeat_and_compare()
cold1, cold2,cold3,cold4 = st.columns([1, 1,1,3],gap="small",vertical_alignment="center")  # Adjust column widths as needed
st.write('') 

cold1.write(f"<p style='text-align: right;'>Estado de Dron :</p>", unsafe_allow_html=True)
     
if Dron_Status:

    cold2.write(f"<p style='text-align: left;'>En Linea ✔️</p>", unsafe_allow_html=True)

    datos1 = DB.obtener_datos_inventarios_pendientes()

    with cold3:
        if st.button("Solicitar a Dron Enviar Inventario",disabled=st.session_state.running, key='run_button'):
            
            DB.Dron_SET_Boton_Envio_Datos_Hora(cookie_manager.get(cookie='username'))
   
            # for i in range(6):
            #     st.toast("Esperando Inventario...")
            #     time.sleep(5)
            #     datos2 = DB.obtener_datos_inventarios_pendientes()
            #     if len(datos2)>len(datos1):
            #         st.toast("¡Inventario Recibido!", icon='🎉')
            #         st.balloons()
            #         time.sleep(5)
            #         success=True
            #         break
            #     success=False   
            # if not success:
            #         st.toast("¡Ningún Inventario Recibido!", icon='😞')
            #         time.sleep(5)


            # st.rerun()

            with cold4:
                with st.spinner("Esperando Inventario...", show_time=True):
                    time.sleep(10)
                    datos2 = DB.obtener_datos_inventarios_pendientes()
                    message_placeholder = st.empty()
                    if len(datos2)>len(datos1):
                        message_placeholder.success("¡Inventario Recibido!")
                    else:
                        message_placeholder.error("¡Ningún Inventario Recibido!")
                time.sleep(5)
                message_placeholder.empty()
                st.rerun()

else:
            cold2.write(f"<p style='text-align: left;'>Fuera de Linea ❌</p>", unsafe_allow_html=True)
                
st.write('')                    
            

with st.expander("Inventarios Pendientes",expanded=True):

# st.title("Inventarios Pendientes")

    #Obtener inventarios pendientes
    datos = DB.obtener_datos_inventarios_pendientes()
    #if len(datos) >0:
    #    total_seconds =sum(row[3] for row in datos)/len(datos)
    #else:
    #    total_seconds=0


    #
    # Mostrar el total de inventarios pendientes
    
    _ = '''
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

    <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:250px;margin-right:10px;">
        <h1>{DB.seconds_to_hhmmss(total_seconds)}</h1>
        <p>Tiempo de Vuelo Promedio</p>
    </div>
    </div>

    """, unsafe_allow_html=True)
    '''


    

    # Mostrar la tabla de inventarios pendientes
    

    #st.subheader("Detalles de Inventarios Pendientes")
    headers_Pendiente = st.columns([1, 2, 1, 1, 2, 1,1,1], gap="medium", vertical_alignment="center")
    header_texts = [
    "Nº",
    "Fecha de Vuelo",
    "Elementos Detectados",
    "Tiempo de Vuelo",
    "Tipo Inventario",
    "Zona",
    "",
    "" # Empty string for the last column
    ]
    #headers_Pendiente[0].write("Nº")
    #headers_Pendiente[1].write("Fecha de Vuelo")
    #headers_Pendiente[2].write("Elementos Detectados")
    #headers_Pendiente[3].write("Tiempo de Vuelo [HH:MM:SS]")
    #headers_Pendiente[4].write("Tipo Inventario")
    #headers_Pendiente[5].write("Zona")
    #headers_Pendiente[6].write("")
    #headers_Pendiente[7].write("")

    for i, header in enumerate(headers_Pendiente):
        with header:
            st.markdown(f"<p style='text-align: center;font-weight: bold;'>{header_texts[i]}</p>", unsafe_allow_html=True) 



    fila = len(datos)
    if datos:
        for inventario in datos:
            # Each row of the table
            col1, col2, col3, col4, col5, col6,col7,col8 = st.columns([1, 2, 1, 1, 2, 1,1,1], gap="medium", vertical_alignment="center")

            # Column 1: ID Inventario
            col1.write(f"<p style='text-align: center;'>{fila}</p>", unsafe_allow_html=True)
            fila -=1

            # Column 2: Fecha de Vuelo
            col2.write(f"<p style='text-align: center;'>{DB.format_datetime(inventario[1])}</p>", unsafe_allow_html=True)

            # Column 3: Elementos Detectador
            col3.write(f"<p style='text-align: center;'>{inventario[2]}</p>", unsafe_allow_html=True)
            # Column 3: Elementos Detectador
            #minutes = str(inventario[3] // 60).zfill(2)
            #seconds = str(inventario[3] % 60).zfill(2)
            #col4.write(minutes+":"+seconds)
            #col4.write(DB.seconds_to_hhmmss(inventario[3]))
            col4.write(f"<p style='text-align: center;'>{DB.format_seconds_HHMMSS(inventario[3])}</p>", unsafe_allow_html=True)
            # Column 4: Tipo Inventario dropdown
            tipo_inventario = col5.selectbox("Tipo Inventario", ["Parcial", "Completo"], key=f"tipo_{inventario[0]}",label_visibility="collapsed")

            zona_disabled = True if tipo_inventario == "Completo" else False
            # Column 5: Zona dropdown
            zona = col6.selectbox("Zona", ["SF0","SF1","SF2","PF1", "PF2", "PF3","PF4","PF5","PF6","PF7"], key=f"zona_{inventario[0]}", help="S= Shelving, P= Pasillo y F=Fila",label_visibility="collapsed",disabled=zona_disabled)

            # Column 6: Acción button
            if col7.button("Iniciar", key=f"iniciar_{inventario[0]}", help="Enviar Inventario a JD Edwards"): #Si el boton es presionado entonces:
                # When the button is clicked, refer to the inventory update page
                # Disable the button
                st.session_state.button_disabled = True
                with st.spinner("Procesando..."):
                    try:
                        result = DB.Generar_Inventario(f"http://127.0.0.1:5100/dron/actualizar-inventario?Tipo_Inventario={tipo_inventario}&Ubicacion={zona}&ID={inventario[0]}")
                        DB.show_popup(result)
                        datos =DB.obtener_datos_inventarios_pendientes() #Actualizar Tabla
                        st.rerun()
                        # Disable the button
                        
                    except Exception as e:
                        st.error(f"invp Error Conectado a Servidor, por favor, intenta mas tarde!" + str(e))
                        st.session_state.button_disabled = False
        
            
            if col8.button("Eliminar", key=f"Eliminar_{inventario[0]}", help="Eliminar inventario"): #Si el boton es presionado entonces:
                    
                    DB.eliminar_inventario_dialog(inventario[0])

                    
                        
                

            st.write('')    
                #st.experimental_rerun(f"http://127.0.0.1:5100/actualizar-estado-inventario?sucursal={tipo_inventario}&Ubicacion={zona}&ID={inventario[0]}")

    else:
        st.write("No hay inventarios pendientes.")
        st.write('')


with st.expander("Inventarios Realizados",expanded=st.session_state.expand_inventario_Realizado):

        
        #st.title("Inventarios Realizados")
        #st.subheader("Patio 2 Mina")
        # Get the data
        datosJDE = DB.obtener_datos_inventarios_jde()
    
        pt_rows = datosJDE[datosJDE['Ubicacion'] == "PT"]
    
        #Obtener inventarios pendientes
        average_porcentaje = datosJDE['Porcentaje_Lectura'].mean()


    #
    # Mostrar el total de inventarios pendientes
    

        _ = ''' st.markdown(f"""
        <div style="display: flex; align-items: center;">
        <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
            <h1>{len(datosJDE)}</h1>
            <p>Inventarios Realizados</p>
        </div>

        <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
            <h1>{len(datosJDE)}</h1>
            <p>Inventaros Completos</p>
        </div>

        <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
            <h1>{int(len(datosJDE)-len(pt_rows))}</h1>
            <p>Inventoarios Parciales</p>
        </div>
        <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:200px;margin-right:10px;">
            <h1>{round(average_porcentaje,2)}%</h1>
            <p>Media de Lectura</p>
        </div>


        </div>

    """, unsafe_allow_html=True)
        '''

        # Pagination variables
        # Number of rows per page
        rows_per_page = 5
        

        # Calculate total pages
        total_pages = (len(datosJDE) + rows_per_page - 1) // rows_per_page  # Ceiling division

        # Update start_row and end_row based on the current page
        start_row = st.session_state.page * rows_per_page
        end_row = start_row + rows_per_page
        #print("start_row: " + str(start_row))
        # Show current page rows
        df_to_display = datosJDE.iloc[start_row:end_row]
        #print (df_to_display)

        #st.subheader("Detalles de Inventarios Realizados")

        headers_Procesado = st.columns([2, 1, 2, 2, 2, 2, 2, 2, 2,2,2], gap="medium", vertical_alignment="top")
    
        _= '''headers[0].write("Tipo Inventario")
        headers[1].write("Zona")
        headers[2].write("Fecha Inventario")
        headers[3].write("Hora Inventario")
        headers[4].write("Tiempo de Vuelo")
        headers[5].write("Correctos")
        headers[6].write("Faltantes")
        headers[7].write("Sobrantes")
        headers[8].write("Lectura [%]")
        headers[9].write("Código JD")
        headers[10].write("") '''

        header_texts = [
            "Tipo Inventario",
            "Zona",
            "Fecha Inventario",
            "Hora Inventario",
            "Tiempo de Vuelo",
            "Correctos",
            "Faltantes",
            "Sobrantes",
            "Lectura [%]",
            "Código JD",
            ""  # Empty string for the last column
        ]        

        for i, header in enumerate(headers_Procesado):
            with header:
                st.markdown(f"<p style='text-align: center;font-weight: bold;'>{header_texts[i]}</p>", unsafe_allow_html=True) 


        if not datosJDE.empty:  # Check if the DataFrame is not empty
            for index, inventario in df_to_display.iterrows():  # Iterate over rows using iterrows()
                # Each row of the table
                col1, col2, col3, col4, col5, col6, col7, col8, col9,col10,col11 = st.columns([2, 1, 2, 2, 2, 2, 2, 2, 2,2,2], gap="medium", vertical_alignment="center")

                # Determine Tipo_inventario based on Ubicacion
                Tipo_inventario = "Completo" if inventario["Ubicacion"] == "PT" else "Parcial"

            
                col1.write(Tipo_inventario)
                col2.write(f"<p style='text-align: center;'>{inventario['Ubicacion']}</p>", unsafe_allow_html=True) 
                col3.write(f"<p style='text-align: center;'>{DB.format_date(inventario["Fecha_Inventario"])}</p>", unsafe_allow_html=True) 
                col4.write(f"<p style='text-align: center;'>{DB.format_time(inventario["Fecha_Inventario"])}</p>", unsafe_allow_html=True) 
                
                col5.write(f"<p style='text-align: center;'>{DB.format_seconds_HHMMSS(inventario["Tiempo_Vuelo"])}</p>", unsafe_allow_html=True) 
            
        

                #col6.write(inventario["Elementos_OK"])
                col6.write(f"<p class='data-ok' style='text-align: center;'>{inventario["Elementos_OK"]}</p>", unsafe_allow_html=True)
                
                #col7.write(inventario["Elementos_Faltantes"])
                col7.write(f"<p class='data-missing' style='text-align: center;'>{inventario["Elementos_Faltantes"]}</p>", unsafe_allow_html=True)

            
                #col8.write(inventario["Elementos_Sobrantes"])
                col8.write(f"<p class='data-excess' style='text-align: center;'>{inventario["Elementos_Sobrantes"]}</p>", unsafe_allow_html=True)
                col9.write(f"<p style='text-align: center;'>{str(inventario["Porcentaje_Lectura"])}%</p>", unsafe_allow_html=True) 
                col10.write(f"<p style='text-align: center;'>{str(inventario["NumeroConteo"])}</p>", unsafe_allow_html=True) 
            

                # Botón de "Resumen"
                if col11.button("Ver", key=f"resumen_{inventario['ID']}"):
                    st.session_state.selected_inventory = inventario["ID"]
                    st.session_state.expand_resumen_inventario=True
                    st.session_state.expand_inventario_Realizado = False
            

        

        # Pagination buttons with center alignment
        # Pagination buttons with custom alignment
        col0,col1, col2, col3,col4 = st.columns([5,2, 2, 2,1])  # Create three columns with different widths

        with col3:  # Next button column (left)
            if st.button("Siguiente Página"):
                if st.session_state.page < total_pages -1:
                    st.session_state.page += 1
                    st.rerun()

        with col2:  # Page indicator column (center)
            st.markdown(f"<p style='text-align: center;'>Página {st.session_state.page +1} de {total_pages}</p>", unsafe_allow_html=True)

        with col1:  # Previous button column (right)
            if st.button("Página Anterior"):
                if st.session_state.page > 0:
                    st.session_state.page -= 1
                    st.rerun()
        st.write('')

with st.expander("Resumen Inventario",expanded=st.session_state.expand_resumen_inventario):

# st.title("Resumen Inventario")

    if st.session_state.selected_inventory:          
        resumen_inventario = DB.obtener_elementos_jde(int(st.session_state.selected_inventory))

        Inventario_Realizado= datosJDE[datosJDE['ID'] == int(st.session_state.selected_inventory) ].squeeze()

        
        Tipo_inventario_r = "Completo" if Inventario_Realizado["Ubicacion"] == "PT" else "Parcial, en " + Inventario_Realizado["Ubicacion"]

        st.subheader("Resumen Inventario JDE-" + str(inventario["NumeroConteo"]) +"{"+Tipo_inventario_r +"} " + DB.format_datetime(Inventario_Realizado["Fecha_Inventario"])    )
    

        
        total_elementos=int(Inventario_Realizado["Elementos_OK"])+int(Inventario_Realizado["Elementos_Faltantes"])+int(Inventario_Realizado["Elementos_Sobrantes"])
    
    
        _='''
        data1 = {
        "Lecturas": ["Correctos", "Faltantes", "Sobrantes", "Total"],
        "": [
            Inventario_Realizado["Elementos_OK"],
            Inventario_Realizado["Elementos_Faltantes"],
            Inventario_Realizado["Elementos_Sobrantes"],
            total_elementos,
        ],
        "%": [
            f'{int(Inventario_Realizado["Elementos_OK"] / total_elementos * 100)}%',  # Multiplicar por 100 para porcentaje
            f'{int(Inventario_Realizado["Elementos_Faltantes"] / total_elementos * 100)}%',
            f'{int(Inventario_Realizado["Elementos_Sobrantes"] / total_elementos* 100)}%',
            "",
        ],
        }

        Lecturas_df = pd.DataFrame(data1)

        data2 = {
        "Vuelo": ["Fecha", "Hora", "Fin", "Duración"],
        "": [
            DB.format_date(Inventario_Realizado["Fecha_Vuelo"]),
            DB.format_time(Inventario_Realizado["Fecha_Vuelo"]),
            DB.add_seconds_to_timestamp_string(Inventario_Realizado["Fecha_Vuelo"],Inventario_Realizado["Tiempo_Vuelo"]),
            DB.format_seconds_HHMMSS(int(Inventario_Realizado["Tiempo_Vuelo"])),
        ]
    
        }

        info_df = pd.DataFrame(data2)'''

    

        
        


        st.button("Cambiar Vista", on_click=DB.toggle_content_advanced)

        if st.session_state.show_content_advanced:
            col1, col2 = st.columns([2,2],gap="medium")
            with col1:
            
                headers_lecturas = st.columns([2, 1, 1], gap="small", vertical_alignment="top") 
                columns = ["Lecturas", "Nº Elementos","%"]
                for i, header in enumerate(headers_lecturas):
                    with header:
                        st.markdown(f"<p style='text-align: left;font-weight: bold;'>{columns[i]}</p>", unsafe_allow_html=True) 

                # Each row of the table
                col10, col20, col30 = st.columns([2, 1, 1], gap="small", vertical_alignment="center")
                col10.write(f"<p class='data-ok' style='text-align: left;'>Correctos</p>", unsafe_allow_html=True)
                col20.write(f"<p class='data-ok' style='text-align: left;'>{Inventario_Realizado['Elementos_OK']}</p>", unsafe_allow_html=True)
                col30.write(f"<p class='data-ok' style='text-align: left;'>{int(Inventario_Realizado['Elementos_OK'] / total_elementos * 100)}%</p>", unsafe_allow_html=True)

                col10, col20, col30 = st.columns([2, 1, 1], gap="small", vertical_alignment="center")
                col10.write(f"<p class='data-missing' style='text-align: left;'>Faltantes</p>", unsafe_allow_html=True)
                col20.write(f"<p class='data-missing' style='text-align: left;'>{Inventario_Realizado['Elementos_Faltantes']}</p>", unsafe_allow_html=True)
                col30.write(f"<p class='data-missing' style='text-align: left;'>{int(Inventario_Realizado['Elementos_Faltantes'] / total_elementos * 100)}%</p>", unsafe_allow_html=True)

                col10, col20, col30 = st.columns([2, 1, 1], gap="small", vertical_alignment="center")
                col10.write(f"<p class='data-excess' style='text-align: left;'>Sobrantes</p>", unsafe_allow_html=True)
                col20.write(f"<p class='data-excess' style='text-align: left;'>{Inventario_Realizado['Elementos_Sobrantes']}</p>", unsafe_allow_html=True)
                col30.write(f"<p class='data-excess' style='text-align: left;'>{int(Inventario_Realizado['Elementos_Sobrantes'] / total_elementos * 100)}%</p>", unsafe_allow_html=True)
            
            with col2:
                
                headers_lecturas = st.columns([2, 1], gap="small", vertical_alignment="top") 
                columns = ["Vuelo", ""]
                for i, header in enumerate(headers_lecturas):
                    with header:
                        st.markdown(f"<p class='fly-data' style='text-align: left;'>{columns[i]}</p>", unsafe_allow_html=True) 

                # Each row of the table
                col10, col20 = st.columns([2, 1], gap="small", vertical_alignment="center")
                col10.write(f"<p class='fly-data' style='text-align: left;'>Fecha</p>", unsafe_allow_html=True)
                col20.write(f"<p class='fly-data' style='text-align: left;'>{DB.format_date(Inventario_Realizado["Fecha_Vuelo"])}</p>", unsafe_allow_html=True)
                col10, col20 = st.columns([2, 1], gap="small", vertical_alignment="center")
                col10.write(f"<p class='fly-data' style='text-align: left;'>Hora</p>", unsafe_allow_html=True)
                col20.write(f"<p class='fly-data' style='text-align: left;'>{DB.format_time(Inventario_Realizado["Fecha_Vuelo"])}</p>", unsafe_allow_html=True)
                col10, col20 = st.columns([2, 1], gap="small", vertical_alignment="center")
                col10.write(f"<p class='fly-data' style='text-align: left;'>Fin</p>", unsafe_allow_html=True)
                col20.write(f"<p class='fly-data' style='text-align: left;'>{DB.add_seconds_to_timestamp_string(Inventario_Realizado["Fecha_Vuelo"],Inventario_Realizado["Tiempo_Vuelo"])}</p>", unsafe_allow_html=True)
                col10, col20 = st.columns([2, 1], gap="small", vertical_alignment="center")
                col10.write(f"<p class='fly-data' style='text-align: left;f'>Duración</p>", unsafe_allow_html=True)
                col20.write(f"<p class='fly-data' style='text-align: left;'>{DB.format_seconds_HHMMSS(int(Inventario_Realizado["Tiempo_Vuelo"]))}</p>", unsafe_allow_html=True)
            st.write('')
        else:
            st.markdown(f"""
            <div style="display: flex; align-items: center;">
            <div style="display:inline-block;background-color:gray;padding:10px;border-radius:10px;text-align:center;width:40%;margin-right:10px;">
                <h1>{DB.format_datetime(Inventario_Realizado["Fecha_Inventario"])}</h1>
                <p>Fecha de inventario</p>
            </div>
            <div style="display:inline-block;background-color:gray;padding:10px;border-radius:10px;text-align:center;width:20%;margin-right:10px;">
                <h1>{len(resumen_inventario)}</h1>
                <p>Elementos en Inventrio</p>
            </div>
            <div style="display:inline-block;background-color:gray;padding:10px;border-radius:10px;text-align:center;width:40%;margin-right:10px;">
                <h1>{DB.format_datetime(Inventario_Realizado["Fecha_Vuelo"])}</h1>
                <p>Fecha de vuelo</p>
            </div>
            </div>""", unsafe_allow_html=True)
            st.write('')

            st.markdown(f"""
            <div style="display: flex; align-items: center;">
            <div style="display:inline-block;background-color:#2bb534;padding:10px;border-radius:10px;text-align:center;width:25%;margin-right:10px;">
                <h1>{Inventario_Realizado["Elementos_OK"]}</h1>
                <p>Elementos correctos</p>
            </div>
            <div style="display:inline-block;background-color:#f89256;padding:10px;border-radius:10px;text-align:center;width:25%;margin-right:10px;">
                <h1>{Inventario_Realizado["Elementos_Faltantes"]}</h1>
                <p>Elementos faltantes</p>
            </div>
            <div style="display:inline-block;background-color:#dfb52c;padding:10px;border-radius:10px;text-align:center;width:25%;margin-right:10px;">
                <h1>{Inventario_Realizado["Elementos_Sobrantes"]}</h1>
                <p>Elementos sobrantes</p>
            </div>
            <div style="display:inline-block;background-color:gray;padding:10px;border-radius:10px;text-align:center;width:25%;margin-right:10px;">
                <h1>{Inventario_Realizado["Porcentaje_Lectura"]}%</h1>
                <p>Porcentaje lectura</p>
            </div>
            </div>""", unsafe_allow_html=True)

            st.write('')
            st.write('')

        _='''
        colA, colB = st.columns([2,2],gap="medium")

        with colA:
            st.markdown("""
            <style>
            .streamlit-table th:nth-child(1),  /* Hide index header */
            .streamlit-table td:nth-child(1) { /* Hide index cells */
                display: none;
            }
            .streamlit-table tr:nth-child(1) { /* Target the first row */
                color: green !important; /* Make text green */
            }            
            </style>
            """, unsafe_allow_html=True)
            st.table(Lecturas_df)

        with colB:
            st.markdown("""
            <style>
            .streamlit-table th:nth-child(1),  /* Hide index header */
            .streamlit-table td:nth-child(1) { /* Hide index cells */
                display: none;
            }
            </style>
            """, unsafe_allow_html=True)
            st.table(info_df)
        '''
        
        # Example data
        data = {
            'Category': ['Correctos', 'Faltantes', 'Sobrantes'],
            'Values': [int(Inventario_Realizado["Elementos_OK"]), int(Inventario_Realizado["Elementos_Faltantes"]), int(Inventario_Realizado["Elementos_Sobrantes"])]
        }
        color_map = {'Correctos': '#2bb534', 'Faltantes': '#f89256', 'Sobrantes': '#dfb52c'}
        # Create a pie chart using Plotly
        fig = px.pie(data, names='Category', values='Values', title='Distribución de Elementos', color='Category',color_discrete_map=color_map)

        # Display the pie chart in Streamlit
        #st.plotly_chart(fig)

        col1, col2 = st.columns([2,3])

        # Display the pie chart in the first column
        with col1:
            st.plotly_chart(fig)

        # Display the table in the second column
        with col2:
            st.write('')
            st.write('')
            st.markdown("**Elementos de inventario**")
            pagination = st.container()
            pagination.dataframe(data=resumen_inventario, use_container_width=True)

        st.write('')

        if Inventario_Realizado["Imagen_Vuelo"] is not None:
            left_co, cent_co,last_co = st.columns(3)
            with cent_co:
                    st.image(Inventario_Realizado["Imagen_Vuelo"], caption="Representación Vuelo")            
       

        if Inventario_Realizado["Video_Vuelo"] is not None:
            left_co, cent_co,last_co = st.columns([1, 7, 1])
            with cent_co:
                    st.write("Representación de vuelo realizado")
                    st.video(data=os.path.relpath(Inventario_Realizado["Video_Vuelo"], 'Webserver'),format="video/mp4", autoplay=False)    

        #st.video(data="videos/42_inventario_vuelo.mp4",format="video/mp4", autoplay=False)    
    else:
        st.write("Ningún Inventario selecionado")
        st.write('')
        st.write('')
        

        # Mostrar detalles del inventario
        #st.write("OK")
with st.expander("Plano Patio Mina 2",expanded=st.session_state.expand_plano):

    st.write('')

    
    left_co, cent_co,last_co = st.columns([1, 7, 1])
    with cent_co:
        st.image('images/PM2_3d_20250226.jpg', caption="Patio Mina 2")  # Adjust the width as necessary

    



#st.sidebar.title("Menú")
#st.sidebar.button("inicio", on_click=lambda: st.experimental_rerun("/inventarios-pendientes"))
#st.sidebar.button("Patio Mina 2", on_click=lambda: st.experimental_rerun("/inventarios_Pendientes"))



#eliminar inventario; fondo gris fuera de los expander, colocar tiempo de vuelo promedio en vez de vuelo, crear api de eliminacion, desplegar tiempo de vuelo en MM:SS, eliminar PT, reemplazar zona por Ubicacion, Agregar numero de Contero en Listado de Inventarios

