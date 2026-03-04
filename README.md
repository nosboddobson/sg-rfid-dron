# Sierra Dron — Resumen rápido

Este repositorio contiene la API Flask (backend) y la interfaz Streamlit (web) para el sistema "Sierra Dron". A continuación se explica de forma concisa la responsabilidad de los dos archivos solicitados y cómo ejecutarlos.

## Archivos principales
- [Server.py](Server.py) — Servidor Flask que expone endpoints para orquestar la actualización de inventarios, recepción de archivos y keep-alive del dron. Referencias a funciones clave:
  - `actualizar_inventario` — Orquesta generación/recepción/comparación de inventario con JD Edwards, persistencia y creación de video.
  - `actualizar_estado_inventario` — Endpoint que valida y procesa el JSON de estado de inventario.
  - `upload_file` — Endpoint `/upload` que recibe CSVs desde el dron y los guarda/registra en BD.
  - `show_message` — Endpoint `/printer/<msg>` usado como keep-alive y para detectar petición web de envío desde la UI.
- [Webserver/inicio.py](Webserver/inicio.py) — Aplicación Streamlit que implementa la UI de inicio/login y puntos de entrada a las páginas.
- [Webserver/Webserver_as_a_service.bat](Webserver/Webserver_as_a_service.bat) — Script de Windows para iniciar la UI Streamlit en modo headless.

## 📚 Documentación API (Swagger/OpenAPI)

La API incluye documentación interactiva generada automáticamente con **Swagger UI** usando **Flasgger**.

### Acceso a Swagger UI
Una vez que el servidor Flask esté ejecutándose, accede a la documentación interactiva:

```
http://localhost:5100/apidocs
```

**Alternativas:**
- ReDoc (documentación alternativa): `http://localhost:5100/redoc`
- Especificación JSON: `http://localhost:5100/swagger.json`

### Características de la documentación
- ✅ Descripción detallada de cada endpoint
- ✅ Parámetros de entrada y validaciones
- ✅ Esquemas de respuesta para cada código de estado HTTP
- ✅ Interfaz interactiva para probar endpoints
- ✅ Ejemplos de uso y respuestas

Para más detalles, ver [SWAGGER.md](SWAGGER.md).

## Flujo rápido (alto nivel)
1. El dron o cliente sube CSVs a `POST /upload` → Server guarda archivos y actualiza BD.
2. Desde la UI Streamlit se invocan acciones llamando endpoints como `POST /dron/actualizar-inventario` o `POST /dron/actualizar-estado-inventario` para orquestar la generación de conteos en JD, comparar y persistir resultados.
3. El endpoint `POST /printer/<msg>` sirve como heartbeat/keep-alive y detecta si la UI solicitó al dron enviar datos (devuelve 201 si se presionó el botón).
4. **Logs y auditoría:** El servidor escribe en el fichero configurado por `DRON_API_LOG_PATH` y en CSVs mediante `Services/LogService.py`.

## Variables de entorno (usadas con dotenv)
- `DRON_API_LOG_PATH` — Ruta por defecto del log del servidor (p. ej. `D:/logs/Sierra_dron_api.txt`).
- `JD_REMOTE_FOLDER`, `JD_REMOTE_FOLDER_USERNAME`, `JD_REMOTE_FOLDER_PASSWORD` — Usadas por `Services.DronService` para conectar a carpeta compartida de JD Edwards.
- `DB_DRON_*` — Credenciales de la BD usadas por `Webserver/Functions/DB_Service.py`.
- `DRON_FOLDER` — Carpeta donde se almacenan archivos recibidos del dron.

(Revisa el `.env` en la raíz para valores actuales.)

## Cómo ejecutar (desarrollo)

### Iniciar la API Flask
Desde la raíz del repo:
```bash
python Server.py
```
- El servidor escucha por defecto en `0.0.0.0:5100`
- Accede a Swagger en: `http://localhost:5100/apidocs`

### Iniciar la UI Streamlit
**Manual:**
```bash
streamlit run Webserver/inicio.py --server.headless true
```

**En Windows como servicio (usa el script .bat):**
```bash
Webserver_as_a_service.bat
```

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/test` | Endpoint de prueba de conectividad |
| POST | `/upload` | Subir archivo CSV desde el dron |
| POST | `/dron/actualizar-inventario` | Proceso principal de actualización de inventario |
| POST | `/dron/actualizar-estado-inventario` | Valida y actualiza estado del inventario |
| POST | `/printer/<msg>` | Heartbeat / comprobar solicitud de envío |
| POST | `/dron/eliminar-inventario` | Eliminar registro de inventario |
| POST | `/dron/TestJDFolder` | Verificar conexión a carpeta compartida de JD |
| POST | `/api/data` | Endpoint genérico para recibir datos JSON |

## Logs y trazabilidad
- **Logger del servidor:** Se configura en `Server.py` y escribe en la ruta indicada por `DRON_API_LOG_PATH`
- **Auditoría:** Las ejecuciones y recepciones de archivos se registran con `Services/LogService.py`
- **Histórico de ejecuciones:** Ver `Api_Executions.csv`

## Dónde mirar para entender la lógica completa
- **Integración con JD Edwards:** [Services/JDService.py](Services/JDService.py)
- **Persistencia de datos:** [Services/MsSQL_Service.py](Services/MsSQL_Service.py), [Services/SQLite_Service.py](Services/SQLite_Service.py)
- **Procesamiento de CSVs:** [DRON/Suscriber_Reader.py](DRON/Suscriber_Reader.py), [DRON/EpcTranslator.py](DRON/EpcTranslator.py)
- **Generación de videos 3D:** [Services/Video_Service.py](Services/Video_Service.py)

## Instalación de dependencias

```bash
pip install -r requirements.txt
```

Este proyecto requiere:
- Python 3.8+
- Flask 3.0.3
- Flasgger 0.9.7.1 (para documentación Swagger)
- Streamlit (para UI)
- pandas, pyodbc, python-dotenv, y más (ver requirements.txt)

## Remote de respaldo en Azure DevOps

El repositorio está configurado con un remote de respaldo en Azure DevOps:

```bash
# Ver remotes
git remote -v

# Hacer push a respaldo
git push backup main

# Push forzado (reemplaza contenido)
git push backup main --force
```

---

Para cambios puntuales en comportamiento del endpoint o flujos, abrir los archivos relevantes en `Server.py`, `Services/`, o `DRON/`.
