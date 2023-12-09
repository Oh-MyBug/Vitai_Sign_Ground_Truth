import os
from os.path import join as fullfile
import time
from datetime import datetime
from array import array
from threading import Thread

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QComboBox, QPushButton, QMessageBox, QSizePolicy
from pglive.sources.data_connector import DataConnector
from pglive.sources.live_plot import LiveLinePlot
from pglive.sources.live_plot_widget import LivePlotWidget
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.constants import TerminalConfiguration

from widgets.form_label import FormLabel

from util.iir_filter import IIRFilter
from util.movavg import MovingAverageFilter


TITLE = "Data Collection (%s - %s)"
PLOT_SECONDS = 2
EXPERIMENTS = ['Exp-Test', 'Exp1-1/Lying', 'Exp2-1/Lying_Walking', 'Exp2-2/Lying_FaceLeft', 'Exp2-2/Lying_FaceRight', 'Exp2-2/Lying_FaceDown', 'Exp2-3/Lying_Exercise', 'Exp1-1/Sitting', 'Exp2-1/Sitting_Walking', 'Exp2-3/Sitting_Exercise']


class DataCollectionWindow(QMainWindow):
    def __init__(self, subject, args):
        super().__init__()

        self.subject = subject
        self.args = args

        self.is_collecting = False
        self.daq_running = 0
        self.f = None

        self.bcg_filter = IIRFilter(4, [0.5, 20], fs=self.args.sample_rate, btype='bandpass')
        self.ecg_filter = MovingAverageFilter(int(args.sample_rate / 50))

        self.layout = self.create_views()

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        self.setWindowTitle(TITLE % (subject.name, subject.no))
        self.setMinimumWidth(600)
        self.setMinimumHeight(800)
        self.resize(1920, 960)

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
        charts_layout = QVBoxLayout()
        charts_layout.setSpacing(8)
        max_points = self.args.sample_rate * PLOT_SECONDS
        update_rate = 50
        # BCG
        plot_widget = LivePlotWidget(title="")
        self.style_plot_widget(plot_widget, title="BCG")
        self.bcg_curve = LiveLinePlot(pen={'color': "k", 'width': 3})
        plot_widget.addItem(self.bcg_curve)
        charts_layout.addWidget(plot_widget)
        self.bcg_connector = DataConnector(self.bcg_curve, max_points=max_points, update_rate=update_rate)
        # ECG
        plot_widget = LivePlotWidget(title="")
        self.style_plot_widget(plot_widget, title="ECG")
        self.ecg_curve = LiveLinePlot(pen={'color': "k", 'width': 3})
        plot_widget.addItem(self.ecg_curve)
        charts_layout.addWidget(plot_widget)
        self.ecg_connector = DataConnector(self.ecg_curve, max_points=max_points, update_rate=update_rate)
        # PPG
        plot_widget = LivePlotWidget(title="")
        self.style_plot_widget(plot_widget, title="PPG")
        self.ppg_curve = LiveLinePlot(pen={'color': "k", 'width': 3})
        plot_widget.addItem(self.ppg_curve)
        charts_layout.addWidget(plot_widget)
        self.ppg_connector = DataConnector(self.ppg_curve, max_points=max_points, update_rate=update_rate)

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

        if self.is_collecting:
            self.btn_control.setText("Start")
            Thread(target=self.stop_collecting).start()
        else:
            self.btn_control.setText("Stop")
            Thread(target=self.start_collecting).start()

    def start_collecting(self):
        self.bcg_filter.reset()
        self.ecg_filter.reset()

        exp = self.cb_exp.currentText()
        filename = fullfile(self.args.data_dir, '%s/%s/%s.dat' % (self.subject.no, exp, datetime.now().strftime("%m-%d-%Y-%H-%M-%S")))
        self.f = self.open_data_file(filename)
        Thread(target=self.open_daqmx).start()
        while self.daq_running == 0:
            time.sleep(0.1)
        self.cb_exp.setEnabled(False)
        self.btn_control.setEnabled(True)

    def stop_collecting(self):
        self.is_collecting = False
        while self.daq_running == 1:
            time.sleep(0.1)
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

    def open_daqmx(self):
        with nidaqmx.Task() as task:
            for ch in self.args.channels:
                # task.ai_channels.add_ai_voltage_chan("%s/ai%d" % (nidaqmx.system.System.local().devices[0].name, ch)) #  , terminal_config=TerminalConfiguration.NRSE
                task.ai_channels.add_ai_voltage_chan("%s/ai%d" % (nidaqmx.system.System.local().devices[0].name, ch) , terminal_config=TerminalConfiguration.NRSE) # 

            task.timing.cfg_samp_clk_timing(self.args.sample_rate, sample_mode=AcquisitionType.CONTINUOUS)

            # with open(self.args.out, 'wb') as f:
            self.daq_running = 1
            self.bcg_connector.clear()
            self.ecg_connector.clear()
            self.ppg_connector.clear()
            counter = 0
            self.is_collecting = True
            while self.is_collecting:
                num_per_channel = self.args.sample_rate // 50
                data = task.read(number_of_samples_per_channel=num_per_channel)
                self.bcg_connector.cb_append_data_array(self.bcg_filter.filter(data[0]), [counter + i for i in range(num_per_channel)])
                self.ecg_connector.cb_append_data_array(self.ecg_filter.filter(data[1]), [counter + i for i in range(num_per_channel)])
                self.ppg_connector.cb_append_data_array(data[2], [counter + i for i in range(num_per_channel)])
                counter += num_per_channel
                array('d', [data[ch][i] for i in range(num_per_channel) for ch in range(len(data))]).tofile(self.f)
            self.daq_running = 0

