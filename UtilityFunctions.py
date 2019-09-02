from PyQt5.QtGui import *
from PyQt5.QtCore import QSize, QRectF
from qgis.core import *
from .config import config

LAYOUT_NAME = "Remote Rendering Layout"


# code mainly from https://github.com/opensourceoptions/pyqgis-tutorials/blob/master/015_render-map-layer.py
def render_image(extent, crs_name, image_width, image_location, render_finish_callback):

    ratio = extent.width() / extent.height()

    # create image
    im_size = QSize(image_width, image_width / ratio)
    img = QImage(im_size, QImage.Format_ARGB32_Premultiplied)

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

    # setup layout
    project = QgsProject.instance()
    manager = project.layoutManager()
    layout_list = manager.printLayouts()

    # if layout with LAYOUT_NAME already exists remove it
    for layout in layout_list:
        if layout.name() == LAYOUT_NAME:
            manager.removeLayout(layout)
    layout = QgsPrintLayout(project)
    layout.initializeDefaults()
    layout.setName(LAYOUT_NAME)
    manager.addLayout(layout)

    map = QgsLayoutItemMap(layout)
    map.setRect(20, 20, 20, 20)

    # set map extent
    rect = QgsRectangle(extent)
    rect.scale(1.0)
    map.setExtent(rect)
    map.setBackgroundColor(QColor(255, 255, 255, 255))

    layout.addLayoutItem(map)
    map.attemptResize(QgsLayoutSize(image_width, image_width / ratio, QgsUnitTypes.LayoutPixels))
    layout.layoutBounds()

    exporter = QgsLayoutExporter(layout)
    image_settings = exporter.ImageExportSettings()
    image_settings.cropMargins = QgsMargins(0, 0, 0, 0)
    image_settings.cropToContent = True
    image_settings.imageSize = im_size
    image = exporter.renderRegionToImage(QRectF(0, 0, 100, 100), im_size)
    image.save(image_location)

    render_finish_callback()
