

TCP_SERVER_SIMULATION = '127.0.0.1'
TCP_SERVER_PORT_SIMULATION = 10005


RESPONSE_CODE_SUCCESS = 0
RESPONSE_CODE_PACKET_ERROR = 1
RESPONSE_CODE_CHANNEL_ERROR = 2
RESPONSE_CODE_OPRATION_ERROR = 3

RESPONSE_CODE_TABLE = {
    RESPONSE_CODE_SUCCESS: 'success',
    RESPONSE_CODE_PACKET_ERROR: 'down packet erorr',
    RESPONSE_CODE_CHANNEL_ERROR: 'channel chat error',
    RESPONSE_CODE_OPRATION_ERROR: 'illegal operation error'
}

# function codes
READ_COILS = 0x01                   # COILS, [0, 1]
READ_DISCRETE_INPUTS = 0x02         # ISTS,  [0, 1]
READ_HOLDING_REGISTERS = 0x03       # HREGS, [0, 65535]
READ_INPUT_REGISTER = 0x04          # IREGS, [0, 65535]

WRITE_SINGLE_COIL = 0x05            # COILS, [0, 1]
WRITE_SINGLE_REGISTER = 0x06        # HREGS, [0, 65535]
WRITE_MULTIPLE_COILS = 0x0F         # COILS, [0, 1]
WRITE_MULTIPLE_REGISTERS = 0x10     # HREGS, [0, 65535]

FUNCTION_TABLE = {
    READ_COILS: 'read_coils',
    READ_DISCRETE_INPUTS: 'read_discrete_inputs',
    READ_HOLDING_REGISTERS: 'read_hoding_registers',
    READ_INPUT_REGISTER: 'read_input_registers',
    WRITE_SINGLE_COIL: 'write_single_coil',
    WRITE_SINGLE_REGISTER: 'write_single_register',
    WRITE_MULTIPLE_COILS: 'write_multiple_coils',
    WRITE_MULTIPLE_REGISTERS: 'write_multiple_registers'
}
