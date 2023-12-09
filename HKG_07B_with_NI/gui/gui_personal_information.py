from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QComboBox, QPushButton, QMessageBox
from PySide6.QtGui import QIntValidator

from widgets.form_label import FormLabel
from widgets.form_textedit import FormTextEdit

from util.subject_storage import Subject

TITLE = "Personal Information Entry"


class PersonalInformationWindow(QMainWindow):
    def __init__(self, subjects, current_subject, onConfirm=None):
        super().__init__()

        self.subjects = subjects
        self.current_subject = current_subject
        self.onConfirm = onConfirm

        self.layout = self.create_views()

        widget = QWidget()
        widget.setLayout(self.layout)
        self.setCentralWidget(widget)

        self.setWindowTitle(TITLE)
        self.setFixedSize(600, 500)

        if self.current_subject is not None:
            self.cb_no.setCurrentText(self.current_subject.no)
            self.te_name.setText(self.current_subject.name)
            self.cb_gender.setCurrentIndex(0 if self.current_subject.gender == 'Male' else 1)
            self.te_age.setText(str(self.current_subject.age))
            self.te_height.setText(str(self.current_subject.height))
            self.te_weight.setText(str(self.current_subject.weight))

    def create_views(self):
        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        # No. input
        no_layer = QVBoxLayout()
        no_layer.addWidget(FormLabel("No.:"))
        self.cb_no = QComboBox()
        self.cb_no.setEditable(True)
        font = self.cb_no.font()
        font.setPointSize(12)
        self.cb_no.setFont(font)
        self.cb_no.addItems([s.no for s in self.subjects])
        self.cb_no.currentIndexChanged.connect(self.switch_subject)
        no_layer.addWidget(self.cb_no)
        layout.addItem(no_layer)

        # Name input
        name_layer = QVBoxLayout()
        name_layer.addWidget(FormLabel("Name:"))
        self.te_name = FormTextEdit()
        name_layer.addWidget(self.te_name)
        layout.addItem(name_layer)

        # Gender
        gender_layer = QVBoxLayout()
        gender_layer.addWidget(FormLabel("Gender:"))
        self.cb_gender = QComboBox()
        self.cb_gender.addItems(["Male", "Female"])
        font = self.cb_gender.font()
        font.setPointSize(12)
        self.cb_gender.setFont(font)
        gender_layer.addWidget(self.cb_gender)
        layout.addItem(gender_layer)

        # Age input
        age_layer = QVBoxLayout()
        age_layer.addWidget(FormLabel("Age:"))
        self.te_age = FormTextEdit()
        self.te_age.setValidator(QIntValidator(10, 120))
        age_layer.addWidget(self.te_age)
        layout.addItem(age_layer)

        # Height input
        height_layer = QVBoxLayout()
        height_layer.addWidget(FormLabel("Height (cm):"))
        self.te_height = FormTextEdit()
        self.te_height.setValidator(QIntValidator(80, 200))
        height_layer.addWidget(self.te_height)
        layout.addItem(height_layer)

        # Weight input
        weight_layer = QVBoxLayout()
        weight_layer.addWidget(FormLabel("Weight (KG):"))
        self.te_weight = FormTextEdit()
        self.te_weight.setValidator(QIntValidator(30, 100))
        weight_layer.addWidget(self.te_weight)
        layout.addItem(weight_layer)

        # Button
        self.btn_confirm = QPushButton("Confirm")
        font = self.btn_confirm.font()
        font.setBold(True)
        font.setPointSize(16)
        self.btn_confirm.setFont(font)
        self.btn_confirm.setMinimumHeight(72)
        self.btn_confirm.pressed.connect(self.click_confirm)
        layout.addWidget(self.btn_confirm)

        return layout

    def switch_subject(self, index):
        no = self.cb_no.currentText()
        for s in self.subjects:
            if s.no == no:
                self.current_subject = s
                self.cb_no.setCurrentText(self.current_subject.no)
                self.te_name.setText(self.current_subject.name)
                self.cb_gender.setCurrentIndex(0 if self.current_subject.gender == 'Male' else 1)
                self.te_age.setText(str(self.current_subject.age))
                self.te_height.setText(str(self.current_subject.height))
                self.te_weight.setText(str(self.current_subject.weight))

    def click_confirm(self):
        no = str.strip(self.cb_no.currentText())
        if len(no) == 0:
            self.show_error("Subject No. can NOT be empty!")
            return

        name = str.strip(self.te_name.text())
        if len(name) == 0:
            self.show_error("Name can NOT be empty!")
            return

        gender = self.cb_gender.currentText()

        age = self.check_range(self.te_age, [10, 120], 'Age')
        if not age:
            return

        height = self.check_range(self.te_height, [80, 200], 'Height')
        if not height:
            return

        weight = self.check_range(self.te_weight, [30, 100], 'Height')
        if not weight:
            return

        if self.onConfirm is not None:
            self.onConfirm(Subject(no=no, name=name, gender=gender, age=age, height=height, weight=weight))

    def check_range(self, te, rg, fieldname):
        val_s = str.strip(te.text())
        if len(val_s) == 0:
            self.show_error("%s can NOT be empty!" % (fieldname))
            return False
        val = int(val_s)
        if val < rg[0] or val > rg[1]:
            self.show_error("Please chekc your %s!" % (fieldname))
            return False
        return val

    def show_error(self, msg):
        QMessageBox.critical(
            self,
            "Error",
            msg,
            QMessageBox.StandardButton.Ok,
            QMessageBox.StandardButton.Ok
        )

