import streamlit as st
from time import sleep
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages
import extra_streamlit_components as stx

cookie_manager = stx.CookieManager()


@st.cache_resource   
def get_current_page_name():
    ctx = get_script_run_ctx()
    if ctx is None:
        raise RuntimeError("Couldn't get script context")

    pages = get_pages("")
    #print(pages)

    return pages[ctx.page_script_hash]["page_name"]


def make_sidebar():
    
    no_sidebar_style = """
    <style>
        div[data-testid="stSidebarNav"] {display: none;}
        
        /* Estilo responsive para la imagen del logo */
        .sidebar-logo {
            width: 100%;
            max-width: 250px; 
            height: auto;
            margin-bottom: 20px;
        }
        
        /* Ajustes para pantallas pequeñas */
        @media screen and (max-width: 768px) {
            .sidebar-logo {
                max-width: 150px;
            }
        }
    </style>
    """
    st.markdown(no_sidebar_style, unsafe_allow_html=True)

    with st.sidebar:

        st.image('images/SG_Logo.png', use_column_width=True)
        
        #st.page_link("inicio.py", label="Inicio")
        st.write("")
        st.write("")
        if st.session_state.get("logged_in", False):
            st.page_link("pages/Inventarios_Pendientes.py", label="Inventarios Pendientes" )
            st.page_link("pages/Inventarios_Realizados.py", label="Inventarios Realizados")
            st.page_link("pages/Inventarios_Log.py", label="Log de Vuelos")
            st.page_link("pages/logout.py", label="Cerrar sesión")
       
        elif get_current_page_name() != "inicio":

            st.switch_page("inicio.py")

        print(str())

def main():
    # Mostrar el logo de manera responsive
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.image('images/SG_Logo.png', use_column_width=True)
    
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