@echo off
call "E:\Program Files\QGIS 3.8\bin\o4w_env.bat"
call "E:\Program Files\QGIS 3.8\bin\qt5_env.bat"
call "E:\Program Files\QGIS 3.8\bin\py3_env.bat"

@echo on
pyrcc5 -o resources.py resources.qrc