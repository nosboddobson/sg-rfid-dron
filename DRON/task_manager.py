import asyncio
import logging


get_reads_task = None
is_task_running = False
_loop = None  # Variable para almacenar el bucle de eventos
pending_files_to_send = []
current_csv_path = None

def set_get_reads_task(task):
    global get_reads_task
    global is_task_running
    get_reads_task = task
    is_task_running = True

def set_event_loop(loop):
    global _loop
    _loop = loop

def _restart_task(get_reads_func,flag_reset_func):
    """Función auxiliar que se ejecuta dentro del bucle de eventos."""
    global get_reads_task
    global is_task_running

    if get_reads_task and not get_reads_task.done():
        logging.info("Reiniciando tarea 'get_reads'...")
        # -------------------------------------------------------------
        # CAMBIO CRÍTICO: Añadir el archivo a la cola AQUÍ de forma síncrona
        # -------------------------------------------------------------
        if current_csv_path:
            pending_files_to_send.append(current_csv_path)
            logging.info(f"Archivo '{current_csv_path}' añadido a la cola de envío.")
            #print  (f"Archivo '{current_csv_path}' añadido a la cola de envío.")

        get_reads_task.cancel()
        is_task_running = False
    
    if not is_task_running:
         # Llamar a la función para reiniciar el flag antes de crear la nueva tarea
        if flag_reset_func:
            flag_reset_func()

        get_reads_task = asyncio.create_task(get_reads_func())
        print ("Nueva tarea 'get_reads' creada.")
        logging.info("Nueva tarea 'get_reads' creada.")
        is_task_running = True

def restart_get_reads(get_reads_func, flag_reset_func=None):
    """
    Programa el reinicio de la tarea de forma segura desde cualquier hilo.
    """
    global _loop
    if _loop and _loop.is_running():
        print("Reiniciando tarea 'get_reads' de forma segura...")
        _loop.call_soon_threadsafe(_restart_task, get_reads_func, flag_reset_func)
        
    else:
        logging.error("No hay un bucle de eventos de asyncio en ejecución para reiniciar la tarea.")