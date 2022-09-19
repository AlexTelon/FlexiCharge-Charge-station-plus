from importlib.resources import is_resource
import websockets
import asyncio
from config import Configurations

class WebSocketReader():
    def __init__(self) -> None:
        self.reserved = False
        self.charging = False

    def is_reserved(self):
        return self.reserved 

    def is_charging(self):
        return self.charging