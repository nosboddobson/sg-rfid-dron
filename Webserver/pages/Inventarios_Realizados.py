import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import math
#import matplotlib.pyplot as plt
#from pywaffle import Waffle

from menu import make_navbar

from Functions import DB_Service as DB
from Functions import Reuse_Service as Reuse


#Inicio Creacion de la Pagina -----------------------------------------------------------------------------------------

st.set_page_config(page_title="Inventarios Sierra Gorda",layout="wide")

make_navbar()
#_lock = RendererAgg.lock


# Create two columns for the logo and title
#col1, col2 = st.columns([1, 4])  # Adjust the ratios as necessary
# Add logo
#with col1:
    
#    st.image('images/SG_Logo.png', width=250)  # Adjust the width as necessary
# Add title in the second column
#with col2:
    #st.title("Inventarios Patio Mina 2")
#st.markdown("<h1 style='text-align: center;'>Inventarios Realizados Patio Mina 2</h1>", unsafe_allow_html=True)

Reuse.Load_css('Functions/CSS_General.css')

def create_waffle_chart(correctos, faltantes, fila, seccion, num_columnas=10):
    """
    Crea un gráfico waffle responsive para visualizar correctos y faltantes.
    """
    total = correctos + faltantes
    
    # Calcular proporciones
    prop_correctos = correctos / total if total > 0 else 0
    prop_faltantes = faltantes / total if total > 0 else 1
    
    # Determinar tamaño de la cuadrícula (100 cuadrados)
    n_cuadrados = 100
    n_columnas = num_columnas
    n_filas = n_cuadrados // n_columnas
    
    # Calcular número de cuadrados para cada categoría
    n_correctos = round(prop_correctos * n_cuadrados)
    n_faltantes = n_cuadrados - n_correctos
    
    # Crear matriz para el waffle
    waffle = np.ones((n_filas, n_columnas))
    
    # Llenar matriz con valores (1 para correctos, 2 para faltantes)
    count = 0
    for i in range(n_filas):
        for j in range(n_columnas):
            if count < n_correctos:
                waffle[i, j] = 1  # Correctos = 1
            else:
                waffle[i, j] = 2  # Faltantes = 2
            count += 1
    
    color_correctos = '#2bb534'  # Verde
    color_faltantes = '#f89256'  # Naranja
    
    # Crear heatmap para representar el waffle
    fig = go.Figure(data=go.Heatmap(
        z=waffle,
        colorscale = [
            [0, 'green'],
            [0.3, 'green'],
            [0.3, 'green'],
            [0.5, 'green'],
            [0.5, 'orange'],
            [1.0, 'orange']
        ],
        showscale=False,
        hoverongaps=False,
        hovertemplate='<extra></extra>'
    ))
    
    # responsive
    fig.update_layout(
         
        title={
            'text': f"Fila: {fila}, Sección: {seccion}",
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        title_font=dict(size=16, color="white", weight="bold"),
        paper_bgcolor="#1E2029",
        plot_bgcolor="#1E2029",
        margin=dict(t=50, l=10, r=10, b=70),
        autosize=True,  
        height=None,    
        annotations=[
            dict(
                x=0.5,  # Centrado horizontalmente
                y=-0.15,  # Primera anotación (Correctos)
                xref="paper",
                yref="paper",
                text=f"Correctos: {correctos} ({round(prop_correctos*100)}%)",
                showarrow=False,
                font=dict(color=color_correctos, size=16, weight="bold"),
                align="center"
            ),
            dict(
                x=0.5,  # Centrado horizontalmente
                y=-0.20,  # Segunda anotación (Faltantes), más abajo
                xref="paper",
                yref="paper",
                text=f"Faltantes: {faltantes} ({round(prop_faltantes*100)}%)",
                showarrow=False,
                font=dict(color=color_faltantes, size=15, weight="bold"),
                align="center"
            )
        ],

        yaxis=dict(scaleanchor="x", scaleratio=1)
    )
    
    fig.update_traces(
        xgap=1,
        ygap=1
    )
    
    fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False)
    fig.update_yaxes(showticklabels=False, showgrid=False, zeroline=False)
        
    return fig
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




with st.expander("Inventarios",expanded=st.session_state.expand_inventario_Realizado):

        
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
        # CSS para hacer el header responsive
        st.markdown("""
        <style>
            /* Estilo base del header */
            .table-header {
                text-align: center;
                font-weight: bold;
                padding: 10px;
                margin: 0;
            }
            
            /* Responsive para tablets */
            @media screen and (max-width: 1024px) {
                .table-header {
                    font-size: 13px;
                    padding: 8px 4px;
                }
            }
            
            /* Responsive para móviles */
            @media screen and (max-width: 768px) {
                .table-header {
                    font-size: 11px;
                    padding: 6px 2px;
                    word-wrap: break-word;
                }
            }
            
            /* Ajustar columnas en pantallas pequeñas */
            @media screen and (max-width: 768px) {
                div[data-testid="column"] {
                    padding: 0px 2px !important;
                    min-width: 60px;
                }
            }
        </style>
        """, unsafe_allow_html=True)
        headers_Procesado = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 2,2,2], gap="medium", vertical_alignment="top")
    
        _= '''headers[0].write("Tipo Inventario")
        headers[1].write("Ubicación")
        headers[2].write("Fecha")
        headers[3].write("Inicio")
        headers[4].write("Duración")
        headers[5].write("Correctos")
        headers[6].write("Faltantes")
        headers[7].write("Sobrantes")
        headers[8].write("Lectura")
        headers[9].write("N Conteo")
        headers[10].write("") '''

        header_texts = [
            "📍",
            "📅",
            "▶️",
            "📆",
            "🚁",
            "⏱️",
            "✅",
            "❗❗",
            "➖",
            "%",
            ""  # Empty string for the last column
        ]        

        for i, header in enumerate(headers_Procesado):
            with header:
                st.markdown(f"<p class='table-header' style='text-align: center;'>{header_texts[i]}</p>", unsafe_allow_html=True)
        if not datosJDE.empty:  # Check if the DataFrame is not empty
            for index, inventario in df_to_display.iterrows():  # Iterate over rows using iterrows()
                # Each row of the table
                col2, col3, col4,colA,colB, col5, col6, col7, col8, col9,col11 = st.columns([1, 2, 2,2,2, 2, 2, 2, 2, 2,2], gap="small", vertical_alignment="center")

                # Determine Tipo_inventario based on Ubicacion
                #Tipo_inventario = "Completo" if inventario["Ubicacion"] == "PT" else "Parcial"


                #col1.write(Tipo_inventario)
                col2.write(f"<p  style='text-align: center;font-size: 12px;'>{inventario['Ubicacion']}</p>", unsafe_allow_html=True) 
                col3.write(f"<p style='text-align: center;font-size: 12px;'>{DB.format_date(inventario["Fecha_Inventario"])}</p>", unsafe_allow_html=True) 
                col4.write(f"<p style='text-align: center;font-size: 12px;'>{DB.format_time(inventario["Fecha_Inventario"])}</p>", unsafe_allow_html=True) 

                colA.write(f"<p style='text-align: center;font-size: 12px;'>{DB.format_date(inventario["Fecha_Vuelo"])}</p>", unsafe_allow_html=True) 
                colB.write(f"<p style='text-align: center;font-size: 12px;'>{DB.format_time(inventario["Fecha_Vuelo"])}</p>", unsafe_allow_html=True) 

                col5.write(f"<p style='text-align: center;font-size: 12px;'>{DB.format_seconds_HHMMSS(inventario["Tiempo_Vuelo"])}</p>", unsafe_allow_html=True) 
            
        

                #col6.write(inventario["Elementos_OK"])
                col6.write(f"<p class='data-ok' style='text-align: center;'>{inventario["Elementos_OK"]}</p>", unsafe_allow_html=True)
                
                #col7.write(inventario["Elementos_Faltantes"])
                col7.write(f"<p class='data-missing' style='text-align: center;'>{inventario["Elementos_Faltantes"]}</p>", unsafe_allow_html=True)

            
                #col8.write(inventario["Elementos_Sobrantes"])
                col8.write(f"<p class='data-excess' style='text-align: center;'>{inventario["Elementos_Sobrantes"]}</p>", unsafe_allow_html=True)
                col9.write(f"<p style='text-align: center;'>{str(inventario["Porcentaje_Lectura"])}</p>", unsafe_allow_html=True) 
                #col10.write(f"<p style='text-align: center;'>{str(inventario["NumeroConteo"])}</p>", unsafe_allow_html=True) 
            

                # Botón de "Resumen"
                if col11.button("🔎", key=f"resumen_{inventario['ID']}"):
                    st.session_state.selected_inventory = inventario["ID"]
                    st.session_state.expand_resumen_inventario=True
                    st.session_state.expand_inventario_Realizado = False
            

        

        # Pagination buttons with center alignment
        # Pagination buttons with custom alignment
        col0,col1, col2, col3,col4 = st.columns([3,2, 2, 2,3],gap="small")  # Create three columns with different widths

        with col3:  # Next button column (left)
            if st.button("Siguiente"):
               
                if st.session_state.page2 < total_pages -1 :
                    st.session_state.page2 = st.session_state.page2 + 1
                    st.rerun()
                  


        with col2:  # Page indicator column (center)
            st.markdown(f"<p style='text-align: center;'>Página {st.session_state.page2 + 1} de {total_pages}</p>", unsafe_allow_html=True)

        with col1:  # Previous button column (right)
            if st.button("Anterior"):
                if st.session_state.page2 > 0:
                    st.session_state.page2 = st.session_state.page2 - 1
                    st.rerun()

        st.write('')

with st.expander("Ver detalle",expanded=st.session_state.expand_resumen_inventario):

#st.title("Resumen Inventario")

    if st.session_state.selected_inventory:          
        resumen_inventario = DB.obtener_elementos_jde(int(st.session_state.selected_inventory))

        Inventario_Realizado= datosJDE[datosJDE['ID'] == int(st.session_state.selected_inventory) ].squeeze()

        
        Tipo_inventario_r = "Completo" if Inventario_Realizado["Ubicacion"] == "PT" else "Parcial, en " + Inventario_Realizado["Ubicacion"]

        st.subheader("Inventario " + Tipo_inventario_r + ", realizado el " + DB.format_datetime(Inventario_Realizado["Fecha_Inventario"]) + ", " + " Número conteo: " +  str(Inventario_Realizado["NumeroConteo"])    )
    

        
        total_elementos=int(Inventario_Realizado["Elementos_OK"])+int(Inventario_Realizado["Elementos_Faltantes"])+int(Inventario_Realizado["Elementos_Sobrantes"])
    
    

        st.write('')

        # if st.session_state.show_content_advanced:
        #     col1, col2 = st.columns([2,2],gap="medium")
        #     with col1:
            
        #         headers_lecturas = st.columns([2, 1, 1], gap="small", vertical_alignment="top") 
        #         columns = ["Lecturas", "Nº Elementos","%"]
        #         for i, header in enumerate(headers_lecturas):
        #             with header:
        #                 st.markdown(f"<p class='table-header' style='text-align: left;'>{columns[i]}</p>", unsafe_allow_html=True) 

        #         # Each row of the table
        #         col10, col20, col30 = st.columns([2, 1, 1], gap="small", vertical_alignment="center")
        #         col10.write(f"<p class='data-ok' style='text-align: left;'>Correctos</p>", unsafe_allow_html=True)
        #         col20.write(f"<p class='data-ok' style='text-align: left;'>{Inventario_Realizado['Elementos_OK']}</p>", unsafe_allow_html=True)
        #         col30.write(f"<p class='data-ok' style='text-align: left;'>{int(Inventario_Realizado['Elementos_OK'] / total_elementos * 100)}%</p>", unsafe_allow_html=True)

        #         col10, col20, col30 = st.columns([2, 1, 1], gap="small", vertical_alignment="center")
        #         col10.write(f"<p class='data-missing' style='text-align: left;'>Faltantes</p>", unsafe_allow_html=True)
        #         col20.write(f"<p class='data-missing' style='text-align: left;'>{Inventario_Realizado['Elementos_Faltantes']}</p>", unsafe_allow_html=True)
        #         col30.write(f"<p class='data-missing' style='text-align: left;'>{int(Inventario_Realizado['Elementos_Faltantes'] / total_elementos * 100)}%</p>", unsafe_allow_html=True)

        #         col10, col20, col30 = st.columns([2, 1, 1], gap="small", vertical_alignment="center")
        #         col10.write(f"<p class='data-excess' style='text-align: left;'>Sobrantes</p>", unsafe_allow_html=True)
        #         col20.write(f"<p class='data-excess' style='text-align: left;'>{Inventario_Realizado['Elementos_Sobrantes']}</p>", unsafe_allow_html=True)
        #         col30.write(f"<p class='data-excess' style='text-align: left;'>{int(Inventario_Realizado['Elementos_Sobrantes'] / total_elementos * 100)}%</p>", unsafe_allow_html=True)
            
        #     with col2:
                
        #         headers_lecturas = st.columns([2, 1], gap="small", vertical_alignment="top") 
        #         columns = ["Vuelo", ""]
        #         for i, header in enumerate(headers_lecturas):
        #             with header:
        #                 st.markdown(f"<p class='fly-data' style='text-align: left;'>{columns[i]}</p>", unsafe_allow_html=True) 

        #         # Each row of the table
        #         col10, col20 = st.columns([2, 1], gap="small", vertical_alignment="center")
        #         col10.write(f"<p class='fly-data' style='text-align: left;'>Fecha</p>", unsafe_allow_html=True)
        #         col20.write(f"<p class='fly-data' style='text-align: left;'>{DB.format_date(Inventario_Realizado["Fecha_Vuelo"])}</p>", unsafe_allow_html=True)
        #         col10, col20 = st.columns([2, 1], gap="small", vertical_alignment="center")
        #         col10.write(f"<p class='fly-data' style='text-align: left;'>Hora</p>", unsafe_allow_html=True)
        #         col20.write(f"<p class='fly-data' style='text-align: left;'>{DB.format_time(Inventario_Realizado["Fecha_Vuelo"])}</p>", unsafe_allow_html=True)
        #         col10, col20 = st.columns([2, 1], gap="small", vertical_alignment="center")
        #         col10.write(f"<p class='fly-data' style='text-align: left;'>Fin</p>", unsafe_allow_html=True)
        #         col20.write(f"<p class='fly-data' style='text-align: left;'>{DB.add_seconds_to_timestamp_string(Inventario_Realizado["Fecha_Vuelo"],Inventario_Realizado["Tiempo_Vuelo"])}</p>", unsafe_allow_html=True)
        #         col10, col20 = st.columns([2, 1], gap="small", vertical_alignment="center")
        #         col10.write(f"<p class='fly-data' style='text-align: left;f'>Duración</p>", unsafe_allow_html=True)
        #         col20.write(f"<p class='fly-data' style='text-align: left;'>{DB.format_seconds_HHMMSS(int(Inventario_Realizado["Tiempo_Vuelo"]))}</p>", unsafe_allow_html=True)
        #     st.write('')
       
        left_co, cent_co,last_co = st.columns([8,0.1,0.1])
        
       
        with left_co:
                    #with st.container(height=420,border=False): 
                        
                    if Inventario_Realizado["Video_Vuelo"] is not None:
                        #st.write("Representación de vuelo realizado") #eliminar-pv
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

        
     

        #with last_co:
                #with st.container(height=420,border=False): 
                    #st.write("Distribución de elementos")
                    #with _lock:
                    #st.plotly_chart(figd)
                
   
        # Display the pie chart in Streamlit
        #st.plotly_chart(fig)

        

        st.write('')
        st.markdown("**Detalle por Fila**")
        def procesar_ubicacion(ubicacion):
            fila = ubicacion[3:6]
            rack = ubicacion[6:]
            return pd.Series([fila, rack])

        # Procesamiento de datos igual que antes
        resumen_inventario[['Fila', 'Rack']] = resumen_inventario['Ubicación'].apply(procesar_ubicacion)
        conteo = resumen_inventario.groupby(['Fila', 'Rack', 'Resultado']).size().unstack(fill_value=0)
        #conteo = conteo.reindex(columns=['Faltantes', 'Correctos'], fill_value=0)
        try:
            conteo.columns = ['Faltantes', 'Correctos']
        except:
            conteo = conteo.reindex(columns=['Faltantes', 'Correctos'], fill_value=0)
            
        nuevo_df = conteo.reset_index()

        # Definir número de columnas por fila
        num_cols = 4

        # Calcular cuántas filas de la UI necesitamos
        num_filas_ui = (len(nuevo_df) + num_cols - 1) // num_cols  # División con redondeo hacia arriba

        for fila_ui in range(num_filas_ui):
            # Crear una fila de columnas en Streamlit
            cols = st.columns(num_cols)
            
            # Iterar sobre los elementos de esta fila
            for col_idx in range(num_cols):
                # Calcular el índice en el dataframe
                df_idx = fila_ui * num_cols + col_idx
                
                # Verificar que no nos pasemos del final del dataframe
                if df_idx < len(nuevo_df):
                    row = nuevo_df.iloc[df_idx]
                    
                    # Mostrar el gráfico en la columna correspondiente
                    with cols[col_idx]:
                        fig = create_waffle_chart(
                            correctos=row['Correctos'], 
                            faltantes=row['Faltantes'], 
                            fila=int(row['Fila']), 
                            seccion=int(row['Rack'])
                        )
                        st.plotly_chart(fig)

        def highlight_resultado(row):
            # Estilo base para todas las celdas
            styles = ['background-color: black; color: #D3D3D3; font-size: 30px; font-weight: bold; border: 2px solid #444'] * len(row)
  
            return styles

        def style_dataframe_for_streamlit(df):
            """
            Styles a DataFrame for st.dataframe using Pandas Styler.
            ALL styling for headers and cells is done here.
            """
            header_properties = [
                ('background-color', '#D3D3D3'),
                ('color', '#f89256'),
                ('font-size', '22px'),
                ('font-weight', 'bold'),
                ('border', 'px solid #555')
            ]
            
            cell_properties = [
                ('background-color', 'black'),
                ('color', '#D3D3D3'), 
                ('font-size', '20px'),
                ('border', '1px solid #444')
            ]
            # Create a Styler object from the DataFrame
            styler = df.style
            

            # Apply styles to the data cells (td elements)
            styler.set_table_styles([
                {'selector': 'th', 'props': header_properties},
                {'selector': 'td', 'props': cell_properties}
            ], overwrite=False)

            # --- Optional: Add your original 'highlight_resultado' logic conditionally ---
            # If you need specific rows to have a different style based on their content,
            # you would use .apply() here.
            # For example, if you wanted to highlight rows based on the 'Estado' column:
            def highlight_estado(row):
                base_cell_style_str = "background-color: black; color: #D3D3D3; font-size: 16px; border: 2px solid #444;"
                
                estado = row['Resultado']
                text_color_override = None
                font_weight_override = None

                if estado == 'Faltante':
                    text_color_override = '#f89256'
                    #font_weight_override = 'bold'
                elif estado == 'Ok':
                    text_color_override = '#2bb534'
                    #font_weight_override = 'bold'
                # 'Disponible' will use the default cell_properties text color

                styles = []
                for col_name, val in row.items():
                    current_style = base_cell_style_str # Start with base
                    if col_name == 'Resultado': # Or apply to whole row
                        if text_color_override:
                            current_style += f" color: {text_color_override};"
                        if font_weight_override:
                            current_style += f" font-weight: {font_weight_override};"
                    styles.append(current_style)
                return styles

            # If you want to apply the conditional styling:
            # Make sure your 'Estado' column exists or adjust the condition
            if 'Resultado' in df.columns:
                styler = styler.apply(highlight_estado, axis=1)
                

            return styler

        # Aplicar solo este método de estilo
        styled_df = resumen_inventario.style.apply(highlight_resultado, axis=1)


        styled_df = styled_df.apply(highlight_resultado, axis=1)
        styled_df_output = style_dataframe_for_streamlit(resumen_inventario)
        

        st.write('')
        st.markdown("**Detalle**")
        pagination = st.container()
        #pagination.dataframe(data=styled_df, use_container_width=True)      
        pagination.dataframe(data=styled_df_output, use_container_width=True)
        #pagination.write(styled_df_output.to_html(), unsafe_allow_html=True)      
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

