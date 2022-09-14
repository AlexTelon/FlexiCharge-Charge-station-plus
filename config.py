class Configurations():
    _iPAddress = "ws://18.202.253.30:1337/"
    _chargerSerialNumber = "testnumber13"
    _protocol = "ocpp1.6"

    def getWebSocketAddress(self):
        return self._iPAddress + self._chargerSerialNumber

    def getProtocol(self):
        return self._protocol
