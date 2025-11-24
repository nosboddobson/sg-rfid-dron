# Sierra Dron — Resumen rápido

Este repositorio contiene la API Flask (backend) y la interfaz Streamlit (web) para el sistema "Sierra Dron". A continuación se explica de forma concisa la responsabilidad de los dos archivos solicitados y cómo ejecutarlos.

## Archivos principales
- [Server.py](Server.py) — Servidor Flask que expone endpoints para orquestar la actualización de inventarios, recepción de archivos y keep-alive del dron. Referencias a funciones clave:
  - [`Server.actualizar_inventario`](Server.py) — Orquesta generación/recepción/comparación de inventario con JD Edwards, persistencia y creación de video.
  - [`Server.actualizar_estado_inventario`](Server.py) — Endpoint que valida y procesa el JSON de estado de inventario.
  - [`Server.upload_file`](Server.py) — Endpoint `/upload` que recibe CSVs desde el dron y los guarda/registrar en DB.
  - [`Server.show_message`](Server.py) — Endpoint `/printer/<msg>` usado como keep-alive y para detectar petición web de envío desde la UI.
- [Webserver/inicio.py](Webserver/inicio.py) — Aplicación Streamlit que implementa la UI de inicio/login y puntos de entrada a las páginas. Función relevante:
  - [`inicio.log_event`](Webserver/inicio.py) — Helper para escribir eventos en LOG_FILE.

También útil:
- [Webserver/Webserver_as_a_service.bat](Webserver/Webserver_as_a_service.bat) — Script de Windows para iniciar la UI Streamlit en modo headless.

## Flujo rápido (alto nivel)
1. El dron o cliente sube CSVs a `POST /upload` (`Server.upload_file`) → Server guarda archivos y actualiza DB.
2. Desde la UI Streamlit se invocan acciones que llaman endpoints como `/dron/actualizar-inventario` (`Server.actualizar_inventario`) o `/dron/actualizar-estado-inventario` (`Server.actualizar_estado_inventario`) para orquestar la generación de conteos en JD, comparar y persistir resultados.
3. El endpoint `/printer/<msg>` (`Server.show_message`) sirve como heartbeat/keep-alive y detecta si la UI solicitó al dron enviar datos (devuelve 201 si se presionó el botón).
4. Logs y auditoría: el servidor escribe en el fichero configurado por `DRON_API_LOG_PATH` (ver `.env`) y en CSVs mediante `Services/LogService.py`.

## Variables de entorno (usadas con dotenv)
- DRON_API_LOG_PATH — ruta por defecto del log del servidor (p. ej. `D:/logs/Sierra_dron_api.txt`).
- JD_REMOTE_FOLDER, JD_REMOTE_FOLDER_USERNAME, JD_REMOTE_FOLDER_PASSWORD — usadas por `Services.DronService`.
- DB_DRON_* — credenciales de la BD usadas por `Webserver/Functions/DB_Service.py`.
- DRON_FOLDER — carpeta donde se almacenan archivos recibidos del dron.

(Revisa el `.env` en la raíz para valores actuales.)

## Cómo ejecutar (desarrollo)
- Iniciar la API Flask:
  - Desde la raíz del repo:
    ```sh
    python Server.py
    ```
  - El servidor escucha por defecto en `0.0.0.0:5100`.

- Iniciar la UI Streamlit:
  - Manual:
    ```sh
    streamlit run Webserver/inicio.py --server.headless true
    ```
  - En Windows como servicio (usa el .bat):
    - Ejecutar: 

## Rutas importantes (ejemplos)
- GET /test — endpoint de prueba.
- POST /upload — subir archivo CSV ().
- POST /dron/actualizar-inventario — proceso principal ().
- POST /dron/actualizar-estado-inventario — valida y actualiza estado ().
- POST /printer/<msg> — heartbeat / comprobar botón de envío ().

## Logs y trazabilidad
- El logger del servidor se configura en  y escribe en la ruta indicada por `DRON_API_LOG_PATH`.
- Las ejecuciones y recepciones de archivos se registran con .

## Dónde mirar para entender la lógica completa
- Lógica de integración con JD: 
- Persistencia y consultas:  y 
- Procesamiento de CSVs recibidos:  y 

---

Para cambios puntuales en comportamiento del endpoint o flujos, abrir los archivos:
- 
- 
- 