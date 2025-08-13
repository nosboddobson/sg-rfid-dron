import base64
from dotenv import load_dotenv
import streamlit as st
from time import sleep
import streamlit_authenticator as stauth
from Functions import AD_Service as AD
import extra_streamlit_components as stx
import os
from PIL import Image

st.set_page_config(page_title="Inicio", layout="wide", initial_sidebar_state="collapsed")

cookie_manager = stx.CookieManager()

@st.cache_resource
def set_bg_hack_url():
    '''
    A function to unpack an image from url and set as bg.
    Returns
    -------
    The background.
    '''
    # Asegurándonos que la ruta es correcta
    bg_image_path = "images/PM2_Dron.jpg"
    if os.path.exists(bg_image_path):
        st.markdown(
            f"""
            <style>
            .stApp {{
                background: url(data:image/jpeg;base64,{base64.b64encode(open(bg_image_path, "rb").read()).decode()});
                background-size: cover;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        st.error(f"No se encontró la imagen de fondo en: {bg_image_path}")
    
# Comprobar si el usuario ya está logueado
if cookie_manager.get(cookie='logged_in') is True:
    st.session_state['logged_in'] = True
    st.success("Conectado correctamente!")
    st.switch_page("pages/Inventarios_Pendientes.py")

# Aplicar el fondo
set_bg_hack_url()
    
# Create two columns for the logo and title
col1, col2 = st.columns([1, 6])  # Adjust the ratios as necessary

# Add logo in the first column - responsive version
with col1:
    # Verificar que la imagen existe antes de mostrarla
    logo_path = "images/SG_Logo.png"
    
    if os.path.exists(logo_path):
        # Cargar la imagen con PIL para garantizar que funciona
        logo_img = Image.open(logo_path)
        st.image(logo_img, use_container_width=True)
    else:
        st.error(f"No se encontró el logo en: {logo_path}")
        
        # Solución alternativa: probar con una ruta relativa diferente
        alternative_paths = [
            "./images/SG_Logo.png",
            "../images/SG_Logo.png",
            "static/images/SG_Logo.png",
            "app/images/SG_Logo.png"
        ]
        
        for alt_path in alternative_paths:
            if os.path.exists(alt_path):
                st.image(alt_path, use_container_widthh=True)
                st.success(f"Logo encontrado en ruta alternativa: {alt_path}")
                break

# Add title in the second column
with col2:
    st.markdown("<h1 style='text-align: center;'>Sierra Dron - Gerencia Operativa Supply Chain </h1>", unsafe_allow_html=True)

col1_t, col2_t, col3_t = st.columns([2, 3, 2])

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
        st.write("Por favor, inicia sesión para continuar.")

        username = st.text_input("Nombre de Usuario SG")
        password = st.text_input("Contraseña", type="password")

        if st.form_submit_button("Iniciar sesión", type="primary"):
            if username == "test" and password == "test":  
                st.session_state['username'] = "Test"      
                st.session_state['logged_in'] = True
                cookie_manager.set('logged_in', True,key='logged_in_cookie')
                cookie_manager.set('username', "Test",key='username_cookie')
                st.success("Conectado correctamente!")
                sleep(0.5)
                st.switch_page("pages/Inventarios_Pendientes.py")

            if username != "" and password != "":
                login = AD.ldap_authenticate(username, password)
                
                if login is not False:
                    st.session_state['username'] = username
                    st.session_state['logged_in'] = True
                    cookie_manager.set('logged_in', True,key='logged_in_cookie')
                    cookie_manager.set('username', username,key='username_cookie')
                    st.success("Conectado correctamente!")
                    sleep(0.5)
                    st.switch_page("pages/Inventarios_Pendientes.py")
                else:
                    st.error(f"Actualmente presentamos problemas para conectarnos al servidor.")
            else:
                st.error("Nombre de usuario o contraseña incorrectos")