from PySide6.QtWidgets import QLineEdit
from PySide6.QtGui import QFontMetrics

class FormTextEdit(QLineEdit):
    def __init__(self, *argv, **kargvs):
        super(FormTextEdit, self).__init__(*argv, **kargvs)

        font = self.font()
        font.setPointSize(12)
        self.setFont(font)
        self.setFixedHeight(QFontMetrics(font).lineSpacing() + 10)

