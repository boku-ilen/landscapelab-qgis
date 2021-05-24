from json import JSONDecodeError

import json

import socket

import websockets
import asyncio
from websockets import WebSocketException

DEFAULT_PORT = 5005


# this class implements a websocket server within the QGIS plugin
# to listen to render requests and returns the rendered image
class Communicator:

    new_loop = None
    ws_server: websockets.WebSocketServer = None
    remote_renderer = None

    def __init__(self, remote_renderer):
        # generate a new dedicated event loop as this is run in
        # a separate thread        
        self.new_loop = asyncio.new_event_loop()
        self.remote_renderer = remote_renderer

    def start(self):

        # initialize websocket connection
        asyncio.set_event_loop(self.new_loop)
        # FIXME: make binding address configurable
        # FIXME: restarting the websockets server currently does not work
        ws_future = websockets.serve(self.on_request, socket.gethostname(), DEFAULT_PORT)

        # initialize server and run the event loop to listen for messages
        self.ws_server = self.new_loop.run_until_complete(ws_future)
        self.new_loop.run_forever()

    # this method is invoked on receiving a connection
    async def on_request(self, websocket, path):

        active = True
        while active:
            json_message = await websocket.recv()
            try:
                dict_message = json.loads(json_message)
                if dict_message["keyword"] == "quit":
                    active = False
                else:
                    # TODO: we might want to dispatch different requests in the future based on path
                    dict_answer = self.remote_renderer.handle_rendering_request(dict_message)
                    dict_answer["message_id"] = dict_message["message_id"]
                    dict_answer["success"] = True
                    await self.send(websocket, dict_answer)

            except JSONDecodeError as e:
                await self.send(websocket, {"success": False, "error": e.msg})

    async def send(self, websocket, dict_message: dict):
        try:
            json_message = json.dumps(dict_message)
            await websocket.send(json_message)
        except TypeError as e:
            self.remote_renderer.log("TypeError: {}".format(e))
        except ValueError as e:
            self.remote_renderer.log("ValueError: {}".format(e))
        except OverflowError as e:
            self.remote_renderer.log("OverflowError: {}".format(e))
        except WebSocketException as e:
            self.remote_renderer.log("WebSocketException: {}".format(e))

    # stopping the server
    def close(self):
        # FIXME: this does not seem to really close the websockets server
        self.new_loop.call_soon_threadsafe(self.ws_server.close)
        self.new_loop.call_soon_threadsafe(self.ws_server.wait_closed)

    def stop(self):
        self.new_loop.call_soon_threadsafe(self.new_loop.stop)
