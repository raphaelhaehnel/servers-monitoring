from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QCheckBox, QComboBox

from models.filterState import FilterState


class FilterControls(QHBoxLayout):
    filters_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Checkbox + Combo Layout
        self.checkbox_available = QCheckBox("Available")
        self.checkbox_busy = QCheckBox("Busy")
        self.checkbox_operational = QCheckBox("Operational")

        for cb in (self.checkbox_available, self.checkbox_busy, self.checkbox_operational):
            cb.toggled.connect(self._on_any_change)
            self.addWidget(cb)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["All", "MC", "GW", "Mid", "Heart", "Emda"])
        self.combo_type.setFixedWidth(150)
        self.combo_type.currentTextChanged.connect(self._on_any_change)
        self.addWidget(self.combo_type)

        self.combo_env = QComboBox()
        self.combo_env.addItems(["All", "preprod", "prod"])
        self.combo_env.setFixedWidth(150)
        self.combo_env.currentTextChanged.connect(self._on_any_change)
        self.addWidget(self.combo_env)

        self.addStretch()
        self.current_filters = None

    def _on_any_change(self, *_):
        print("Function _on_any_change called!!")
        """Gather all current controls’ states and emit them."""
        self.current_filters = FilterState(available=self.checkbox_available.isChecked(),
                                           busy=self.checkbox_busy.isChecked(),
                                           operational=self.checkbox_operational.isChecked(),
                                           type=self.combo_type.currentText(), env=self.combo_env.currentText())
        self.filters_changed.emit(self.current_filters)
