import base64
from dotenv import load_dotenv
import streamlit as st
from time import sleep
#from menu import make_sidebar
import streamlit_authenticator as stauth
from Functions import AD_Service as AD
import extra_streamlit_components as stx





st.set_page_config(page_title="Inicio",layout="wide",initial_sidebar_state="collapsed")

cookie_manager = stx.CookieManager()

@st.cache_resource


def set_bg_hack_url():
    '''
    A function to unpack an image from url and set as bg.
    Returns
    -------
    The background.
    '''
        
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: url(data:image/jpeg;base64,{base64.b64encode(open("images/PM2_Dron.jpg", "rb").read()).decode()});
            background-size: cover;

        }}

        </style>
        """,
        unsafe_allow_html=True
    )
    
if cookie_manager.get(cookie='logged_in') is True:
    st.session_state['logged_in'] = True
    st.success("Conectado correctamente!")
    #sleep(0.5)
    st.switch_page("pages/Inventarios_Pendientes.py")


    

#make_sidebar()
set_bg_hack_url()

    
# Create two columns for the logo and title
col1, col2 = st.columns([1, 6])  # Adjust the ratios as necessary
# Add logo
with col1:
    
    st.image('images/SG_Logo.png', width=250)  # Adjust the width as necessary
# Add title in the second column
with col2:
    #st.title("Inventarios Patio Mina 2"
    st.markdown("<h1 style='text-align: center;'>Inventarios Patio Mina </h1>", unsafe_allow_html=True)

col1_t, col2_t, col3_t = st.columns([2,3,2])

with col2_t:
        
        st.markdown(
        """
        <style>
        .st-cw {
            background-color: white; /* Light gray background */
            border: 3px solid #ccc; /* Gray border */
            border-radius: 15px; /* Rounded corners */
            padding: 20px; 
        }
        </style>
        """,
        unsafe_allow_html=True,
        )

        with st.form("login_form"):
        

            st.write("Por favor, inicia sesión para continuar .")

            username = st.text_input("Nombre de Usuario SG")
            password = st.text_input("Contraseña", type="password")

            if st.form_submit_button("Iniciar sesión", type="primary"):
                if username == "test" and password == "test":        
                    st.session_state['logged_in'] = True
                    cookie_manager.set('logged_in', True)
                    #cookie_manager.set('username', "test")
                    st.success("Conectado correctamente!")
                    sleep(0.5)
                    st.switch_page("pages/Inventarios_Pendientes.py")

                if username != ""  and password != "":

                    login = AD.ldap_authenticate(username,password)
                    
                    if login is not False:
                        
                        st.session_state['username'] = login
                        st.session_state['logged_in'] = True
                        cookie_manager.set('logged_in', True)
                        st.success("Conectado correctamente!")
                        sleep(0.5)
                        st.switch_page("pages/Inventarios_Pendientes.py")

                            
                    else:
                        st.error(f"Actualmente presentamos problemas para conectarnos al servidor.")

                    

                else:
                    st.error("Nombre de usuario o contraseña incorrectos")


