from qgis.core import *
from qgis.utils import *

from PyQt5.QtGui import *
from PyQt5.QtCore import QSize, QBuffer, QByteArray

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
        QgsMessageLog.logMessage('setting up RemoteRendering Task',
                                 MESSAGE_CATEGORY, Qgis.Info)

    # executes the main task (start listening and waiting for connections)
    def run(self):
        self.active = True
        QgsMessageLog.logMessage('starting to listen for messages',
                                 MESSAGE_CATEGORY, Qgis.Info)
        self.communicator.start()
        QgsMessageLog.logMessage('stop listening for messages',
                                 MESSAGE_CATEGORY, Qgis.Info)
        self.communicator.stop()
        self.active = False
        return True

    # reads request and acts accordingly
    def handle_rendering_request(self, request: dict) -> dict:

        QgsMessageLog.logMessage("received message: {}".format(request),
                                 MESSAGE_CATEGORY, Qgis.Info)

        # extract information from request
        target_name = request["target"]
        image_width = int(request["resolution"])
        coordinate_reference_system = request["crs"]
        extent = QgsRectangle(float(request["extent"]["min_x"]), float(request["extent"]["min_y"]),
                              float(request["extent"]["max_x"]), float(request["extent"]["max_y"]))

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
            "image": rendered_image
        }
        return answer

    # cancels the task
    def cancel(self):
        self.communicator.stop()
        super().cancel()
        self.active = False
        QgsMessageLog.logMessage('Task "{name}" was canceled'.format(name=self.description()),
                                 MESSAGE_CATEGORY, Qgis.Info)


# code mainly from https://github.com/opensourceoptions/pyqgis-tutorials/blob/master/015_render-map-layer.py
# renders the requested map extent and returns the image as string? TODO
def render_image(extent: QgsRectangle, crs: QgsCoordinateReferenceSystem, image_width: int):

    # create image
    ratio = extent.width() / extent.height()
    img = QImage(QSize(image_width, image_width / ratio), QImage.Format_ARGB32_Premultiplied)

    # set background color
    color = QColor(255, 255, 255, 0)
    img.fill(color.rgba())

    # create map settings
    ms = QgsMapSettings()
    ms.setBackgroundColor(color)

    # set layers to render
    layers = QgsProject.instance().layerTreeRoot().layerOrder()
    ms.setLayers(layers)
    # TODO: define layers via parameters

    # set extent & crs
    ms.setExtent(extent)
    ms.setDestinationCrs(crs)
    ms.setOutputSize(img.size())

    # render image
    qp = QPainter(img)
    render = QgsMapRendererCustomPainterJob(ms, qp)
    render.start()
    render.waitForFinished()
    qp.end()
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QBuffer.WriteOnly)
    img.save(buf, 'PNG')
    data = ba.data()

    return data
