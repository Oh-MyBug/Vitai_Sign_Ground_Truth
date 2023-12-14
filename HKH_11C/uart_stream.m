function [data, ret] = uart_stream(data_port)
global HEADER_WORDS DEVICE_TYPE CMD
data = [];
ret = 1;
if read_uart(data_port, 1, 'uint8') ~= HEADER_WORDS
    ret = 0;
    return;
end
if read_uart(data_port, 1, 'uint8') ~= DEVICE_TYPE
    ret = 0;
    return;
end
if read_uart(data_port, 1, 'uint8') ~= 0x05
    ret = 0;
    return;
end
read_uart(data_port, 1, 'uint8');
if read_uart(data_port, 1, 'uint8') ~= CMD.START
    ret = 0;
    return;
end
data = read_uart(data_port, 1, 'int16');
end