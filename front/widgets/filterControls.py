from PySide6.QtGui import QAction
from PySide6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QComboBox


class FilterControls(QHBoxLayout):

    def __init__(self, parent=None):
        super().__init__(parent)
        # Checkbox + Combo Layout
        self.checkbox_available = QCheckBox("Available")
        self.checkbox_busy = QCheckBox("Busy")
        self.checkbox_operational = QCheckBox("Operational")

        for cb in (self.checkbox_available, self.checkbox_busy, self.checkbox_operational):
            self.addWidget(cb)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["All", "Microservice", "GW", "Mid", "Heart", "Emda", "Other"])
        self.combo_type.setFixedWidth(150)
        self.addWidget(self.combo_type)
        self.addStretch()