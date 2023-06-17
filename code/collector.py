from usr.control import Controller
from usr.modbus_adapter import ModbusAdapter
from usr.modules.common import Singleton
import _thread
from queue import Queue
from usr.modules.logging import getLogger
from usr.modules.history import History
import usr.global_config as config
import modem

log = getLogger(__name__)


class Collector(Singleton):
    def __init__(self):
        self.__history = None
        self.__controller = None
        self.__modbus_adapter = None
        self.queue = Queue()
        _thread.start_new_thread(self.get_data, ())

    def add_module(self, module, led_type=None, callback=None):
        if isinstance(module, Controller):
            self.__controller = module
            return True
        elif isinstance(module, ModbusAdapter):
            self.__modbus_adapter = module
            return True
        elif isinstance(module, History):
            self.__history = module
            return True
        return False

    # 处理来自上层的下行数据
    def modbus_adapter_msg_resolve(self, param):
        if not self.__modbus_adapter:
            raise TypeError("self.__controller is not registered.")
        modbus_data = param
        log.info(modbus_data)
        message_id = modbus_data['message_id']
        if message_id is not None:
            self.__modbus_adapter.put_data(modbus_data)

    # Do cloud event downlink option by controller
    def event_option(self, *args, **kwargs):
        if kwargs['status'] == 'online':
            self.device_data_report()


    def event_done(self, *args, **kwargs):
        """Hanle setting object model downlink message from cloud."""
        pass

    def event_query(self, *args, **kwargs):
        """Hanle quering object model downlink message from cloud."""
        data = eval(args[0])
        self.put_data(data)

    def event_ota_plain(self, *args, **kwargs):
        """Hanle OTA plain from cloud."""
        pass

    def event_ota_file_download(self, *args, **kwargs):
        """ OAT MQTT File Download Is Not Supported Yet."""
        pass

    def rrpc_request(self, *args, **kwargs):
        """Hanle RRPC request"""
        pass

    def update(self, observable, *args, **kwargs):
        """Observer update option"""
        log.info('start update')
        if isinstance(observable, ModbusAdapter):
            log.info('data send: ' + str(args[1]))
            self.__controller.remote_post_data(args[1])

    def put_data(self, data):
        # log.info('PUSH: ' + str(data))
        self.queue.put(data)

    def get_data(self):
        while True:
            # 阻塞获取
            data = self.queue.get()
            # log.info('POP: ' + str(data))
            if data['nodeData'] is not None:
                # ack without value
                response = self.__modbus_adapter.parse_data(data['nodeData'])

                # ack with report value
                # response, value = self.__modbus_adapter.parse_data(data)
            else:
                response = self.__controller.parse_data(data)
            message_id = data['message_id']
            ack = "{\"message_id\":" + str(message_id) + ",\"response\":" + str(response) + ",\"desc\": \"" + \
                  config.RESPONSE_CODE_TABLE[response] + "\"}"
            log.info('send request ack: ' + str(ack))
            self.__controller.remote_post_data(ack)

    def get_dev_imei(self):
        return modem.getDevImei()

    def report_history(self):
        log.debug('---------------history report check----------------')
        """Publish history data to cloud."""
        if not self.__history:
            log.warn("self.__history is not registered.")
            return False
        if not self.__controller:
            log.warn("self.__controller is not registered.")
            return False

        res = True
        hist = self.__history.read()
        if hist["data"]:
            pt_count = 0
            for i, data in enumerate(hist["data"]):
                pt_count += 1
                if not self.__controller.remote_post_data(data):
                    res = False
                    break

            hist["data"] = hist["data"][pt_count:]
            if hist["data"]:
                # Flush data in hist-dictionary to tracker_data.hist file.
                self.__history.write(hist["data"])

        return res

    def device_data_report(self, power_switch=True, event_data={}, msg=""):
        """Publish data to cloud from controller"""
        # TODO: msg to mark post data source
        if not self.__controller:
            log.warn("self.__controller is not registered.")

        self.report_history()
        imei = self.get_dev_imei()
        report = "{\"report\":{\"imei\": \"" + str(imei) + "\"}}"
        log.debug('report device base info: ' + report)
        self.__controller.remote_post_data(report)


