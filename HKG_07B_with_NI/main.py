import os
import sys
import argparse

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from gui.gui_personal_information import PersonalInformationWindow
from gui.gui_data_collection import DataCollectionWindow
from util import subject_storage

parser = argparse.ArgumentParser(description='')

# Exp config
parser.add_argument('--data_dir', default='rawdata', type=str)
parser.add_argument('--sample_rate', default=1000, type=int)
parser.add_argument('--device', default='Dev2', type=str)
parser.add_argument('--channels', default=4, type=int, nargs='+')

args = parser.parse_args()

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)


confirm = False

def main():
    app = QApplication(sys.argv)
    pi_win = PersonalInformationWindow(subject_storage.get_all(), subject_storage.get_current(), lambda subject: handle_confirm(pi_win, subject))
    pi_win.show()
    exit_code = app.exec()

    if confirm:
        dc_win = DataCollectionWindow(subject_storage.get_current(), args)
        dc_win.show()
        exit_code = app.exec()

    sys.exit(exit_code)


def handle_confirm(pi_win, subject):
    global confirm
    confirm = True

    # Handle current subject information
    subjects = subject_storage.get_all()
    exist = False
    for s in subjects:
        if s == subject:
            exist = True
            if s != subject:
                subject_storage.update(subject)
    if not exist:
        subject_storage.insert(subject)

    subject_storage.set_current_subject(subject)

    # Close window
    pi_win.close()


if __name__ == '__main__':
    main()

