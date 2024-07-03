from usr.modules.common import CloudObservable

import usocket
import utime
import _thread
from usr.modules.logging import getLogger
from usr.global_config import TCP_SERVER_SIMULATION
from usr.global_config import TCP_SERVER_PORT_SIMULATION

log = getLogger(__name__)


class TcpBridge(CloudObservable):
    def __init__(self):
        super().__init__()
        self.__sock = None
        self.status = None
        self.sockaddr = None

    # Processing downlink data from the server
    def __server_msg_resolve(self, data):
        log.info('recv: ' + data.decode())
        self.notifyObservers(self, *("query", {data}))

    def __server_msg_thread(self):
        while True:
            try:
                data = self.__sock.recv(1024)
            except Exception as e:
                log.warn("fail to listen on port %s" % e)
                self.server_reconnect()
            else:
                self.__server_msg_resolve(data)

    def __async_wait(self):
        _thread.start_new_thread(self.__server_msg_thread, ())

    def server_reconnect(self):
        self.__sock.close()
        self.update_connect_status(False)
        while True:
            try:
                self.__sock.connect(self.sockaddr)
                self.update_connect_status(True)
                break
            except Exception as e:
                log.warn("server reconnect failed %s" % e)
            utime.sleep(1)

    def update_connect_status(self, stat):
        self.status = stat
        if self.status:
            self.notifyObservers(self, *("raw_data", {"status": 'online'}))

    def init(self, enforce=False):
        """Cloud init"""
        if self.get_status():
            return True
        # Create a socket instance
        self.__sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        # Increase port reuse
        self.__sock.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
        # DNS domain resolve
        addr = usocket.getaddrinfo(TCP_SERVER_SIMULATION, TCP_SERVER_PORT_SIMULATION)
        self.sockaddr = addr[0][-1]
        log.info('server connect ' + str(self.sockaddr))
        # establish connection
        self.__sock.connect(self.sockaddr)
        self.__async_wait()
        self.update_connect_status(True)

    def close(self):
        """Cloud disconnect"""
        self.__sock.close()

    def post_data(self, data):
        """Cloud publish data"""
        ret = self.__sock.send(data)
        log.info('send %d bytes to server success' % ret)
        return True

    def get_status(self):
        return self.status
