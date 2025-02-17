
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
    </style>
    """
    st.markdown(no_sidebar_style, unsafe_allow_html=True)

    with st.sidebar:
        st.title("Inventarios Patio SG")
        st.write("")
        st.page_link("inicio.py", label="Inicio", icon="🏠")
        st.write("")

        #if controller.get("logged_in"):
        if st.session_state.get("logged_in", False):
            st.page_link("pages/Inventarios_Pendientes.py", label="Patio Mina 2", icon="🕵️")
    

            st.write("")
            st.page_link("pages/Inventarios_Log.py", label="Log de Vuelos", icon="📃")
            st.write("")

            if st.button("Cerrar Sesión"):
                logout()

        elif get_current_page_name() != "inicio":
            # If anyone tries to access a secret page without being logged in,
            # redirect them to the login page
            st.switch_page("inicio.py")

        print (str())
def logout():


    if st.session_state.get('logged_in',True):  
       
        del st.session_state["logged_in"]  # Update session state
        cookie_manager.delete("logged_in")

        st.query_params.clear()    
        st.info("Sesión Cerrada correctamente!")
        sleep(0.5)
        st.switch_page("inicio.py")
    else: 
        st.warning("Aún no inicias sesión")