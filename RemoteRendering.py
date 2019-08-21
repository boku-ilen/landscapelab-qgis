# NOTE since this script is executed in the QGIS-Python environment
#  PyCharm might wrongfully mark some libraries/classes as unknown
import os
import socket
from qgis.core import *
from qgis.utils import *
from .UtilityFunctions import render_image
from .config import config
"""
NOTE: in order for this script to work, the QGIS plugin PowerPan has to be installed

To run this make sure that the path to this file is included in sys.path
then call 'import QGIS_POC1' in the QGIS pyton console
"""


class RemoteRendering(QgsTask):

    def __init__(self):
        super().__init__('remote control listener task', QgsTask.CanCancel)

        QgsMessageLog.logMessage('setting up RemoteRendering Task', config.MESSAGE_CATEGORY, Qgis.Info)

        # define image path
        self.image_location = config.output_path

        # setup UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((config.QGIS_IP, config.QGIS_READ_PORT))
        self.write_target = (config.QGIS_IP, config.LEGO_READ_PORT)
        self.active = False

    # listens on socket for commands and
    def run(self):
        self.active = True

        try:
            QgsMessageLog.logMessage('starting to listen for messages', config.MESSAGE_CATEGORY, Qgis.Info)
            while True:
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

                if data.startswith(config.RENDER_KEYWORD):
                    render_info = data[len(config.RENDER_KEYWORD):]
                    render_info = render_info.split(' ')
                    image_width = int(render_info[0])
                    crs = render_info[1]
                    extent_info = render_info[2:6]

                    extent = QgsRectangle(float(extent_info[0]), float(extent_info[1]), float(extent_info[2]), float(extent_info[3]))

                    render_image(extent, crs, image_width, self.image_location)
                    update_msg =  '{}{} {} {} {}'.format(config.UPDATE_KEYWORD, extent_info[0], extent_info[1], extent_info[2], extent_info[3])
                    self.socket.sendto(
                        update_msg.encode(),
                        self.write_target
                    )
                    QgsMessageLog.logMessage('sent: {}'.format(update_msg), config.MESSAGE_CATEGORY, Qgis.Info)

        finally:
            self.socket.close()
            self.active = False

    def cancel(self):
        RemoteRendering.stop_remote_rendering_task()
        QgsMessageLog.logMessage('Task "{name}" was canceled'.format(name=self.description()),
            config.MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()

    @staticmethod
    def start_remote_rendering_task():
        remote_render_task = RemoteRendering()
        QgsApplication.taskManager().addTask(remote_render_task)

        return remote_render_task

    @staticmethod
    def stop_remote_rendering_task():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(config.EXIT_KEYWORD.encode(), (config.QGIS_IP, config.QGIS_READ_PORT))
        finally:
            sock.close()
