from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QComboBox


class CheckboxBoard(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setObjectName("checkboxBoard")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        # TODO add checkboxes for: available, occupied, operational, type (gw, microservice, mid, heart, other, emda)

        self.checkbox_available = QCheckBox("Available")
        layout.addWidget(self.checkbox_available)

        self.checkbox_busy = QCheckBox("Busy")
        layout.addWidget(self.checkbox_busy)

        self.checkbox_operational = QCheckBox("Operational")
        layout.addWidget(self.checkbox_operational)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["All", "Microservice", "GW", "Mid", "Heart", "Emda", "Other"])
        layout.addWidget(self.combo_type)