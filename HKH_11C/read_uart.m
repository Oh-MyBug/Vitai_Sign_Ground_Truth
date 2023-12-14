function ret = read_uart(data_port, num, type)
while ~data_port.NumBytesAvailable
end
ret = read(data_port, num, type);
end