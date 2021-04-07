from typing import Callable
from functools import partial
from qgis.core import *
from qgis.utils import *

from PyQt5.QtGui import *
from PyQt5.QtCore import QSize, QBuffer, QByteArray

from .Communicator import Communicator
from .config import config


# this is the running task which controls the associated websockets server
# and renders the image which has to be sent back
class RemoteRendering(QgsTask):

    communicator: Communicator = None
    active: bool = False

    def __init__(self):
        super().__init__('remote control listener task', QgsTask.CanCancel)
        self.communicator = Communicator()

        QgsMessageLog.logMessage('setting up RemoteRendering Task', config.MESSAGE_CATEGORY, Qgis.Info)

    # executes the main task (start listening and waiting for connections)
    def run(self):
        self.active = True
        QgsMessageLog.logMessage('starting to listen for messages', config.MESSAGE_CATEGORY, Qgis.Info)
        self.communicator.start()
        QgsMessageLog.logMessage('stop listening for messages', config.MESSAGE_CATEGORY, Qgis.Info)
        self.active = False
        return True

    # reads request and acts accordingly
    def handle_request(self, request):

        QgsMessageLog.logMessage("received message: {}".format(request),
                                 config.MESSAGE_CATEGORY, Qgis.Info)

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

            rendered_image = render_image(extent, coordinate_reference_system, image_width,
                self.image_location.format(target_name), render_finish_callback)

            self.send(rendered_image)

    # cancels the task
    def cancel(self):
        self.communicator.close()
        super().cancel()
        self.active = False
        QgsMessageLog.logMessage('Task "{name}" was canceled'.format(name=self.description()),
                                 config.MESSAGE_CATEGORY, Qgis.Info)


# code mainly from https://github.com/opensourceoptions/pyqgis-tutorials/blob/master/015_render-map-layer.py
# renders the requested map extent and finally calls render_finish_callback
def render_image(extent, crs_name, image_width, image_location, render_finish_callback):

    ratio = extent.width() / extent.height()

    # create image
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

    # set extent
    ms.setExtent(extent)

    crs = QgsCoordinateReferenceSystem(crs_name)
    if not crs.isValid():
        QgsMessageLog.logMessage(
            "ERROR: Invalid CRS! Aborting rendering process.", config.MESSAGE_CATEGORY, Qgis.Critical
        )
        return

    ms.setDestinationCrs(crs)
    # QApplication.processEvents()

    # set output size
    ms.setOutputSize(img.size())

    # render image
    # TODO: we also can render via QPainter to a serializable QRect
    qp = QPainter(img)
    render = QgsMapRendererCustomPainterJob(ms, qp)
    render.start()
    render.waitForFinished()
    # render_task = QgsMapRendererTask(ms, qp)
    # render_task = QgsMapRendererTask(ms, image_location, "PNG", False)
    # render_task.addDecorations() TODO: add scale, north arrow etc
    # render_task.taskCompleted.connect(render_finish_callback)
    # QgsApplication.taskManager().addTask(render_task)

    # FIXME: this would be the alternative?
    # this might go to render_finish_callback?
    qp.end()
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QBuffer.WriteOnly)
    img.save(buf, 'PNG')
    data = ba.data()
    return data
