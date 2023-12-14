% current folder: ./HKH_11C
clear, clc, close all;

%% 读取参数文件
func_param              = jsondecode(fileread('./breath.json'));
PORT                    = func_param.serial.port;    % 串口号
BAUDRATE                = func_param.serial.baudrate;    % 波特率
STORE_ENABLED           = func_param.store_file.enabled;
ROOT_PATH               = func_param.store_file.root_path;
NAME                    = func_param.store_file.name;
FILE_PATH               = [ROOT_PATH, '/', NAME];
save_count              = 0;
save_data.timestamps    = cell(10000, 1);
save_data.hkh           = zeros(10000, 1);
if ~exist(ROOT_PATH, 'dir')
    mkdir(ROOT_PATH); 
end

% 启动测量：
% 上位机 →→ 传感器：0xFF 0xCC 0x03 CKSUM 0xA0
% 上位机 ←← 传感器(应答)：0xFF 0xCC 0x05 CKSUM 0xA0 MBH MBL
% 说明：
%   MBH、MBL 分别表示呼吸波数据高低字节(波动幅值，相对量)。

% 停止采样：
% 上位机 →→ 传感器：0xFF 0xCC 0x03 CKSUM 0xA1
% 上位机 ←← 传感器(应答)：0xFF 0xCC 0x03 CKSUM 0xA1

% 调整脉搏幅度：
% 上位机 →→ 传感器：0xFF 0xCC 0x04 CKSUM 0xA4 FD
% 上位机 ←← 传感器(应答)：0xFF 0xCC 0x03 CKSUM 0xA4
% 说明：
%   FD 表示脉搏幅度级别，为 0-16 级或 0-10 级。
global HEADER_WORDS DEVICE_TYPE CMD
HEADER_WORDS = 0xFF;                                % 帧头标识：固定为数据帧起始位
DEVICE_TYPE  = 0xCC;                                % 设备类别：呼吸：HKH-11C
AMP          = 0x00;
FRAME_LEN    = struct("START", 0x03, "END", 0x03, "ADJUST_AMP", 0x04);	% 长度：包含长度、校验、命令、参数的字节数
CMD          = struct("START", 0xA0, "END", 0xA1, "ADJUST_AMP", 0xA4);  % 启动0xA0 停止0xA1
CKSUM        = struct("START", FRAME_LEN.START + CMD.START, "END", FRAME_LEN.END + CMD.END, ...
    "ADJUST_AMP", FRAME_LEN.ADJUST_AMP + CMD.ADJUST_AMP + AMP);  % 校验：长度、命令、参数求和

% 处理变量
SAMPLE_RATE         = 50;
PLOT_SEC            = 15;
PLOT_SIZE           = PLOT_SEC * SAMPLE_RATE;
FFT_SIZE            = 1024;
FREQ_INCREMENT_HZ   = SAMPLE_RATE / FFT_SIZE;
BREATH_FFT_BEG_HZ   = 0.1;                                                  % 呼吸FFT起始频率
BREATH_FFT_END_HZ   = 0.6;                                                  % 呼吸FFT结束频率
BREATH_FFT_BEG_IDX  = floor(BREATH_FFT_BEG_HZ / FREQ_INCREMENT_HZ) + 1;     % 呼吸FFT起始频率对应Bin索引
BREATH_FFT_END_IDX  = ceil(BREATH_FFT_END_HZ / FREQ_INCREMENT_HZ) + 1;      % 呼吸FFT结束频率对应Bin索引
HEART_FFT_BEG_HZ    = 0.8;                                                  % 心跳FFT起始频率
HEART_FFT_END_HZ    = 4;                                                    % 心跳FFT结束频率
HEART_FFT_BEG_IDX   = floor(HEART_FFT_BEG_HZ / FREQ_INCREMENT_HZ) + 1;      % 心跳FFT起始频率对应Bin索引
HEART_FFT_END_IDX   = ceil(HEART_FFT_END_HZ / FREQ_INCREMENT_HZ) + 1;       % 心跳FFT结束频率对应Bin索引
hkh                 = zeros(PLOT_SIZE, 1);
hkh_fft             = zeros(FFT_SIZE, 1);

% 连接串口
hkh_port = serialport(PORT, BAUDRATE);
configureTerminator(hkh_port, "CR");
% 启动测量
write(hkh_port, [HEADER_WORDS DEVICE_TYPE FRAME_LEN.ADJUST_AMP CKSUM.ADJUST_AMP CMD.ADJUST_AMP, AMP], "uint8");
read(hkh_port, 5, "uint8");
write(hkh_port, [HEADER_WORDS DEVICE_TYPE FRAME_LEN.START CKSUM.START CMD.START], "uint8");

% 画图
plot_num_row = 1;
plot_num_col = 2;
fig = figure('color', 'w', 'position', [150, 150, 400, 200]);
for p_i = 1: plot_num_row*plot_num_col
    ax(p_i) = subplot(plot_num_row, plot_num_col, p_i);
    hold(ax(p_i), 'on');
end
line_hkh     = plot(ax(1), 0, 0, '-k', 'linewidth', 1.5);
line_hkh_fft = plot(ax(2), 0, 0, '-k', 'linewidth', 1.5);
while isempty(get(gcf,'CurrentCharacter'))
    fprintf('NumBytesAvailable: %d\n', hkh_port.NumBytesAvailable);
    [data, ret] = uart_stream(hkh_port);
    if ~ret
        continue;
    end
    % 更新存储
    save_count                       = save_count + 1;
    save_data.timestamps{save_count} = datestr(datetime('now'), 'yyyy-mm-dd HH:MM:SS.FFF');
    save_data.hkh(save_count)        = data;
    
    hkh     = [hkh(2:end); data];
    hkh_fft = abs(fft(hkh, FFT_SIZE));
    
    % 更新图
    line_hkh.XData          = linspace(0, PLOT_SEC, PLOT_SIZE);
    line_hkh.YData          = hkh;
    line_hkh_fft.XData      = (BREATH_FFT_BEG_IDX-1:HEART_FFT_END_IDX-1) * FREQ_INCREMENT_HZ;
    line_hkh_fft.YData      = hkh_fft(BREATH_FFT_BEG_IDX:HEART_FFT_END_IDX);
    
    drawnow limitrate;
end
save_data.timestamps = save_data.timestamps(1:save_count);
save_data.hkh        = save_data.hkh(1: save_count);
save(FILE_PATH, 'save_data');
close all;