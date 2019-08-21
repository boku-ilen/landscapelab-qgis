from PyQt5.QtGui import *
from PyQt5.QtCore import QSize
from qgis.core import *
from .config import config


# code mainly from https://github.com/opensourceoptions/pyqgis-tutorials/blob/master/015_render-map-layer.py
def render_image(extent, crs_name, image_width, image_location):

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
        QgsMessageLog.logMessage("ERROR: Invalid CRS! Aborting rendering process.", config.MESSAGE_CATEGORY, Qgis.Critical)
        return

    ms.setDestinationCrs(crs)
    # QApplication.processEvents()

    # set output size
    ms.setOutputSize(img.size())

    # setup qgis map renderer
    render = QgsMapRendererParallelJob(ms)
    render.start()
    render.waitForFinished()
    img = render.renderedImage()

    # save the image
    img.save(image_location)