from PySide6.QtWidgets import QLabel

class FormLabel(QLabel):
    def __init__(self, *argv, **kargvs):
        super(FormLabel, self).__init__(*argv, **kargvs)

        font = self.font()
        font.setBold(True)
        font.setPointSize(16)
        self.setFont(font)
