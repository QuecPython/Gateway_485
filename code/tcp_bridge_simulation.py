from usr.modules.common import CloudObservable

# 导入usocket模块
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

        # 处理来自服务器的下行数据
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
        # 创建一个socket实例
        self.__sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        # 增加端口复用
        self.__sock.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
        # 解析域名
        addr = usocket.getaddrinfo(TCP_SERVER_SIMULATION, TCP_SERVER_PORT_SIMULATION)
        self.sockaddr = addr[0][-1]
        log.info('server connect ' + str(self.sockaddr))
        # 建立连接
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
