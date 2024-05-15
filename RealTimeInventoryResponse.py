class RealTimeInventoryResponse:
    def __init__(self, btAryTranData):
        self.parse_packet(btAryTranData)

    def parse_packet(self, btAryTranData):
        self.btPacketType = btAryTranData[0]
        self.btDataLen = btAryTranData[1]
        self.btReadId = btAryTranData[2]
        self.btCmd = btAryTranData[3]

        # Obtener la longitud de la respuesta de cada etiqueta
        tag_response_len = len(btAryTranData) - 4  # Restar los bytes de encabezado y longitud

        # Inicializar listas vacías para almacenar los datos de las etiquetas
        self.freq_ant_list = []
        self.pc_list = []
        self.epc_list = []
        self.rssi_list = []

        # Iterar sobre los datos de las etiquetas en la respuesta
        for i in range(4, len(btAryTranData), tag_response_len):
            self.freq_ant_list.append(btAryTranData[i])
            self.pc_list.append(btAryTranData[i + 1 : i + 3])
            self.epc_list.append(btAryTranData[i + 3 : i + tag_response_len - 2])
            self.rssi_list.append(btAryTranData[i + tag_response_len - 1])
    
    def create_packet(self, btReadId, btCmd, btAryData):
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
        self.btAryData.copy_to(self.btAryTranData, 4)

        self.btCheck = self.check_sum(self.btAryTranData, 0, nLen + 4)
        self.btAryTranData[nLen + 4] = self.btCheck

    def create_short_packet(self, btReadId, btCmd):
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
