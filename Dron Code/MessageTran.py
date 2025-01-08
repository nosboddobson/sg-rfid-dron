class MessageTran:
    def __init__(self, btReadId=None, btCmd=None, btAryData=None, btAryTranData=None):
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
    def AryTranData(self):
        return self.btAryTranData

    @property
    def AryData(self):
        return self.btAryData

    @property
    def ReadId(self):
        return self.btReadId

    @property
    def Cmd(self):
        return self.btCmd

    @property
    def PacketType(self):
        return self.btPacketType

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
        self.btAryTranData[4:nLen+4] = btAryData 

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

    def parse_packet(self, btAryTranData):
        nLen = len(btAryTranData)

        self.btAryTranData = bytearray(btAryTranData)

        btCK = self.check_sum(self.btAryTranData, 0, nLen - 1)
        if btCK != self.btAryTranData[nLen - 1]:
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

    def check_sum(self, btAryBuffer, nStartPos, nLen):
        btSum = 0x00
        for nloop in range(nStartPos, nStartPos + nLen):
            btSum += btAryBuffer[nloop]
        return ((~btSum) + 1) & 0xFF
    
