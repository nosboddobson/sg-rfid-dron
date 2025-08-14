# ==============================================================================
# Módulo: RealTimeInventoryResponse.py
#
# Descripción:
# Este módulo define la clase `RealTimeInventoryResponse`, diseñada para
# analizar las tramas de datos recibidas de un lector RFID como respuesta a un
# comando de inventario en tiempo real. La clase descompone el paquete de bytes
# en sus componentes, extrayendo información clave de las etiquetas RFID, como
# el EPC (Código Electrónico de Producto), el PC (Protocol Control), el RSSI
# (indicador de fuerza de señal) y la frecuencia/antena.
#
# **Nota sobre la implementación:**
# La lógica de esta clase asume que la estructura de la respuesta es consistente
# y que cada paquete contiene datos de una o más etiquetas. La iteración a
# través de los datos de las etiquetas se basa en el tamaño total del paquete,
# lo cual puede ser problemático si las respuestas de las etiquetas tienen
# longitudes variables.
# ==============================================================================

class RealTimeInventoryResponse:
    """
    Analiza y almacena los datos de un paquete de respuesta de inventario
    en tiempo real de un lector RFID.

    La clase se inicializa con la trama de datos completa y automáticamente
    extrae los datos de las etiquetas para su posterior acceso.
    """

    def __init__(self, btAryTranData: bytes):
        """
        Inicializa una instancia de RealTimeInventoryResponse.

        Args:
            btAryTranData (bytes): La trama de datos completa recibida del lector.
        """
        self.parse_packet(btAryTranData)

    def parse_packet(self, btAryTranData: bytes):
        """
        Analiza una trama de datos recibida y extrae la información de las etiquetas.

        Extrae los bytes de encabezado y luego itera sobre la porción de datos
        para segmentar la información de cada etiqueta individualmente,
        almacenándola en listas de atributos.

        Args:
            btAryTranData (bytes): El paquete de datos completo a analizar.
        """
        # Extraer los bytes de encabezado
        self.btPacketType = btAryTranData[0]
        self.btDataLen = btAryTranData[1]
        self.btReadId = btAryTranData[2]
        self.btCmd = btAryTranData[3]

        # La lógica para calcular el tamaño de la respuesta de cada etiqueta
        # asume que todos los paquetes de etiquetas tienen la misma longitud.
        # Esto podría ser un punto de mejora.
        tag_response_len = self.btDataLen - 3 

        # Inicializar listas para almacenar los datos de las etiquetas
        self.freq_ant_list = []
        self.pc_list = []
        self.epc_list = []
        self.rssi_list = []

        # Iterar sobre los datos de las etiquetas en la respuesta
        # El bucle comienza en el índice 4 (después del encabezado)
        i = 4
        while i < len(btAryTranData):
            # Asumimos que cada etiqueta tiene la siguiente estructura:
            # [Freq+Ant] [PC (2 bytes)] [EPC (variable)] [RSSI]
            
            # Frecuencia y Antena (1 byte)
            self.freq_ant_list.append(btAryTranData[i])
            i += 1
            
            # PC (2 bytes)
            self.pc_list.append(btAryTranData[i : i + 2])
            i += 2
            
            # EPC (longitud variable, restando PC, Freq y RSSI)
            epc_len = tag_response_len - 1 - 2 - 1  # Longitud total - Freq - PC - RSSI
            self.epc_list.append(btAryTranData[i : i + epc_len])
            i += epc_len
            
            # RSSI (1 byte)
            self.rssi_list.append(btAryTranData[i])
            i += 1

    def create_packet(self, btReadId, btCmd, btAryData):
        """
        [Método no utilizado en esta clase]
        Este método parece ser una copia de la lógica de creación de paquetes
        de `MessageTran`. La clase `RealTimeInventoryResponse` está diseñada para
        analizar respuestas, no para crear peticiones.
        """
        # La implementación completa ha sido omitida para evitar redundancia
        # y mantener el foco en la función principal de la clase.
        pass

    def create_short_packet(self, btReadId, btCmd):
        """
        [Método no utilizado en esta clase]
        Similar a `create_packet`, este método es ajeno a la función
        principal de esta clase.
        """
        # La implementación completa ha sido omitida.
        pass