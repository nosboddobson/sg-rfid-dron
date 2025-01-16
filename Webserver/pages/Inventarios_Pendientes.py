
import streamlit as st
import plotly.express as px
from menu import make_sidebar

from Functions import DB_Service as DB


#Inicio Creacion de la Pagina -----------------------------------------------------------------------------------------

st.set_page_config(page_title="Inventario Sierra Gorda",layout="wide")

make_sidebar()

    
st.markdown("""
    <style>
    /* Set the entire background of the page to light gray */
    body {
        background-color: #f0f0f0;
    }
    </style>
    """, unsafe_allow_html=True)



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
# Initialize session state for the expanders
if 'expand_inventario_Realizado' not in st.session_state:
    st.session_state.expand_inventario_Realizado = False
if 'selected_inventario_id' not in st.session_state:
    st.session_state.selected_inventory = None
if 'show_popup_eliminar' not in st.session_state:
    st.session_state['show_popup_eliminar'] = False

    # Crear la página "Inventarios Pendientes"


with st.expander("Inventarios Pendientes",expanded=True):

    st.title("Inventarios Pendientes")

    #Obtener inventarios pendientes
    datos = DB.obtener_datos_inventarios_pendientes()
    if len(datos) >0:
        total_seconds =sum(row[3] for row in datos)/len(datos)
    else:
        total_seconds=0


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

    <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:250px;margin-right:10px;">
        <h1>{DB.seconds_to_hhmmss(total_seconds)}</h1>
        <p>Tiempo de Vuelo Promedio</p>
    </div>
    </div>

    """, unsafe_allow_html=True)



    

    # Mostrar la tabla de inventarios pendientes
    

    st.subheader("Detalles de Inventarios Pendientes")
    headers = st.columns([1, 2, 2, 2, 2, 2,2,2], gap="small", vertical_alignment="top")
    headers[0].write("ID")
    headers[1].write("Fecha de Vuelo")
    headers[2].write("Elementos Detectados")
    headers[3].write("Tiempo de Vuelo[HH:MM:SS]")
    headers[4].write("Tipo Inventario")
    headers[5].write("Zona")
    headers[6].write("Acción")
    headers[7].write("Eliminar")



    if datos:
        for inventario in datos:
            # Each row of the table
            col1, col2, col3, col4, col5, col6,col7,col8 = st.columns([1, 2, 2, 2,2, 2,2,2], gap="medium", vertical_alignment="center")

            # Column 1: ID Inventario
            col1.write(inventario[0])

            # Column 2: Fecha de Vuelo
            col2.write(inventario[1])

            # Column 3: Elementos Detectador
            col3.write(inventario[2])
            # Column 3: Elementos Detectador
            #minutes = str(inventario[3] // 60).zfill(2)
            #seconds = str(inventario[3] % 60).zfill(2)
            #col4.write(minutes+":"+seconds)
            col4.write(DB.seconds_to_hhmmss(inventario[3]))

            # Column 4: Tipo Inventario dropdown
            tipo_inventario = col5.selectbox("Tipo Inventario", ["Parcial", "Completo"], key=f"tipo_{inventario[0]}",label_visibility="collapsed")

            zona_disabled = True if tipo_inventario == "Completo" else False
            # Column 5: Zona dropdown
            zona = col6.selectbox("Zona", ["SF0","SF1","SF2","PF1", "PF2", "PF3","PF4","PF5","PF6","PF7"], key=f"zona_{inventario[0]}", help="S= Shelving, P= Pasillo y F=Fila",label_visibility="collapsed",disabled=zona_disabled)

            # Column 6: Acción button
            if col7.button("Iniciar Inventario", key=f"iniciar_{inventario[0]}", help="Enviar Inventario a JD Edwards"): #Si el boton es presionado entonces:
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
                        st.error(f"Error Conectado a Servidor, por favor, intenta mas tarde!")
                        st.session_state.button_disabled = False
           
            
            if col8.button("Eliminar", key=f"Eliminar_{inventario[0]}", help="Eliminar inventario"): #Si el boton es presionado entonces:
                    
                    DB.eliminar_inventario_dialog(inventario[0])

                    
                        
                

            st.write('')    
                #st.experimental_rerun(f"http://127.0.0.1:5100/actualizar-estado-inventario?sucursal={tipo_inventario}&Ubicacion={zona}&ID={inventario[0]}")

    else:
        st.write("No hay inventarios pendientes.")
        st.write('')


with st.expander("Inventarios Realizados",expanded=st.session_state.expand_inventario_Realizado):

        
        st.title("Inventarios Realizados")
        st.subheader("Patio 2 Mina")
        # Get the data
        datosJDE = DB.obtener_datos_inventarios_jde()
    
        pt_rows = datosJDE[datosJDE['Ubicacion'] == "PT"]
    
        #Obtener inventarios pendientes
        average_porcentaje = datosJDE['Porcentaje_Lectura'].mean()


    #
    # Mostrar el total de inventarios pendientes
    

        st.markdown(f"""
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
        

        # Pagination variables
        # Number of rows per page
        rows_per_page = 8
        if 'page' not in st.session_state:
            st.session_state.page = 0

        # Calculate total pages
        total_pages = (len(datosJDE) + rows_per_page - 1) // rows_per_page  # Ceiling division

        # Update start_row and end_row based on the current page
        start_row = st.session_state.page * rows_per_page
        end_row = start_row + rows_per_page

        # Show current page rows
        df_to_display = datosJDE.iloc[start_row:end_row]

        st.subheader("Detalles de Inventarios Realizados")

        headers = st.columns([2, 1, 2, 2, 2, 2, 2, 2, 2,2,2], gap="small", vertical_alignment="top")
        headers[0].write("Tipo Inventario")
        headers[1].write("Zona")
        headers[2].write("Fecha Inventario")
        headers[3].write("Fecha de Vuelo")
        headers[4].write("Tiempo de Vuelo[HH:MM:SS]")
        headers[5].write("Correctos")
        headers[6].write("Faltantes")
        headers[7].write("Sobrantes")
        headers[8].write("Lectura [%]")
        headers[9].write("Código JD")
        headers[10].write("")
        

        if not datosJDE.empty:  # Check if the DataFrame is not empty
            for index, inventario in df_to_display.iterrows():  # Iterate over rows using iterrows()
                # Each row of the table
                col1, col2, col3, col4, col5, col6, col7, col8, col9,col10,col11 = st.columns([2, 1, 2, 2, 2, 2, 2, 2, 2,2,2], gap="medium", vertical_alignment="center")

                # Determine Tipo_inventario based on Ubicacion
                Tipo_inventario = "Completo" if inventario["Ubicacion"] == "PT" else "Parcial"

            
                col1.write(Tipo_inventario)
                col2.write(inventario["Ubicacion"])
                col3.write(inventario["Fecha_Inventario"])
                col4.write(inventario["Fecha_Vuelo"])
                #minutes = str(inventario["Tiempo_Vuelo"] // 60).zfill(2)
                #seconds = str(inventario["Tiempo_Vuelo"] % 60).zfill(2)
                #col5.write(minutes+":"+seconds)
                col5.write(DB.seconds_to_hhmmss(inventario["Tiempo_Vuelo"]))
                col6.write(inventario["Elementos_OK"])
                col7.write(inventario["Elementos_Faltantes"])
                col8.write(inventario["Elementos_Sobrantes"])
                col9.write(str(inventario["Porcentaje_Lectura"])+"%")
                col10.write(str(inventario["NumeroConteo"]))

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
                if st.session_state.page < total_pages - 1:
                    st.session_state.page += 1

        with col2:  # Page indicator column (center)
            st.markdown(f"<p style='text-align: center;'>Página {st.session_state.page + 1} de {total_pages}</p>", unsafe_allow_html=True)

        with col1:  # Previous button column (right)
            if st.button("Página Anterior"):
                if st.session_state.page > 0:
                    st.session_state.page -= 1
        st.write('')

with st.expander("Resumen Inventario",expanded=st.session_state.expand_resumen_inventario):

    st.title("Resumen Inventario")

    if st.session_state.selected_inventory:          
        resumen_inventario = DB.obtener_elementos_jde(int(st.session_state.selected_inventory))

        Inventario_Realizado= datosJDE[datosJDE['ID'] == int(st.session_state.selected_inventory) ].squeeze()

        Tipo_inventario_r = "Inventario Completo" if inventario["Ubicacion"] == "PT" else "Inventario Parcial, en " + inventario["Ubicacion"]
        st.subheader(Tipo_inventario_r +", Código JD : " + str(inventario["NumeroConteo"])   )
     

        st.markdown(f"""
        <div style="display: flex; align-items: center;">
        <div style="display:inline-block;background-color:lightblue;padding:10px;border-radius:10px;text-align:center;width:40%;margin-right:10px;">
            <h1>{Inventario_Realizado["Fecha_Inventario"]}</h1>
            <p>Fecha de inventario</p>
        </div>
        <div style="display:inline-block;background-color:lavender;padding:10px;border-radius:10px;text-align:center;width:20%;margin-right:10px;">
            <h1>{len(resumen_inventario)}</h1>
            <p>Elementos detectados</p>
        </div>
        <div style="display:inline-block;background-color:lightblue;padding:10px;border-radius:10px;text-align:center;width:40%;margin-right:10px;">
            <h1>{Inventario_Realizado["Fecha_Vuelo"]}</h1>
            <p>Fecha de vuelo</p>
        </div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="display: flex; align-items: center;">
        <div style="display:inline-block;background-color:green;padding:10px;border-radius:10px;text-align:center;width:25%;margin-right:10px;">
            <h1>{Inventario_Realizado["Elementos_OK"]}</h1>
            <p>Elementos correctos</p>
        </div>
        <div style="display:inline-block;background-color:orange;padding:10px;border-radius:10px;text-align:center;width:25%;margin-right:10px;">
            <h1>{Inventario_Realizado["Elementos_Faltantes"]}</h1>
            <p>Elementos faltantes</p>
        </div>
        <div style="display:inline-block;background-color:yellow;padding:10px;border-radius:10px;text-align:center;width:25%;margin-right:10px;">
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
        # Example data
        data = {
            'Category': ['Correctos', 'Faltantes', 'Sobrantes'],
            'Values': [int(Inventario_Realizado["Elementos_OK"]), int(Inventario_Realizado["Elementos_Faltantes"]), int(Inventario_Realizado["Elementos_Sobrantes"])]
        }
        color_map = {'Correctos': 'green', 'Faltantes': 'orange', 'Sobrantes': 'yellow'}
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
            
            st.markdown("**Elementos de inventario**")
            pagination = st.container()
            pagination.dataframe(data=resumen_inventario, use_container_width=True)

        st.write('')
        
            
    else:
        st.write("Ningún Inventario selecionado")
        st.write('')
        st.write('')
        

        # Mostrar detalles del inventario
        #st.write("OK")



#st.sidebar.title("Menú")
#st.sidebar.button("inicio", on_click=lambda: st.experimental_rerun("/inventarios-pendientes"))
#st.sidebar.button("Patio Mina 2", on_click=lambda: st.experimental_rerun("/inventarios_Pendientes"))



#eliminar inventario; fondo gris fuera de los expander, colocar tiempo de vuelo promedio en vez de vuelo, crear api de eliminacion, desplegar tiempo de vuelo en MM:SS, eliminar PT, reemplazar zona por Ubicacion, Agregar numero de Contero en Listado de Inventarios

