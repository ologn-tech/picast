import logging
import os


class PicastFileHandler(logging.FileHandler):

    def __init__(self):
        path = '/var/log/picast'
        fileName = 'picast.log'
        mode = 'a'
        super(PicastFileHandler, self).__init__(os.path.join(path, fileName), mode)