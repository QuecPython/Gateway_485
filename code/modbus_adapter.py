from usr.umodbus.rtu import RTU as ModbusRTUMaster
from usr.modules.common import Observable
import base64
import _thread
import utime
from usr.modules.logging import getLogger
import usr.global_config as config

log = getLogger(__name__)


class ModbusAdapter(Observable):
    def __init__(self):
        super().__init__()
        self.__channel = []
        self.__sample_service_pid = None
        self.__scan_slot = []
        self.host = ModbusRTUMaster(None)
        log.info('modbus adapter init success')

    def add_channel(self, module):
        self.__channel.append(module)
        return False

    def read_coils(self, data):
        # READ COILS slave_addr, coil_address, coil_qty
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['quantity']))
        coil_status = self.host.read_coils(data['slave'], data['startAddress'], data['quantity'])
        log.info('Status of coil coil_status: {}'.format(coil_status[data['quantity']]))
        self.data_report(data, coil_status[:data['quantity']])
        return config.RESPONSE_CODE_SUCCESS

    def write_single_coil(self, data):
        # WRITE COILS slave_addr, coil_address, new_coil_val
        log.info('slave_addr={}, hreg_address={}, value={}'.format(data['slave'], data['startAddress'], data['value']))
        operation_status = self.host.write_single_coil(data['slave'], data['startAddress'], data['value'])
        log.info('Result of setting coil operation_status: {}'.format(operation_status))
        if operation_status:
            return config.RESPONSE_CODE_SUCCESS
        return config.RESPONSE_CODE_OPRATION_ERROR

    def write_multiple_coils(self, data):
        # slave_addr, ireg_address, output_values
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['value']))
        operation_status = self.host.write_multiple_coils(data['slave'], data['startAddress'], data['value'])
        log.info('Status of ireg operation_status: {}'.format(operation_status))
        if operation_status:
            return config.RESPONSE_CODE_SUCCESS
        return config.RESPONSE_CODE_OPRATION_ERROR

    def read_hoding_registers(self, data):
        # READ HREGS slave_addr, hreg_address, register_qty
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['quantity']))
        register_value = self.host.read_holding_registers(data['slave'], data['startAddress'], data['quantity'], signed=False)
        log.info('Status of hreg value: {}'.format(register_value))
        self.data_report(data, register_value)
        return config.RESPONSE_CODE_SUCCESS

    def write_single_register(self, data):
        # WRITE HREGS slave_addr, hreg_address, new_hreg_val
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['value']))
        operation_status = self.host.write_single_register(data['slave'], data['startAddress'], data['value'], signed=False)
        log.info('Result of setting operation_status: {}'.format(operation_status))
        if operation_status:
            return config.RESPONSE_CODE_SUCCESS
        return config.RESPONSE_CODE_OPRATION_ERROR

    def write_multiple_registers(self, data):
        # slave_addr, ireg_address, register_values
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['value']))
        operation_status = self.host.write_multiple_registers(data['slave'], data['startAddress'], data['value'], signed=False)
        log.info('Status of ireg operation_status: {}'.format(operation_status))
        if operation_status:
            return config.RESPONSE_CODE_SUCCESS
        return config.RESPONSE_CODE_OPRATION_ERROR

    def read_discrete_inputs(self, data):
        # READ ISTS slave_addr, ist_address, input_qty
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['quantity']))
        input_status = self.host.read_discrete_inputs(data['slave'], data['startAddress'], data['quantity'])
        log.info('Status of ist input_status: {}'.format(input_status[:data['quantity']]))
        self.data_report(data, input_status[:data['quantity']])
        return config.RESPONSE_CODE_SUCCESS

    def read_input_registers(self, data):
        # READ IREGS slave_addr, ireg_address, register_qty
        log.info('slave_addr={}, hreg_address={}, register_qty={}'.format(data['slave'], data['startAddress'], data['quantity']))
        register_value = self.host.read_input_registers(data['slave'], data['startAddress'], data['quantity'], signed=False)
        log.info('Status of ireg register_value: {}'.format(register_value))
        self.data_report(data, register_value)
        return config.RESPONSE_CODE_SUCCESS

    def passthrough_data_transfer(self, data):
        self.host.update_channel(self.__channel[data['channel']])
        base64_value = data['data']
        value = base64.decodebytes(base64_value.encode())
        try:
            resp = self.host.passthrough_send_receive(value)
        except Exception as e:
            log.error("channel chat error %s" % e)
            return config.RESPONSE_CODE_CHANNEL_ERROR
        self.passthrough_data_report(data, resp)
        return config.RESPONSE_CODE_SUCCESS

    def data_report(self, data, value):
        response = "{\"report\":{\"slave\":" + str(data['slave']) \
                   + ",\"passthrough\": 0" \
                   + ",\"channel\":" + str(data['channel']) \
                   + ",\"startAddress\":" + str(data['startAddress']) \
                   + ",\"quantity\":" + str(data['quantity']) \
                   + ",\"value\":" + str(list(value)) + "}}"
        self.notifyObservers(self, *(response,))

    def passthrough_data_report(self, data, value):
        base64_value = base64.encodebytes(value)
        base64_value_str = base64_value.decode().strip('\n')
        response = "{\"report\":{" \
                   + "\"channel\":" + str(data['channel']) \
                   + ",\"passthrough\": 1" \
                   + ",\"value\":\"" + base64_value_str + "\"}}"
        self.notifyObservers(self, *(response,))

    def check_data(self, data):
        value = data['channel']
        if value is None or (0 > value > 3):
            return False
        value = data['slave']
        if value is None or (0 > value > 255):
            return False
        return True

    def parse_data(self, data):
        log.info('modbus node data: ' + str(data))
        passthrough = data['passthrough']
        if passthrough == 1:
            self.check_auto_sampling_status(data)
            return self.passthrough_data_transfer(data)

        if self.check_data(data) is False:
            return config.RESPONSE_CODE_PACKET_ERROR
        self.check_auto_sampling_status(data)
        function = data['function']
        func_arg = config.FUNCTION_TABLE[data['function']]
        if function is not None:
            func = getattr(self, func_arg)
            self.host.update_channel(self.__channel[data['channel']])
            try:
                response = func(data)
            except Exception as e:
                log.error("channel chat error %s" % e)
                return config.RESPONSE_CODE_CHANNEL_ERROR
            return response
        else:
            log.warn("RemoteSubscribe Has No Attribute [%s]." % func_arg)
        return config.RESPONSE_CODE_PACKET_ERROR

    def auto_sampling_add(self, data):
        # calcute loop cnt, slot loop 100ms
        cnt = data['scan_rate'] // 100
        print(cnt)
        data.pop('scan_rate')
        for tmp in self.__scan_slot:
            if tmp['data'] == data:
                if cnt != tmp['set']:
                    tmp['set'] = cnt
                return 0

        slot = {"set": cnt, "current": cnt, "data": data}
        self.__scan_slot.append(slot)
        log.info("add slot: \n" + str(slot))
        if self.__sample_service_pid is None:
            self.auto_sampling_start()
        return 0

    def auto_sampling_remove(self, data):
        data.pop('scan_rate')
        for slot in self.__scan_slot:
            if slot['data'] == data:
                self.__scan_slot.remove(slot)
                log.info("remove slot: \n" + str(slot))

    def check_auto_sampling_status(self, data):
        rate = data.get('scan_rate')
        if rate is not None:
            if rate == 0:
                self.auto_sampling_remove(data)
            else:
                self.auto_sampling_add(data)

    # The minimum time slice is 100ms, so only multiples of 100 are supported. Other values ​​will automatically fall into the nearest time slot.
    def auto_sampling_service(self):
        while True:
            for slot in self.__scan_slot:
                if slot['current'] == 0:
                    self.parse_data(slot['data'])
                    slot['current'] = slot['set']
                else:
                    slot['current'] -= 1
            utime.sleep_ms(100)

    def auto_sampling_start(self):
        self.__sample_service_pid = _thread.start_new_thread(self.auto_sampling_service, ())

    def auto_sampling_stop(self):
        _thread.stop_thread(self.__sample_service_pid)
        self.__sample_service_pid = None

