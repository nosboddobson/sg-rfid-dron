import os
import pandas as pd
import streamlit as st
import plotly.express as px
#import matplotlib.pyplot as plt
#from pywaffle import Waffle

from menu import make_sidebar

from Functions import DB_Service as DB


#Inicio Creacion de la Pagina -----------------------------------------------------------------------------------------

st.set_page_config(page_title="Inventarios Sierra Gorda",layout="wide")

make_sidebar()
#_lock = RendererAgg.lock


# Create two columns for the logo and title
#col1, col2 = st.columns([1, 4])  # Adjust the ratios as necessary
# Add logo
#with col1:
    
#    st.image('images/SG_Logo.png', width=250)  # Adjust the width as necessary
# Add title in the second column
#with col2:
    #st.title("Inventarios Patio Mina 2")
st.markdown("<h1 style='text-align: center;'>Inventarios Realizados Patio Mina 2</h1>", unsafe_allow_html=True)


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
if 'expand_plano' not in st.session_state:
    st.session_state.expand_plano = False
if 'selected_inventory' not in st.session_state:
    st.session_state.selected_inventory = None
if 'show_popup_eliminar' not in st.session_state:
    st.session_state['show_popup_eliminar'] = False
if "show_content_advanced" not in st.session_state:
            st.session_state.show_content_advanced = True

    # Crear la página "Inventarios Pendientes"
if 'page2' not in st.session_state:
            st.session_state.page2 = 0
            print ("st.session_state.page2 = 0")




with st.expander("Inventarios Realizados",expanded=st.session_state.expand_inventario_Realizado):

        
        #st.title("Inventarios Realizados")
        #st.subheader("Patio 2 Mina")
        # Get the data
        datosJDE = DB.obtener_datos_inventarios_jde()
    
       # pt_rows = datosJDE[datosJDE['Ubicacion'] == "PT"]
    
        #Obtener inventarios pendientes
        #average_porcentaje = datosJDE['Porcentaje_Lectura'].mean()


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
        start_row = st.session_state.page2 * rows_per_page
        end_row = start_row + rows_per_page
        #print ("start Row: " + str(start_row))
        # Show current page rows
        df_to_display = datosJDE.iloc[start_row:end_row]

        #st.subheader("Detalles de Inventarios Realizados")

        headers_Procesado = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 2,2,2], gap="medium", vertical_alignment="top")
    
        _= '''headers[0].write("Tipo Inventario")
        headers[1].write("Zona")
        headers[2].write("Fecha Inventario")
        headers[3].write("Hora Inventario")
        headers[4].write("Tiempo de Vuelo [HH:MM:SS]")
        headers[5].write("Correctos")
        headers[6].write("Faltantes")
        headers[7].write("Sobrantes")
        headers[8].write("Lectura [%]")
        headers[9].write("Código JD")
        headers[10].write("") '''

        header_texts = [
            "Zona",
            "Fecha Inventario",
            "Hora Inventario",
            "Fecha de Vuelo",
            "Hora de Vuelo",
            "Tiempo de Vuelo",
            "Correctos",
            "Faltantes",
            "Sobrantes",
            "Lectura [%]",
            ""  # Empty string for the last column
        ]        

        for i, header in enumerate(headers_Procesado):
            with header:
                st.markdown(f"<p style='text-align: center;font-weight: bold;'>{header_texts[i]}</p>", unsafe_allow_html=True) 


        if not datosJDE.empty:  # Check if the DataFrame is not empty
            for index, inventario in df_to_display.iterrows():  # Iterate over rows using iterrows()
                # Each row of the table
                col2, col3, col4,colA,colB, col5, col6, col7, col8, col9,col11 = st.columns([1, 2, 2,2,2, 2, 2, 2, 2, 2,2], gap="medium", vertical_alignment="center")

                # Determine Tipo_inventario based on Ubicacion
                #Tipo_inventario = "Completo" if inventario["Ubicacion"] == "PT" else "Parcial"


                #col1.write(Tipo_inventario)
                col2.write(f"<p style='text-align: center;'>{inventario['Ubicacion']}</p>", unsafe_allow_html=True) 
                col3.write(f"<p style='text-align: center;'>{DB.format_date(inventario["Fecha_Inventario"])}</p>", unsafe_allow_html=True) 
                col4.write(f"<p style='text-align: center;'>{DB.format_time(inventario["Fecha_Inventario"])}</p>", unsafe_allow_html=True) 

                colA.write(f"<p style='text-align: center;'>{DB.format_date(inventario["Fecha_Vuelo"])}</p>", unsafe_allow_html=True) 
                colB.write(f"<p style='text-align: center;'>{DB.format_time(inventario["Fecha_Vuelo"])}</p>", unsafe_allow_html=True) 

                col5.write(f"<p style='text-align: center;'>{DB.format_seconds_HHMMSS(inventario["Tiempo_Vuelo"])}</p>", unsafe_allow_html=True) 
            
        

                #col6.write(inventario["Elementos_OK"])
                col6.write(f"<p style='text-align: center;color: lime;font-weight: bold;'>{inventario["Elementos_OK"]}</p>", unsafe_allow_html=True)
                
                #col7.write(inventario["Elementos_Faltantes"])
                col7.write(f"<p style='text-align: center;color: orange'>{inventario["Elementos_Faltantes"]}</p>", unsafe_allow_html=True)

            
                #col8.write(inventario["Elementos_Sobrantes"])
                col8.write(f"<p style='text-align: center;color: yellow'>{inventario["Elementos_Sobrantes"]}</p>", unsafe_allow_html=True)
                col9.write(f"<p style='text-align: center;'>{str(inventario["Porcentaje_Lectura"])}%</p>", unsafe_allow_html=True) 
                #col10.write(f"<p style='text-align: center;'>{str(inventario["NumeroConteo"])}</p>", unsafe_allow_html=True) 
            

                # Botón de "Resumen"
                if col11.button("Ver", key=f"resumen_{inventario['ID']}"):
                    st.session_state.selected_inventory = inventario["ID"]
                    st.session_state.expand_resumen_inventario=True
                    st.session_state.expand_inventario_Realizado = False
            

        

        # Pagination buttons with center alignment
        # Pagination buttons with custom alignment
        col0,col1, col2, col3,col4 = st.columns([3,2, 2, 2,3],gap="small")  # Create three columns with different widths

        with col3:  # Next button column (left)
            if st.button("Siguiente Página"):
               
                if st.session_state.page2 < total_pages -1 :
                    st.session_state.page2 = st.session_state.page2 + 1
                    st.rerun()
                  


        with col2:  # Page indicator column (center)
            st.markdown(f"<p style='text-align: center;'>Página {st.session_state.page2 + 1} de {total_pages}</p>", unsafe_allow_html=True)

        with col1:  # Previous button column (right)
            if st.button("Página Anterior"):
                if st.session_state.page2 > 0:
                    st.session_state.page2 = st.session_state.page2 - 1
                    st.rerun()

        st.write('')

with st.expander("Resumen Inventario",expanded=st.session_state.expand_resumen_inventario):

# st.title("Resumen Inventario")

    if st.session_state.selected_inventory:          
        resumen_inventario = DB.obtener_elementos_jde(int(st.session_state.selected_inventory))

        Inventario_Realizado= datosJDE[datosJDE['ID'] == int(st.session_state.selected_inventory) ].squeeze()

        
        Tipo_inventario_r = "Completo" if Inventario_Realizado["Ubicacion"] == "PT" else "Parcial, en " + Inventario_Realizado["Ubicacion"]

        st.subheader("Resumen Inventario JDE-" + str(Inventario_Realizado["NumeroConteo"]) +" {"+Tipo_inventario_r +"} " + DB.format_datetime(Inventario_Realizado["Fecha_Inventario"])    )
    

        
        total_elementos=int(Inventario_Realizado["Elementos_OK"])+int(Inventario_Realizado["Elementos_Faltantes"])+int(Inventario_Realizado["Elementos_Sobrantes"])
    
    

        st.write('')


       
        left_co, cent_co,last_co = st.columns([5,0.2,3])
        
       
        with left_co:
                    #with st.container(height=420,border=False): 
                        
                        if Inventario_Realizado["Video_Vuelo"] is not None:
                            st.write("Representación de vuelo realizado")
                            st.video(data=os.path.relpath(Inventario_Realizado["Video_Vuelo"], 'Webserver'),format="video/mp4", autoplay=False)  
                        else:
                               st.write("Representación NO encontrada")
    


        # datos para grafico
        data = {
            'Category': [f"Total Elementos {total_elementos}",'Correctos', 'Faltantes', 'Sobrantes'],
            'Values': [0,int(Inventario_Realizado["Elementos_OK"]), int(Inventario_Realizado["Elementos_Faltantes"]), int(Inventario_Realizado["Elementos_Sobrantes"])],
            'Parents': ["", f"Total Elementos {total_elementos}", f"Total Elementos {total_elementos}",f"Total Elementos {total_elementos}"]
        }

    

        color_map = {'Correctos': 'green', 'Faltantes': 'orange', 'Sobrantes': 'yellow',f"Total Elementos {total_elementos}": 'black'}
        # Create a pie chart using Plotly

        #grafico de pie
        #fig = px.pie(data, names='Category', values='Values', color='Category',color_discrete_map=color_map)
        figd=px.treemap(data,names='Category',
                               values='Values', 
                               parents='Parents',
                               labels='Category',
                               color='Category',
                               color_discrete_map=color_map,
                               #hover_data='Values',  #customize hover data
                              # hover_name='Category', # Customize main hover name,
                          
                               
                               )
        figd.update_layout(margin = dict(t=0, l=0, r=0, b=20))
        figd.update_traces(textinfo = "label+value",sort=False,textposition='middle center',hovertemplate='')

        
     

        with last_co:
                #with st.container(height=420,border=False): 
                    st.write("Distribución de elementos")
                    #with _lock:
                    st.plotly_chart(figd)
                
   
        # Display the pie chart in Streamlit
        #st.plotly_chart(fig)

        

        st.write('')
        st.markdown("**Existencias por Fila**")
        def procesar_ubicacion(ubicacion):
            fila = ubicacion[3:6]  # Extrae los caracteres del 4 al 6 (inclusive)
            rack = ubicacion[6:]   # Extrae los caracteres del 7 en adelante
            return pd.Series([fila, rack])  # Retorna una Serie de Pandas
       
        # Aplica la función a la columna 'Ubicacion'
        resumen_inventario[['Fila', 'Rack']] = resumen_inventario['Ubicación'].apply(procesar_ubicacion)

        # Cuenta 'Correctos' y 'Faltantes' por 'Fila' y 'Rack'
        conteo = resumen_inventario.groupby(['Fila', 'Rack', 'Resultado']).size().unstack(fill_value=0)
        #print(conteo)
        conteo.columns = ['Faltantes', 'Correctos']  # Renombra las columnas
        nuevo_df = conteo.reset_index()

        #print(nuevo_df)
        
        cols = st.columns(4)  # Create 4 columns

        for index,row in nuevo_df.iterrows():
            
                with cols[index % 4]: 
                    data = {
                    'Category': ['Correctos', 'Faltantes'],
                    'Values': [row['Correctos'], row['Faltantes']],
                    
                    }
                    data2 = {
                    'Category': [f"Fila: {int(row['Fila'])}, Sección: {int(row['Rack'])}",'Correctos', 'Faltantes'],
                    'Values': [0,row['Correctos'], row['Faltantes']],
                    'Parents': ["",f"Fila: {int(row['Fila'])}, Sección: {int(row['Rack'])}", f"Fila: {int(row['Fila'])}, Sección: {int(row['Rack'])}"]
                    }
                
                    fign = px.pie(data,
                            names='Category',
                            values='Values',
                            color='Category',
                            color_discrete_map=color_map,
                          #  title=f"Fila: {int(row['Fila'])}, Sección: {int(row['Rack'])}",
                            hover_name='Category',
                        )  # Agrega un título

                    color_mapn = {'Correctos': 'green', 'Faltantes': 'orange', 'Total': 'black',}

                    figd=px.treemap(data2,names='Category',
                                values='Values', 
                                parents='Parents',
                                labels='Category',
                               # title=f"Fila: {int(row['Fila'])}, Sección: {int(row['Rack'])}",
                                color='Category',
                                color_discrete_map=color_mapn,
                                height=250,
                                color_discrete_sequence=['black']
                                )
                    figd.update_layout(margin = dict(t=50, l=25, r=25, b=10))
                    figd.update_traces(textinfo = "label+value", sort=False,textposition='middle center',hovertemplate='')

                
                    
                    st.plotly_chart(figd)
                    #st.plotly_chart(fign)

        st.write('')
        st.markdown("**Elementos de inventario**")
        pagination = st.container()
        pagination.dataframe(data=resumen_inventario, use_container_width=True)      
               
        #st.video(data="videos/42_inventario_vuelo.mp4",format="video/mp4", autoplay=False)    
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

