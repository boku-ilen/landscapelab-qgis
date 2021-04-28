# setup UDP socket config


class config:
    QGIS_IP = "192.168.0.38"
    QGIS_READ_PORT = 5005
    TABLE_READ_PORT = 5006
    UDP_BUFFER_SIZE = 1024

    output_path = '/tmp/{}.png'

    RENDER_KEYWORD = 'render:'
    UPDATE_KEYWORD = 'update:'
    EXIT_KEYWORD = 'exit'

    MESSAGE_CATEGORY = "Remote Rendering Plugin"

    def __init__(self):
        pass
