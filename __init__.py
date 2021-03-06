# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RemoteRenderer
                                 A QGIS plugin
 Communicates with other programs via websockets and renders requested extents
                             -------------------
        begin                : 2019-08-19
        copyright            : (C) 2019-2021 by BOKU ILEN, MR, CG
        email                : christoph.graf@boku.ac.at
        git sha              : $Format:%H$
 ***************************************************************************/

 This script initializes the plugin, making it known to QGIS.
"""


# Load RemoteRenderer class from file RemoteRenderer
def classFactory(iface):

    from .remote_renderer import RemoteRenderer
    return RemoteRenderer(iface)
