import time
import streamlit as st
from time import sleep
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages
import extra_streamlit_components as stx
from Functions import DB_Service as DB
cookie_manager = stx.CookieManager()


@st.cache_resource   
def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("Couldn't get script context")

    pages = get_pages("")
    return pages[ctx.page_script_hash]["page_name"]


def make_navbar():
    """Navbar con botones horizontales"""
    
    # Ocultar el sidebar predeterminado y la flecha
    hide_sidebar_style = """
    <style>
        [data-testid="stSidebar"] {display: none;}
        div[data-testid="stSidebarNav"] {display: none;}
        
        /* Ocultar la flecha de colapsar sidebar */
        button[kind="header"] {display: none;}
        [data-testid="collapsedControl"] {display: none;}
        /* Reducir el espacio superior */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }
        /* Ocultar el iframe del CookieManager */
        iframe[title="extra_streamlit_components.CookieManager.cookie_manager"] {
            display: none;
        }
        
        /* Ocultar todos los custom components con altura 0 */
        .stCustomComponentV1[height="0"] {
            display: none;
        }
        /* Reducir espacio del header */
        header[data-testid="stHeader"] {
            padding-top: 0rem;
        }
        
        /* Ajustar el espacio de los botones */
        div[data-testid="column"] {
            padding: 0px 5px;
        }
    
    
    </style>
    """
    st.markdown(hide_sidebar_style, unsafe_allow_html=True)
    
    
    
    # Menú horizontal con botones
    if st.session_state.get("logged_in", False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📋 Pendientes", use_container_width=True):
                st.switch_page("pages/Inventarios_Pendientes.py")
        
        with col2:
            if st.button("✅ Realizados", use_container_width=True):
                st.switch_page("pages/Inventarios_Realizados.py")
        
        with col3:
            if st.button("📝 Log", use_container_width=True):
                st.switch_page("pages/Inventarios_Log.py")
        
        with col4:
            # if st.button("🚪 Cerrar", use_container_width=True):
            #     st.switch_page("pages/logout.py")
            ####Comunicacion y estado de Dron
            Dron_Status = DB.get_last_heartbeat_and_compare()
            if not Dron_Status:

                

                datos1 = DB.obtener_datos_inventarios_pendientes()

               

                if st.button("🔴 Solicitar Inventario", help="Dron en línea, Solicitar inventario.", type="primary",use_container_width=True):
                    
                    #DB.Dron_SET_Boton_Envio_Datos_Hora(cookie_manager.get(cookie='username'))
        
                    for i in range(10):
                        st.toast("Esperando Inventario...")
                        time.sleep(5)
                        datos2 = DB.obtener_datos_inventarios_pendientes()
                        if len(datos2)>len(datos1):
                            st.toast("¡Inventario Recibido!", icon='🎉')
                            #st.balloons()
                            time.sleep(5)
                            success=True
                            break
                        success=False   
                    if not success:
                            st.toast("¡Ningún Inventario Recibido!", icon='😞')
                            time.sleep(5)


                    st.rerun()

            else:
                    st.button("🚁 Fuera de Linea ",help="Dron no conectado a la red",type="tertiary",use_container_width=True)
        
         
    
    elif get_current_page_name() != "inicio":
        st.switch_page("inicio.py")


def main():
    if "logged_in" in st.session_state:
        del st.session_state["logged_in"]

    try:
        cookie_manager.delete("logged_in")
    except KeyError:
        pass
    
    st.query_params.clear()    
    st.info("Sesión Cerrada correctamente!")
    sleep(0.5)
    st.switch_page("inicio.py")


if __name__ == "__main__":
    main()