
import os
from dotenv import load_dotenv
from ldap3 import ALL, Connection, Server


load_dotenv(override=True)

AD_SERVER = Server(os.getenv('AD_ADDRESS'), use_ssl=True, get_info=ALL)
USER_NAME = 'nombre_usuario'
USER_NAME_DOMAIN = os.getenv('AD_DOMAIN')+"\\{USER_NAME}"
USER_PASSWORD = "contraseña_usuario"  # checkear
SEARCH_BASE = os.getenv('AD_SEARCH_BASE')


def ldap_authenticate(username,password):
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
                return user_name
            else: 
                return False
            
            
    except Exception as e:
                        print(f"Error en la conexión: {e}")
    finally:
            
            if conn:
                conn.unbind()
                print("Conexión cerrada")