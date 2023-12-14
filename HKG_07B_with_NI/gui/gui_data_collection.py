import os
from os.path import join as fullfile
import numpy as np
import time
from datetime import datetime
from array import array
from threading import Thread

from PySide6.QtGui import QFont
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QPushButton, QMessageBox, QSizePolicy, QGridLayout, QLabel
from pglive.sources.data_connector import DataConnector
from pglive.sources.live_plot import LiveLinePlot
from pglive.sources.live_plot_widget import LivePlotWidget
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import TerminalConfiguration

from widgets.form_label import FormLabel


TITLE = "Data Collection (%s - %s)"
PLOT_SECONDS   = 10
CONVERT_TO_BPM = 60
FFT_SIZE       = 40*1000
EXPERIMENTS = ['Heartbeat_Visualization', 'PPG_Collection']

class DataCollectionWindow(QMainWindow):
    def __init__(self, subject, args):
        super().__init__()

        self.subject = subject
        self.args    = args

        self.is_recording   = False
        self.is_collecting  = False
        self.daq_running    = 0
        self.f              = None
        self.ppg_buf        = np.zeros(FFT_SIZE)
        self.beg_Hz         = 0.8
        self.end_Hz         = 4
        self.fft_size       = FFT_SIZE
        self.incremental_hz = self.args.sample_rate / self.fft_size
        self.beg_idx        = int(self.beg_Hz // self.incremental_hz)
        self.end_idx        = int(self.end_Hz // self.incremental_hz)

        self.layout = self.create_views()

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        self.setWindowTitle(TITLE % (subject.name, subject.no))
        self.setMinimumWidth(600)
        self.setMinimumHeight(800)
        self.resize(480, 240)

    def create_views(self):
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        # Exp setting
        exp_layout = QVBoxLayout()
        exp_layout.setSpacing(8)
        exp_layout.addWidget(FormLabel("Experiment:"))
        self.cb_exp = QComboBox()
        self.cb_exp.addItems(EXPERIMENTS)
        font = self.cb_exp.font()
        font.setPointSize(16)
        self.cb_exp.setFont(font)
        exp_layout.addWidget(self.cb_exp)
        actions_layout.addItem(exp_layout)
        # Control button
        self.btn_control = QPushButton("Start")
        font = self.btn_control.font()
        font.setBold(True)
        font.setPointSize(16)
        self.btn_control.setFont(font)
        self.btn_control.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.btn_control.pressed.connect(self.click_start_stop)
        actions_layout.addWidget(self.btn_control)
        layout.addItem(actions_layout)

        # Live line charts
        charts_layout = QGridLayout()
        max_points    = self.args.sample_rate * PLOT_SECONDS
        self.update_rate   = 50
        # heart rate label
        heartbeat_label = QLabel('Heart rate: ')
        heartbeat_label.setFont((QFont('Arial', 16)))
        heartbeat_label.setStyleSheet('color: red')
        self.heartbeat_value = QLabel('')
        self.heartbeat_value.setFont((QFont('Arial', 16)))
        self.heartbeat_value.setStyleSheet('color: red')
        charts_layout.addWidget(heartbeat_label, 0, 0, 1, 1, alignment=Qt.AlignHCenter)
        charts_layout.addWidget(self.heartbeat_value, 0, 1, 1, 1, alignment=Qt.AlignHCenter)
        # ppg time-domain data
        plot_widget = LivePlotWidget(title="")
        self.style_plot_widget(plot_widget, title="PPG (Time domain)")
        self.ppg_curve_time = LiveLinePlot(pen={'color': "k", 'width': 3})
        plot_widget.addItem(self.ppg_curve_time)
        charts_layout.addWidget(plot_widget, 1, 0, 1, 4)
        self.ppg_connector_time = DataConnector(self.ppg_curve_time, max_points=max_points, update_rate=self.update_rate)
        # ppg freq-domain data
        plot_widget = LivePlotWidget(title="")
        self.style_plot_widget(plot_widget, title="PPG (Frequency domain)")
        self.ppg_curve_freq = LiveLinePlot(pen={'color': "k", 'width': 3})
        plot_widget.addItem(self.ppg_curve_freq)
        charts_layout.addWidget(plot_widget, 2, 0, 1, 4)
        self.ppg_connector_freq = DataConnector(self.ppg_curve_freq, max_points=self.end_idx-self.beg_idx, update_rate=self.update_rate)

        layout.addItem(charts_layout)

        return layout

    def style_plot_widget(self, plot_widget, title):
        plot_widget.getAxis('left').setTextPen('k')
        plot_widget.getAxis('bottom').setTextPen('k')
        plot_widget.setBackground((255, 255, 255, 0))
        title_label_item = plot_widget.getPlotItem().titleLabel.item
        title_label_item.setPlainText(title)
        font = title_label_item.font()
        font.setBold(True)
        font.setPointSize(14)
        plot_widget.getPlotItem().titleLabel.item.setFont(font)

    def click_start_stop(self):
        self.btn_control.setEnabled(False)

        if self.is_recording:
            self.btn_control.setText("Start")
            Thread(target=self.stop_recording).start()
        else:
            self.btn_control.setText("Stop")
            Thread(target=self.start_recording).start()

    def start_recording(self):
        exp = self.cb_exp.currentText()
        if not exp == EXPERIMENTS[0]:
            self.is_collecting = True
        
        if self.is_collecting:
            filename = fullfile(self.args.data_dir, '%s/%s/%s.dat' % (self.subject.no, exp, datetime.now().strftime("%m-%d-%Y-%H-%M-%S")))
            self.f = self.open_data_file(filename)
        Thread(target=self.open_daqmx).start()
        while self.daq_running == 0:
            time.sleep(0.1)
        self.cb_exp.setEnabled(False)
        self.btn_control.setEnabled(True)

    def stop_recording(self):
        self.is_recording = False
        while self.daq_running == 1:
            time.sleep(0.1)
        if self.is_collecting:
            self.is_collecting = False
            self.f.close()
        self.cb_exp.setEnabled(True)
        self.btn_control.setEnabled(True)

    def open_data_file(self, filename):
        folder_path = os.path.dirname(filename)
        if not os.path.exists(folder_path):
            try:
                os.makedirs(folder_path)
            except:
                pass

        return open(filename, 'wb')

    def update_fft(self, data):
        data = np.array(data)
        self.ppg_buf = np.concatenate((self.ppg_buf[data.shape[0]:], data), axis=None)
        self.ppg_spectrum_abs  = np.abs(np.fft.fft(self.ppg_buf, self.fft_size))
        # Pick the Peaks in the Heart Spectrum [1.6 - 4.0 Hz]
        max_heart_spectrum_idx = np.argmax(self.ppg_spectrum_abs[self.beg_idx: self.end_idx])
        self.heart_rate        = (max_heart_spectrum_idx + self.beg_idx) * self.incremental_hz * CONVERT_TO_BPM
        

    def open_daqmx(self):
        with nidaqmx.Task() as task:
            # for ch in self.args.channels:
                # task.ai_channels.add_ai_voltage_chan("%s/ai%d" % (nidaqmx.system.System.local().devices[0].name, ch)) #  , terminal_config=TerminalConfiguration.NRSE
                # task.ai_channels.add_ai_voltage_chan("%s/ai%d" % (nidaqmx.system.System.local().devices[0].name, ch) , terminal_config=TerminalConfiguration.NRSE) # 
            task.ai_channels.add_ai_voltage_chan("%s/ai%d" % (nidaqmx.system.System.local().devices[0].name, self.args.channels) , terminal_config=TerminalConfiguration.NRSE) # 

            task.timing.cfg_samp_clk_timing(self.args.sample_rate, sample_mode=AcquisitionType.CONTINUOUS)

            self.daq_running = 1
            self.ppg_connector_time.clear()
            self.ppg_connector_freq.clear()

            counter = 0
            self.is_recording = True
            while self.is_recording:
                num_per_channel = self.args.sample_rate // self.update_rate
                data = task.read(number_of_samples_per_channel=num_per_channel)
                self.update_fft(data)

                self.ppg_connector_time.cb_append_data_array(data, [counter + i for i in range(num_per_channel)])
                self.ppg_connector_freq.cb_append_data_array(self.ppg_spectrum_abs[self.beg_idx: self.end_idx], [i for i in range(self.beg_idx, self.end_idx)])
                self.heartbeat_value.setText(str(round(self.heart_rate, 2)))

                counter += num_per_channel
                if self.is_collecting:
                    array('d', [data]).tofile(self.f)
            self.daq_running = 0
            