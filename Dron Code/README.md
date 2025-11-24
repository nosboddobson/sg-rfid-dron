# Suscriber_Reader.py — README

Resumen
-------
Script principal del sistema de inventario RFID ejecutado en el dron. Orquesta la comunicación con un lector RFID, procesa lecturas en tiempo real, las almacena en CSV y comunica estado/archivos a servicios externos (servidor central y Telegram). Emplea asyncio para tareas concurrentes y evita bloquear el bucle de eventos usando operaciones de I/O en hilos (asyncio.to_thread).

Requisitos
---------
- Python 3.10+ (recomendado)
- Dependencias (instalar via pip):
  - pandas
  - otras dependencias internas del proyecto (Services.*, EpcTranslator, MessageTran)
- Acceso a la red al lector RFID (IP y puerto configurados en el código).
- Permisos de escritura en la carpeta `files` (ubicada junto al script).

Ubicación de salida
-------------------
- Archivos CSV generados en: <repo>/Dron Code/files  
  Nombre: `sierradron_lecturas_<YYYYMMDD_HHMMSS>.csv`

Configuración importante
-----------------------
- IP del lector: `ip = '192.168.1.200'` (configurado en send_message)
- Puerto del lector: `port = 4001`
- Ruta del log configurada por defecto:
  `/home/sg-sierra-dron/Documents/sierra-dron/sg-rfid-dron/log/mi_programa.log`
  (ajustar según entorno Windows/ráiz del repo)

Componentes principales
-----------------------
- Funciones utilitarias:
  - calculate_frequency_and_antenna(value): devuelve (MHz, antenna_id)
  - rssi_data(rssi): normaliza RSSI (retorna valor positivo/legible)
  - pc_data(bytes_data): formatea PC bytes a hex legible
- Comunicación con lector:
  - send_message(bt_ary_tran_data): abre conexión TCP asíncrona, envía trama y lee respuesta con reintentos y timeout
- Persistencia:
  - write_to_csv(csv_path, fieldnames, data): escribe una fila en CSV usando AsyncFileWriter
  - AsyncFileWriter: contexto asíncrono que ejecuta apertura/cierre de archivo en hilo
- Lógica de lectura:
  - get_reads(): bucle infinito que solicita lecturas al lector, traduce EPC, calcula metadatos, mantiene estado en memoria (`epc_data`) y escribe CSV
- Servicios y administración:
  - check_network_status(), send_heartbeat(), send_periodic_message(): chequeos periódicos, envío de heartbeat y publicación de CSVs pendientes via PublisherService
  - initialize_system(): comprobaciones iniciales (red, hora) y notificaciones
  - main(): orquesta tasks asincrónicas (send_periodic_message y get_reads) y maneja cierre/cancelación

Cómo ejecutar
-------------
Desde la carpeta del script:
- Linux / macOS / Windows (PowerShell/CMD):
  ```
  python "Dron Code\Suscriber_Reader.py"
  ```
- Ejecuta indefinidamente; detener con Ctrl+C.

Registro (logging)
------------------
- Nivel por defecto: DEBUG
- Archivo de log (modificar si se ejecuta en Windows): ajustar la ruta en logging.basicConfig para que apunte dentro del repo o a una carpeta de logs accesible.

Buenas prácticas y notas
------------------------
- Ajustar la ruta del log para el entorno de despliegue.
- Validar y, si corresponde, parametrizar IP/PUERTO del lector para no hardcodearlos.
- Revisar las dependencias del paquete `Services` y asegurarse de que sus funciones (PublisherService, MessageService, StatusService, TelegramService) estén disponibles y correctamente configuradas.
- Para entornos con alto volumen de lectura, considerar persistir epc_data periódicamente o rotar archivos CSV para evitar crecer indefinidamente en memoria.
- Probar la conectividad TCP al lector antes de ejecutar (p. ej. telnet o nc) y comprobar permisos de red/firewall.

Errores comunes
---------------
- Timeout de socket: comprobar IP/PUERTO y que el lector esté en la misma red.
- Permiso denegado al crear logs/CSV: comprobar rutas y permisos de escritura.
- ImportError en módulos del proyecto: ejecutar desde la raíz del repo o añadirla al PYTHONPATH.

Contacto
-------
Revisar módulos Services y configuraciones del proyecto para detalles de integración con servidor central y Telegram.