from qgis.core import *
from qgis.utils import *

from PyQt5.QtGui import *
from PyQt5.QtCore import QSize, QBuffer, QByteArray

from datetime import datetime

from .Communicator import Communicator

MESSAGE_CATEGORY = "LL Remote Rendering"


# this is the running task which controls the associated websockets server
# and renders the image which has to be sent back
class RemoteRendering(QgsTask):

    communicator: Communicator = None
    active: bool = False

    def __init__(self):
        super().__init__('remote control listener task', QgsTask.CanCancel)
        self.communicator = Communicator(self)
        QgsMessageLog.logMessage('setting up RemoteRendering Task', MESSAGE_CATEGORY, Qgis.Info)

    # executes the main task (start listening and waiting for connections)
    def run(self):
        self.active = True
        QgsMessageLog.logMessage('starting to listen for messages', MESSAGE_CATEGORY, Qgis.Info)
        self.communicator.start()
        QgsMessageLog.logMessage('stop listening for messages', MESSAGE_CATEGORY, Qgis.Info)
        self.communicator.stop()
        self.active = False
        return True

    # reads request and acts accordingly
    def handle_rendering_request(self, request: dict) -> dict:

        # extract information from request
        target_name = request["target"]
        image_width = int(request["resolution"])
        coordinate_reference_system = request["crs"]

        extent = QgsRectangle(float(request["extent"]["x_min"]), float(request["extent"]["y_min"]),
                              float(request["extent"]["x_max"]), float(request["extent"]["y_max"]))

        if not extent.isFinite():
            QgsMessageLog.logMessage("ERROR: Invalid Extent! Aborting rendering process.",
                                     MESSAGE_CATEGORY, Qgis.Critical)
            return {}

        # set coordinate system
        crs = QgsCoordinateReferenceSystem(coordinate_reference_system)
        if not crs.isValid():
            QgsMessageLog.logMessage("ERROR: Invalid CRS! Aborting rendering process.",
                                     MESSAGE_CATEGORY, Qgis.Critical)
            return {}

        # prepare response message
        rendered_image = render_image(extent, crs, image_width)
        answer = {
            "target": target_name,
            "extent": request["extent"],
            "image": rendered_image.decode("ascii")
        }
        return answer

    # cancels the task
    def cancel(self):
        self.communicator.stop()
        super().cancel()
        self.active = False
        QgsMessageLog.logMessage('Task "{name}" was canceled'.format(name=self.description()),
                                 MESSAGE_CATEGORY, Qgis.Info)

    def log(self, text):
        QgsMessageLog.logMessage('{}'.format(text), MESSAGE_CATEGORY, Qgis.Info)


# code mainly from https://github.com/opensourceoptions/pyqgis-tutorials/blob/master/015_render-map-layer.py
# renders the requested map extent and returns the image as BASE64 encoded PNG
def render_image(extent: QgsRectangle, crs: QgsCoordinateReferenceSystem, image_width: int):

    # create map settings
    ms = QgsMapSettings()

    color = QColor(255, 255, 255, 0)
    ms.setBackgroundColor(color)
    ms.setExtent(extent)
    ms.setDestinationCrs(crs)

    ratio = extent.width() / extent.height()
    size = QSize(image_width, image_width // ratio)    
    ms.setOutputSize(size)

    # set layers to render
    layers = QgsProject.instance().layerTreeRoot().layerOrder()
    ms.setLayers(layers)
    # TODO: define layers via parameters

    # render image
    render = QgsMapRendererParallelJob(ms)
    QgsMessageLog.logMessage('pre-render {}'.format(datetime.now()), MESSAGE_CATEGORY, Qgis.Info)
    render.start()
    render.waitForFinished()
    QgsMessageLog.logMessage('post-render {} ({})'.format(datetime.now(), render.renderingTime()), MESSAGE_CATEGORY, Qgis.Info)

    # store result in ByteArray
    img = render.renderedImage()
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QBuffer.WriteOnly)
    img.save(buf, 'PNG')
    # QgsMessageLog.logMessage('post-png {}'.format(datetime.now()), MESSAGE_CATEGORY, Qgis.Info)

    # encode as Base64 for network transport
    # TODO: we could try to change transfer method to BSON or MsgPack and directly transfer binary data
    base64 = ba.toBase64(QByteArray.Base64Encoding).data()
    return base64
