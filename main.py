from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QLineEdit
)
from PySide6.QtCore import Qt

import sys

from stylesheet import style

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setObjectName("customTitleBar")

        #TODO the css is not applying on the customTitleBar
        #TODO add icons for close, minimize, settings like in Dorban

        #TODO add logs for each action that has been done
        #TODO add logged as viewer or admin
        #TODO add ip column
        #TODO perform multiple threading to get all servers at once (10 by 10)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        self.title = QLabel("FacIT")
        self.title.setObjectName("titleLabel")
        layout.addWidget(self.title)

        layout.addStretch()

        self.minimize_button = QPushButton("-")
        self.minimize_button.setFixedSize(20, 20)
        self.minimize_button.clicked.connect(self.minimize_window)
        layout.addWidget(self.minimize_button)

        self.close_button = QPushButton("x")
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self.close_window)
        layout.addWidget(self.close_button)

    def minimize_window(self):
        self.parent.showMinimized()

    def close_window(self):
        self.parent.close()

    def mousePressEvent(self, event: QMouseEvent):
        self.offset = event.globalPosition().toPoint() - self.parent.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.offset)


class ListItem(QWidget):
    def __init__(self, text1, text2, available, text3):
        super().__init__()
        self.text1 = text1
        self.text2 = text2
        self.available = available
        self.text3 = text3

        layout = QHBoxLayout()
        layout.setSpacing(10)

        label1 = QLabel(text1)
        label2 = QLabel(text2)
        available_text = QLabel(str(available) if available in [True, False] else "Unknown")
        button = QPushButton("Action")
        label3 = QLabel(text3)

        layout.addWidget(label1)
        layout.addWidget(label2)
        layout.addWidget(available_text)
        layout.addWidget(button)
        layout.addWidget(label3)

        self.setLayout(layout)

        # Tag for QSS styling
        if available is True:
            self.setObjectName("availableTrue")
        elif available is False:
            self.setObjectName("availableFalse")
        else:
            self.setObjectName("availableUnknown")

        # Apply object names to children for custom styles
        label1.setObjectName("lineLabel")
        label2.setObjectName("lineLabel")
        available_text.setObjectName("lineLabel")
        button.setObjectName("lineButton")
        label3.setObjectName("lineLabel")

    def matches(self, query):
        return (
                query.lower() in self.text1.lower() or
                query.lower() in self.text2.lower() or
                query.lower() in str(self.available).lower()
        )


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)

        # Main layout
        main_layout = QVBoxLayout(self)

        title_bar = CustomTitleBar(self)
        main_layout.addWidget(title_bar)
        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_items)
        main_layout.addWidget(self.search_bar)

        # Header row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        label_item = QLabel("Host")
        label_detail = QLabel("App")
        label_available = QLabel("Available")
        label_action = QLabel("Reservation")
        label_start_reservation = QLabel("Reservation start time")

        # Optional: bold font for headers
        bold_font = label_item.font()
        bold_font.setBold(True)
        for label in (label_item, label_detail, label_available, label_action, label_start_reservation):
            label.setFont(bold_font)

        header_layout.addWidget(label_item)
        header_layout.addWidget(label_detail)
        header_layout.addWidget(label_available)
        header_layout.addWidget(label_action)
        header_layout.addWidget(label_start_reservation)
        main_layout.addLayout(header_layout)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        # Container widget inside the scroll area
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(5)
        self.scroll_layout.setAlignment(Qt.AlignTop)

        # Populate items
        self.items = []
        for i in range(20):
            available = i % 2 == 0  # Alternate True/False
            item = ListItem(f"Item {i}", f"Detail {i}", available, "0")
            self.scroll_layout.addWidget(item)
            self.items.append(item)

        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

    def filter_items(self, text):
        for item in self.items:
            #TODO add match for the reservation user (not only item)
            match = item.matches(text)
            item.setVisible(match)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(style)
    window = MainWindow()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
