import streamlit as st
from time import sleep
import extra_streamlit_components as stx

cookie_manager = stx.CookieManager()

def main():
  
    if "logged_in" in st.session_state:
        del st.session_state["logged_in"]
    else:
        pass

    cookies = cookie_manager.get_all()
    if "logged_in" in cookies:
        cookie_manager.delete("logged_in")

    st.query_params.clear()    
    st.info("Sesión Cerrada correctamente...")
    sleep(1)
    st.switch_page("inicio.py")

if __name__ == "__main__":
    main()