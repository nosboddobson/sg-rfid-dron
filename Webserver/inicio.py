import base64
import os
from dotenv import load_dotenv
import streamlit as st
from time import sleep
#from menu import make_sidebar
from ldap3 import Server, Connection, ALL, SUBTREE
from streamlit_cookies_controller import CookieController


st.set_page_config(page_title="Inicio",layout="wide",initial_sidebar_state="collapsed")




load_dotenv(override=True)

AD_SERVER = Server(os.getenv('AD_ADDRESS'), use_ssl=True, get_info=ALL)
USER_NAME = 'nombre_usuario'
USER_NAME_DOMAIN = os.getenv('AD_DOMAIN')+"\\{USER_NAME}"
USER_PASSWORD = "contraseña_usuario"  # checkear
SEARCH_BASE = os.getenv('AD_SEARCH_BASE')





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
             background: url(data:image/jpeg;base64,{base64.b64encode(open("images/PM2_Dron.jpeg", "rb").read()).decode()});
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True
     )
    


#make_sidebar()
#set_bg_hack_url()
controller = CookieController()

#redirigir si ya esta logeado
if st.session_state.get('logged_in',False):
    #st.session_state['logged_in'] = True
    #controller.set("logged_in", True)
    st.switch_page("pages/Inventarios_Pendientes.py")
    
# Create two columns for the logo and title
col1, col2 = st.columns([1, 6])  # Adjust the ratios as necessary
# Add logo
with col1:
    
    st.image('images/SG_Logo.png', width=250)  # Adjust the width as necessary
# Add title in the second column
with col2:
    #st.title("Inventarios Patio Mina 2")
    st.markdown("<h1 style='text-align: center;'>Inventarios Patio Mina </h1>", unsafe_allow_html=True)

col1_t, col2_t, col3_t = st.columns([2,3,2])

with col2_t:
    with st.form("login_form"):
    

        st.write("Por favor, inicia sesión para continuar .")

        username = st.text_input("Nombre de Usuario SG")
        password = st.text_input("Contraseña", type="password")

        if st.form_submit_button("Iniciar sesión", type="primary"):
         #   if username == "test" and password == "test":        
         #       st.session_state['logged_in'] = True
         #       controller.set("logged_in", True,path="/")
         #       st.success("Conectado correctamente!")
         #       sleep(0.5)
         #       st.switch_page("pages/Inventarios_Pendientes.py")
            if username != ""  and password != "":

                USER_NAME=username
                USER_PASSWORD=password
                USER_NAME_DOMAIN=f'quadra\\{USER_NAME}'
                # Crear una conexión
                conn = Connection(AD_SERVER, user=USER_NAME_DOMAIN,
                        password=USER_PASSWORD,
                        authentication='SIMPLE'
                        )
                
                try:
                    #print(f'User name: {USER_NAME}')
                    #print(f'User password: {USER_PASSWORD}')
                    print(f'Estado conexión: {conn.bind()}')
                    
                    if conn.bind():
                        search_filter = f'(SAMAccountName={USER_NAME})'

                        search_result = conn.search(search_base=SEARCH_BASE,
                                                    search_filter=search_filter,
                                                    attributes=["cn"],
                                                    )
                        #print(search_result)
                        if conn.entries:
                            user_info = conn.entries[0]
                            user_name = user_info.cn
                            #print(user_name)
                            st.session_state['username']=user_name
                            controller.set("logged_in", True,path="/")
                            st.session_state['logged_in'] = True
                            st.success("Conectado correctamente!")
                            sleep(0.5)
                            st.switch_page("pages/Inventarios_Pendientes.py")
                        print("Conexión cerrada")
                        conn.unbind()
                    else:
                        st.error(f"Actualmente presentamos problemas para conectarnos al servidor.")
                except Exception as e:
                    print(f"Error en la conexión: {e}")

                

            else:
                st.error("Nombre de usuario o contraseña incorrectos")

   


