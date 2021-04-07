import socket

import websockets
import asyncio
from qgis.core import QgsMessageLog, Qgis

from .config import config

DEFAULT_PORT = 5004


# this class implements a websocket server within the QGIS plugin
# to listen to render requests and returns the rendered image
class Communicator:

    new_loop = None
    ws_server: websockets.WebSocketServer = None

    def __init__(self):
        # generate a new dedicated event loop as this is run in
        # a separate thread        
        self.new_loop = asyncio.new_event_loop()

    def start(self):

        # initialize websocket connection
        # FIXME: make binding address configurable
        asyncio.set_event_loop(self.new_loop)
        ws_future = websockets.serve(self.on_request, socket.gethostname(), DEFAULT_PORT)

        # initialize server and run the event loop to listen for messages
        self.ws_server = self.new_loop.run_until_complete(ws_future)
        self.new_loop.run_forever()

    # this method is invoked on receiving a message
    async def on_request(self, websocket, path):

        name = await websocket.recv()
        await websocket.send(name)

    # stopping the server
    def close(self):
        self.ws_server.wait_closed()
        self.new_loop.call_soon_threadsafe(self.new_loop.stop)
