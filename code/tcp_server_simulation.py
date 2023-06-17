import usocket
import _thread
from usr.modules.logging import getLogger
from usr.global_config import TCP_SERVER_SIMULATION
from usr.global_config import TCP_SERVER_PORT_SIMULATION

log = getLogger(__name__)


class Server(object):
    def __init__(self):
        self.__sock = None
        self.__client = None
        self.status = None
        _thread.start_new_thread(self.server_listen, ())

    def client_msg_resolve(self, data):
        log.info('recv: ' + data.decode())

    def server_listen(self):
        self.status = 0
        self.__sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM, usocket.IPPROTO_TCP_SER)
        self.__sock.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
        self.__sock.bind((TCP_SERVER_SIMULATION, TCP_SERVER_PORT_SIMULATION))
        try:
            self.__sock.listen(0)
        except Exception as e:
            raise ValueError("[server] fail to listen on port %s" % e)

        self.__client = self.__sock.accept()[0]
        log.info('socket listen occurred')
        while True:
            self.status = 1
            try:
                data = self.__client.recv(1024)
            except Exception as e:
                log.warn("fail to listen on port %s" % e)
                self.status = 0
                self.__client = self.__sock.accept()[0]
            else:
                self.client_msg_resolve(data)

    def send(self, data):
        log.info('server send data: ' + str(data))
        self.__client.send(data)

    def close(self):
        self.__sock.close()
