# landscapelab-qgis

**This respository is not used anymore and may be defunct**. We developed it to obtain map renderings from QGIS in real-time for a separate visualization application. This worked, but it was fairly slow, not very stable, and limited. That's why we eventually switched to pre-processed MBTiles (using QGIS' "Generate XYZ Tiles" algorithm).

## Old README

a qgis plugin that allows remote controlled rendering and dynamic geodata-visualisation

Setup
-----------------

- clone this repository into `%APPDATA%/QGIS/<QGIS version>/profiles/<desired user profile>/python/plugins`
- open QGIS and select `Plugins > Manage and Install Plugins...`
- under Installed find and enable "Remote Renderer"

Usage
-----------------

You can toggle the remote rendering task via `Plugins > Remote Renderer > Toggle Remote Rendering` or with the dedicated button in the Plugins toolbar. If the task is active a blue progress bar will show up at the bottom of the screen.
