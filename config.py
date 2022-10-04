class Configurations():

    def __init__(self):
        self._mockServerIP = 'ws://127.0.0.1:60003'
        self._iPAddress = "ws://18.202.253.30:1337/"
        self._chargerSerialNumber = "testnumber13"
        self._protocols = ['ocpp1.6']
        self._pingInterval = 5 #Websocket ping interval in seconds.
        self._timeout = None #Websocket timeout in seconds.

    def getMockServerAddress(self):
        return self._mockServerIP

    def getWebSocketAddress(self):
        return self._iPAddress + self._chargerSerialNumber

    def getProtocol(self):
        return self._protocols

    def getWebSocketPingInterval(self):
        return self._pingInterval

    def getWebSocketTimeout(self):
        return self._timeout