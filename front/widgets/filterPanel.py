from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QLineEdit, QVBoxLayout

from front.widgets.filterControls import FilterControls


class FilterPanel(QFrame):

    search_text_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("filterPanel")
        self.setFrameShape(QFrame.StyledPanel)
        filter_layout = QVBoxLayout(self)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(6)

        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.search_text_changed)
        self.search_bar.setStyleSheet("QLineEdit { padding: 5px; }")
        filter_layout.addWidget(self.search_bar)

        filter_controls = FilterControls()
        filter_layout.addLayout(filter_controls)