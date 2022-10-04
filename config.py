class Configurations():
    _iPAddress = "ws://18.202.253.30:1337/"
    _chargerSerialNumber = "testnumber13"
    _protocols = ['ocpp1.6']
    _pingInterval = 5 #Websocket ping interval in seconds.
    _timeout = None #Websocket timeout in seconds.

    def __init__(self):
        pass

    def getWebSocketAddress(self):
        return self._iPAddress + self._chargerSerialNumber

    def getProtocol(self):
        return self._protocols

    def getWebSocketPingInterval(self):
        return self._pingInterval

    def getWebSocketTimeout(self):
        return self._timeout