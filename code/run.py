from usr.tcp_server_simulation import Server
from usr.tcp_bridge_simulation import TcpBridge
from usr.control import Controller
from usr.collector import Collector
from usr.modules.remote import RemotePublish, RemoteSubscribe
from usr.modules.history import History
from usr.modbus_adapter import ModbusAdapter
from usr.channel.serial import Serial
from machine import UART
import base64
import utime


def Gateway():
    bridge = TcpBridge()
    history = History('/usr/485.hist', 20)

    # RemotePublish initialization
    remote_pub = RemotePublish()
    # Add History to RemotePublish for recording failure data
    remote_pub.addObserver(history)
    # Add bridge to RemotePublish for publishing data to server
    remote_pub.add_cloud(bridge)

    # Controller initialization
    controller = Controller()
    # Add RemotePublish to Controller for publishing data to server
    controller.add_module(remote_pub)

    # modbus adapter initialization
    modbus_adapter = ModbusAdapter()
    # serial channel initialization, ctrl_gpio used when connect to 485 device
    serial_channel_0 = Serial(uart=UART.UART2,
                              baudrate=9600,
                              databits=8,
                              parity=0,
                              stopbits=1,
                              flowctl=0,
                              ctrl_gpio=None)
    serial_channel_1 = Serial(uart=UART.UART1,
                              baudrate=9600,
                              databits=8,
                              parity=0,
                              stopbits=1,
                              flowctl=0,
                              ctrl_gpio=None)

    # spi_channel_3 = Spi()
    # modbus adapter add channel, so we can send data by choose specified channel
    modbus_adapter.add_channel(serial_channel_0)
    modbus_adapter.add_channel(serial_channel_1)
    # modbus_adapter.add_channel(spi_channel_3)

    # Collector initialization
    collector = Collector()
    # Add Controller to Collector for puting command to control device.
    collector.add_module(controller)
    # Add History to Collector for collect 485 sensor data.
    collector.add_module(modbus_adapter)
    # Add History to Collector for getting history data.
    collector.add_module(history)
    # modbus adapter add observer and update to indicate collector
    modbus_adapter.addObserver(collector)

    # RemoteSubscribe initialization
    remote_sub = RemoteSubscribe()
    # RemoteSubscribe add executor, when recv data will call executor
    remote_sub.add_executor(collector)
    # RemoteSubscribe add Observeror, Observeror can get bridge data
    bridge.addObserver(remote_sub)

    # bridge init, start connect to server
    bridge.init()


if __name__ == "__main__":
    server = Server()
    Gateway()

    '''Sending messages by non-passthrough
    message_id: Message ID
    nodeData: node Data content
        passthrough: passthrough
        channel:  Channel Number
        slave:   Slave Device Address
        function: function code
        start_address: Starting register address
        quantity: Read register quantity
        scan_rate: Automatic sampling frequency, multiples of 100, unit ms
    '''
    example_data1 = '{ ' \
                    '"message_id": 100,' \
                    '"nodeData": {' \
                    '"passthrough": 0,' \
                    '"channel": 0,' \
                    '"slave": 1,' \
                    '"function": 3,' \
                    '"startAddress": 2,' \
                    '"quantity": 3,' \
                    '"scan_rate": 10000' \
                    '}' \
                    '}'

    '''Sending messages by passthrough
    message_id: Message ID
    nodeData: node Data content
        passthrough: passthrough
        channel:  Channel Number
        data:   base64 encoded data
        scan_rate: Automatic sampling frequency, multiples of 100, unit ms
    '''
    base64_value = base64.encodebytes(b'\x01\x03\x00\x02\x00\x03\xa4\x0b')
    base64_value_str = base64_value.decode().strip('\n')
    example_data2 = "{\"message_id\": 101,\"nodeData\": {\"passthrough\": 1,\"channel\": 0,\"data\": \"" + \
                    base64_value_str + "\",\"scan_rate\": 0}}"

    # Read device holding register value
    server.send(example_data1)
    utime.sleep(1)
    server.send(example_data2)
