# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RemoteRenderer
                                 A QGIS plugin
 Communicates with other programs via sockets and renders requested extents
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-08-19
        git sha              : $Format:%H$
        copyright            : (C) 2019-21 by BOKU ILEN, MR, CG
        email                : christoph.graf@boku.ac.at
 ***************************************************************************/
"""
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication

from .resources import *  # this is required

# Import the code for the dialog
from .RemoteRendering import RemoteRendering


# QGIS Plugin Implementation.
class RemoteRenderer:

    rendering_task: RemoteRendering = None

    def __init__(self, iface):

        # Save reference to the QGIS interface
        self.iface = iface

        # Declare instance attributes
        self.actions = []
        self.menu = u'&Remote Renderer'

    # adding plugin actions to QGIS
    def add_action(self, icon_path, text, callback, enabled_flag=True, add_to_menu=True,
                   add_to_toolbar=True, status_tip=None, whats_this=None, parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        self.actions.append(action)
        return action

    # Create the menu entries and toolbar icons inside the QGIS GUI
    def initGui(self):

        start_icon_path = ':/plugins/remote_renderer/icon.png'

        self.add_action(start_icon_path, text=u'Toggle Remote Rendering', callback=self.toggle_rendering,
                        parent=self.iface.mainWindow())

    # Removes the plugin menu item and icon from QGIS GUI.
    def unload(self):

        # cancel the task if it is still active
        if self.rendering_task and self.rendering_task.active:
            self.rendering_task.cancel()

        for action in self.actions:
            self.iface.removePluginMenu(u'&Remote Renderer', action)
            self.iface.removeToolBarIcon(action)

    # turns remote rendering task on / off
    def toggle_rendering(self):
        if self.rendering_task and self.rendering_task.active:
            self.rendering_task.cancel()
            return

        self.rendering_task = RemoteRendering()
        QgsApplication.taskManager().addTask(self.rendering_task)
