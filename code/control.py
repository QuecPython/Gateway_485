from usr.modules.remote import RemotePublish
from usr.modules.common import Singleton
from usr.modules.logging import getLogger

log = getLogger(__name__)


class Controller(Singleton):
    def __init__(self):
        self.__remote_pub = None
        log.info('control init success')

    def add_module(self, module, led_type=None, callback=None):
        if isinstance(module, RemotePublish):
            self.__remote_pub = module
            log.info('remote pub add')
            return True
        return False

    def remote_post_data(self, msg):
        self.__remote_pub.post_data(str(msg))

    def parse_data(self, data):
        log.info(data)

