# ==============================================================================
# Módulo: MessageTran.py
#
# Descripción:
# Este módulo define la clase `MessageTran`, que es fundamental para la
# comunicación con un lector RFID. Se encarga de crear las tramas de datos
# (paquetes) que se envían al lector y de parsear las respuestas que se reciben.
# Sigue un protocolo de comunicación específico que incluye un tipo de paquete,
# una longitud de datos, un ID de lectura, un comando, la carga útil de datos
# y un byte de checksum para la validación de la integridad.
#
# La clase soporta la creación de paquetes largos (con datos), paquetes cortos
# (sin datos) y el análisis de paquetes recibidos.
# ==============================================================================

class MessageTran:
    """
    Gestiona la creación y el análisis de paquetes de datos para la
    comunicación con el lector RFID.

    La clase se puede inicializar de varias maneras:
    - Con `btReadId`, `btCmd` y `btAryData` para crear un paquete completo.
    - Con `btReadId` y `btCmd` para crear un paquete corto.
    - Con `btAryTranData` para analizar un paquete recibido.
    - Sin argumentos para crear un objeto vacío.
    """

    def __init__(self, btReadId=None, btCmd=None, btAryData=None, btAryTranData=None):
        """
        Inicializa una instancia de MessageTran con la lógica adecuada.

        Args:
            btReadId (int, optional): ID de lectura. Usado para identificar el lector.
            btCmd (int, optional): Byte de comando. Define la operación a realizar.
            btAryData (list[int], optional): La carga útil de datos del paquete.
            btAryTranData (bytes, optional): La trama de datos completa a analizar.
        """
        if btReadId is not None and btCmd is not None and btAryData is not None:
            self.create_packet(btReadId, btCmd, btAryData)
        elif btReadId is not None and btCmd is not None:
            self.create_short_packet(btReadId, btCmd)
        elif btAryTranData is not None:
            self.parse_packet(btAryTranData)
        else:
            self.btPacketType = None
            self.btDataLen = None
            self.btReadId = None
            self.btCmd = None
            self.btAryData = None
            self.btCheck = None
            self.btAryTranData = None

    @property
    def AryTranData(self) -> bytes:
        """
        Devuelve la trama de datos completa (paquete) lista para ser enviada.

        Returns:
            bytes: La trama de datos completa.
        """
        return self.btAryTranData

    @property
    def AryData(self) -> bytearray:
        """
        Devuelve la carga útil de datos del paquete.

        Returns:
            bytearray: Los datos del paquete.
        """
        return self.btAryData

    @property
    def ReadId(self) -> int:
        """
        Devuelve el ID de lectura.

        Returns:
            int: El ID del lector.
        """
        return self.btReadId

    @property
    def Cmd(self) -> int:
        """
        Devuelve el byte de comando.

        Returns:
            int: El comando del paquete.
        """
        return self.btCmd

    @property
    def PacketType(self) -> int:
        """
        Devuelve el tipo de paquete.

        Returns:
            int: El tipo de paquete (ej. 0xA0).
        """
        return self.btPacketType

    def create_packet(self, btReadId: int, btCmd: int, btAryData: list[int]):
        """
        Crea un paquete de comunicación completo con datos.

        Esta función construye la trama de datos `btAryTranData` a partir de
        los parámetros de entrada, incluyendo el cálculo del checksum.

        Args:
            btReadId (int): ID de lectura.
            btCmd (int): Comando de la operación.
            btAryData (list[int]): Lista de enteros que forman la carga útil.
        """
        nLen = len(btAryData)
        
        self.btPacketType = 0xA0
        self.btDataLen = nLen + 3
        self.btReadId = btReadId
        self.btCmd = btCmd
        self.btAryData = bytearray(btAryData)
        
        self.btAryTranData = bytearray(nLen + 5)
        self.btAryTranData[0] = self.btPacketType
        self.btAryTranData[1] = self.btDataLen
        self.btAryTranData[2] = self.btReadId
        self.btAryTranData[3] = self.btCmd
        self.btAryTranData[4:nLen + 4] = self.btAryData
        
        self.btCheck = self.check_sum(self.btAryTranData, 0, nLen + 4)
        self.btAryTranData[nLen + 4] = self.btCheck

    def create_short_packet(self, btReadId: int, btCmd: int):
        """
        Crea un paquete de comunicación corto, sin carga útil de datos.

        Args:
            btReadId (int): ID de lectura.
            btCmd (int): Comando de la operación.
        """
        self.btPacketType = 0xA0
        self.btDataLen = 0x03
        self.btReadId = btReadId
        self.btCmd = btCmd
        
        self.btAryTranData = bytearray(5)
        self.btAryTranData[0] = self.btPacketType
        self.btAryTranData[1] = self.btDataLen
        self.btAryTranData[2] = self.btReadId
        self.btAryTranData[3] = self.btCmd
        
        self.btCheck = self.check_sum(self.btAryTranData, 0, 4)
        self.btAryTranData[4] = self.btCheck

    def parse_packet(self, btAryTranData: bytes):
        """
        Analiza un paquete de datos recibido y extrae sus componentes.

        Primero valida el checksum del paquete. Si es válido, extrae el
        tipo de paquete, longitud de datos, ID de lectura, comando y
        la carga útil de datos.

        Args:
            btAryTranData (bytes): La trama de datos completa recibida.
        """
        nLen = len(btAryTranData)
        
        self.btAryTranData = bytearray(btAryTranData)
        
        btCK = self.check_sum(self.btAryTranData, 0, nLen - 1)
        if btCK != self.btAryTranData[nLen - 1]:
            # El checksum es inválido, no se procesa el paquete.
            return
            
        self.btPacketType = self.btAryTranData[0]
        self.btDataLen = self.btAryTranData[1]
        self.btReadId = self.btAryTranData[2]
        self.btCmd = self.btAryTranData[3]
        self.btCheck = self.btAryTranData[nLen - 1]
        
        if nLen > 5:
            self.btAryData = bytearray(nLen - 5)
            for nloop in range(nLen - 5):
                self.btAryData[nloop] = self.btAryTranData[4 + nloop]

    def check_sum(self, btAryBuffer: bytearray, nStartPos: int, nLen: int) -> int:
        """
        Calcula el checksum de un buffer de datos.

        El método de cálculo del checksum es la suma de todos los bytes
        en un rango, invertida y sumada a uno (complemento a dos).

        Args:
            btAryBuffer (bytearray): El buffer de datos a chequear.
            nStartPos (int): La posición de inicio en el buffer.
            nLen (int): La longitud del segmento a chequear.

        Returns:
            int: El byte de checksum calculado.
        """
        btSum = 0x00
        for nloop in range(nStartPos, nStartPos + nLen):
            btSum += btAryBuffer[nloop]
        return ((~btSum) + 1) & 0xFF