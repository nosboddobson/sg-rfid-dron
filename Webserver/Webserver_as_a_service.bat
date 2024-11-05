@echo off
set STREAMLIT_PATH=C:\Users\ra-rdobson\AppData\Local\Programs\Python\Python312\Scripts\streamlit.exe
set APP_PATH=D:\dev\sg-rfid-dron\Webserver\inicio.py
set STREAMLIT_EMAIL_ADDRESS=roberto.dobson@sgscm.cl
set STREAMLIT_HEADLESS=true

"%STREAMLIT_PATH%" run "%APP_PATH%" --server.headless true > D:\dev\sg-rfid-dron\Webserver\website_log.log 2>&1