# NOTE since this script is executed in the QGIS-Python environment
#  PyCharm might wrongfully mark some libraries/classes as unknown
import os
import socket
from typing import Callable
from functools import partial
from qgis.core import *
from qgis.utils import *
from .UtilityFunctions import render_image
from .config import config


class RemoteRendering(QgsTask):

    def __init__(self, finished_request_callback: Callable):
        super().__init__('remote control listener task', QgsTask.CanCancel)

        QgsMessageLog.logMessage('setting up RemoteRendering Task', config.MESSAGE_CATEGORY, Qgis.Info)

        # define image path
        self.image_location = config.output_path

        # setup UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((config.QGIS_IP, config.QGIS_READ_PORT))
        self.write_target = (config.QGIS_IP, config.LEGO_READ_PORT)
        self.active = False
        self.last_request = None
        self.finished_request_callback = finished_request_callback

    # listens on socket for commands and
    def run(self):
        self.active = True

        try:
            QgsMessageLog.logMessage('starting to listen for messages', config.MESSAGE_CATEGORY, Qgis.Info)
            while True:

                try:
                    # wait for msg
                    data, addr = self.socket.recvfrom(config.UDP_BUFFER_SIZE)
                    data = data.decode()
                    QgsMessageLog.logMessage('got message {} from address {}'.format(data, addr),
                                             config.MESSAGE_CATEGORY, Qgis.Info)

                    # if msg is exit stop
                    if data == 'exit':
                        self.socket.sendto(config.EXIT_KEYWORD.encode(), self.write_target)
                        QgsMessageLog.logMessage('stop listening', config.MESSAGE_CATEGORY, Qgis.Info)
                        return True

                    self.handle_request(data)
                    self.last_request = data
                    self.finished_request_callback()

                except ConnectionResetError:
                    QgsMessageLog.logMessage('Connection was reset. Setting up new connection',
                                             config.MESSAGE_CATEGORY, Qgis.Warning)
                    self.socket.close()

                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.socket.bind((config.QGIS_IP, config.QGIS_READ_PORT))

        finally:
            self.socket.close()
            self.active = False
            self.finished_request_callback()

    # reads request and acts accordingly
    def handle_request(self, request):

        if request.startswith(config.RENDER_KEYWORD):
            # prepare request for information extraction
            render_info = request[len(config.RENDER_KEYWORD):]
            render_info = render_info.split(' ')

            # extract information from request
            target_name = render_info[0]
            image_width = int(render_info[1])
            coordinate_reference_system = render_info[2]
            extent_info = render_info[3:7]

            extent = QgsRectangle(
                float(extent_info[0]), float(extent_info[1]),
                float(extent_info[2]), float(extent_info[3])
            )

            # prepare response message
            update_msg = '{}{} {} {} {} {}'.format(
                config.UPDATE_KEYWORD, target_name,
                extent_info[0], extent_info[1], extent_info[2], extent_info[3]
            )

            # define callback function that should be called when rendering finished
            render_finish_callback = partial(self.send, update_msg)

            render_image(
                extent,
                coordinate_reference_system,
                image_width,
                self.image_location.format(target_name),
                render_finish_callback
            )

    # sends a given message to the lego client
    def send(self, msg):

        self.socket.sendto(msg.encode(), self.write_target)
        QgsMessageLog.logMessage('sent: {}'.format(msg), config.MESSAGE_CATEGORY, Qgis.Info)

    # cancels the task
    def cancel(self):
        RemoteRendering.stop_remote_rendering_task()
        QgsMessageLog.logMessage('Task "{name}" was canceled'.format(name=self.description()),
            config.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

    @staticmethod
    def start_remote_rendering_task(finished_request_callback: Callable):
        remote_render_task = RemoteRendering(finished_request_callback)
        QgsApplication.taskManager().addTask(remote_render_task)

        return remote_render_task

    @staticmethod
    def stop_remote_rendering_task():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(config.EXIT_KEYWORD.encode(), (config.QGIS_IP, config.QGIS_READ_PORT))
        finally:
            sock.close()
