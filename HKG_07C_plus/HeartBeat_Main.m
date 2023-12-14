% current folder: ./HKH_11C
clear, clc, close all;

%% 读取参数文件
func_param              = jsondecode(fileread('./heartbeat.json'));
STORE_ENABLED           = func_param.store_file.enabled;
ROOT_PATH               = func_param.store_file.root_path;
NAME                    = func_param.store_file.name;
FILE_PATH               = [ROOT_PATH, '/', NAME];
PORT                    = func_param.serial.port;         % 串口号
BAUDRATE                = func_param.serial.baudrate;     % 波特率

save_count              = 0;
save_data.timestamps    = cell(10000, 1);
save_data.hkg           = zeros(10000, 1);
if ~exist(ROOT_PATH, 'dir')
    mkdir(ROOT_PATH); 
end

%  采样频率：200Hz
%  波特率： 9600 bps
%  数据格式：8 位数据，1 位停止位，无奇偶校验
%  帧格式：帧头(1Byte) + 命令(1Byte) + 数据(1Byte)
%  通信命令：
% 1．读序列号: 20H 31H
% 2．开始采样：20H 32H
% 3．停止采样：20H 33H
% 4．设置放大倍数：20H 34H xx(放大倍数 0-9)
% 5．设置基线位置：20H 35H xx(基线位置 0-3)
% 6．设置采样频率：20H 37H xx(频率 0-3)
CMD = struct("START", 0x2032, "STOP", 0x2033);

% 处理变量
SAMPLE_RATE         = 200;
CONVERT_HZ_BPM      = 60;
PLOT_SEC            = 20;
PLOT_SIZE           = PLOT_SEC * SAMPLE_RATE;
FFT_SIZE            = 1024*5;
FREQ_INCREMENT_HZ   = SAMPLE_RATE / FFT_SIZE;
BREATH_FFT_BEG_HZ   = 0.1;                                                  % 呼吸FFT起始频率
BREATH_FFT_END_HZ   = 0.6;                                                  % 呼吸FFT结束频率
BREATH_FFT_BEG_IDX  = floor(BREATH_FFT_BEG_HZ / FREQ_INCREMENT_HZ) + 1;     % 呼吸FFT起始频率对应Bin索引
BREATH_FFT_END_IDX  = ceil(BREATH_FFT_END_HZ / FREQ_INCREMENT_HZ) + 1;      % 呼吸FFT结束频率对应Bin索引
HEART_FFT_BEG_HZ    = 0.8;                                                  % 心跳FFT起始频率
HEART_FFT_END_HZ    = 4;                                                    % 心跳FFT结束频率
HEART_FFT_BEG_IDX   = floor(HEART_FFT_BEG_HZ / FREQ_INCREMENT_HZ) + 1;      % 心跳FFT起始频率对应Bin索引
HEART_FFT_END_IDX   = ceil(HEART_FFT_END_HZ / FREQ_INCREMENT_HZ) + 1;       % 心跳FFT结束频率对应Bin索引
hkg                 = zeros(PLOT_SIZE, 1);
hkg_fft             = zeros(FFT_SIZE, 1);

% 连接串口
hkg_port = serialport(PORT, BAUDRATE);
configureTerminator(hkg_port, "CR");
% 启动测量
write(hkg_port, CMD.START, "uint8");

% 画图
plot_num = 1;
plot_num_row = 1;
plot_num_col = 2;
fig = figure('color', 'w', 'position', [150, 550, 400, 200]);
for p_i = 1: plot_num_row*plot_num_col
    ax(p_i) = subplot(plot_num_row, plot_num_col, p_i);
    hold(ax(p_i), 'on');
end
line_hkg     = plot(ax(1), 0, 0, '-k', 'linewidth', 1.5);
line_hkg_fft = plot(ax(2), 0, 0, '-k', 'linewidth', 1.5);
while isempty(get(gcf,'CurrentCharacter'))
    fprintf('NumBytesAvailable: %d\n', hkg_port.NumBytesAvailable);
    try
        data = read(hkg_port, 1, 'uint8');
    catch
        continue;
    end
    % 更新存储
    save_count                       = save_count + 1;
    save_data.timestamps{save_count} = datestr(datetime('now'), 'yyyy-mm-dd HH:MM:SS.FFF');
    save_data.hkg(save_count)        = data;
    
    hkg     = [hkg(2:end); data];
    hkg_fft = abs(fft(hkg, FFT_SIZE));
    
    [~, i]      = max(hkg_fft(HEART_FFT_BEG_IDX: HEART_FFT_END_IDX));
    heart_rate  = (i + HEART_FFT_BEG_IDX - 2) * CONVERT_HZ_BPM * FREQ_INCREMENT_HZ;
    
    plot_num = plot_num + 1;
    if mod(plot_num, 5)
        continue;
    end
    % 更新图
    line_hkg.XData          = linspace(0, PLOT_SEC, PLOT_SIZE);
    line_hkg.YData          = hkg;
    line_hkg_fft.XData      = (HEART_FFT_BEG_IDX-1:HEART_FFT_END_IDX-1) * FREQ_INCREMENT_HZ;
    line_hkg_fft.YData      = hkg_fft(HEART_FFT_BEG_IDX:HEART_FFT_END_IDX);
    title(ax(2), sprintf("Heart Rate: %.2fBPM", heart_rate))
    
    drawnow limitrate;
end
save_data.timestamps = save_data.timestamps(1:save_count);
save_data.hkg        = save_data.hkg(1: save_count);
save(FILE_PATH, 'save_data');
close all;