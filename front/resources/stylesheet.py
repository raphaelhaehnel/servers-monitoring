style = """
    QWidget {
        background-color: #282C34;
        color: #DDDDDD;
        font-family: 'Segoe UI', sans-serif;
        font-size: 14px;
    }

    QLineEdit {
        background-color: #3c3f41;
        color: #a9b7c6;
        border: 1px solid #555;
        border-radius: 4px;
        padding: 6px;
    }

    QPushButton {
        background-color: #4e5254;
        color: #ffffff;
        border: 1px solid #5c5c5c;
        border-radius: 4px;
        padding: 6px 12px;
    }

    QPushButton:hover {
        background-color: #64686a;
    }

    QPushButton:pressed {
        background-color: #737779;
    }

    QScrollArea {
        border: none;
    }

    QLabel {
        padding: 2px;
    }
    
    QFrame QLabel {
        background-color: #3c3f41;
    }

    QScrollBar:vertical {
        background: #3c3f41;
        width: 10px;
        margin: 0px;
        border-radius: 5px;
    }

    QScrollBar::handle:vertical {
        background: #5c5f61;
        min-height: 20px;
        border-radius: 5px;
    }

    QScrollBar::handle:vertical:hover {
        background: #787b7d;
    }

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {
        background: none;
    }

    QScrollBar:horizontal {
        background: #3c3f41;
        height: 10px;
        margin: 0px;
        border-radius: 5px;
    }

    QScrollBar::handle:horizontal {
        background: #5c5f61;
        min-width: 20px;
        border-radius: 5px;
    }

    QScrollBar::handle:horizontal:hover {
        background: #787b7d;
    }

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    QScrollBar::add-page:horizontal,
    QScrollBar::sub-page:horizontal {
        background: none;
    }
    
    /* === Row background === */
    QWidget#availableTrue {
        background-color: #2e4430; /* dark green */
    }
    
    QWidget#availableFalse {
        background-color: #442e2e; /* dark red */
    }
    
    /* === Label color === */
    QWidget#availableTrue QLabel#lineLabel {
        color: #b9f6ca;  /* mint green */
    }
    
    QWidget#availableFalse QLabel#lineLabel {
        color: #ffcdd2;  /* light red */
    }
    
    /* === Button style === */
    QWidget#availableTrue QPushButton#lineButton {
        background-color: #388e3c;
        color: white;
        border-radius: 4px;
    }
    
    QWidget#availableTrue QPushButton#lineButton:hover {
        background-color: #4caf50;
    }
    
    QWidget#availableFalse QPushButton#lineButton {
        background-color: #d32f2f;
        color: white;
        border-radius: 4px;
    }
    
    QWidget#availableFalse QPushButton#lineButton:hover {
        background-color: #f44336;
    }
    
    QWidget#customTitleBar {
        background-color: #21252B;
        color: white;
        border-bottom: 1px solid #34495e;
    }
    
    #cardFrame {
        background-color: #3c3f41;
        border-radius: 15px;
        padding: 1px;
        margin: 1px;
        border: 1px solid #555;
    }
    
    QWidget#customTitleBar QPushButton:disabled {
        background-color: #388e3c;
        padding: 1px;
    }
    
    #titleLabel {
        font-weight: bold;
    }
    
    #versionLabel, #copyrightName {
        background-color: #282C34;
        font-family: 'Segoe UI', sans-serif;
        font-size: 12px;
        color: #555555;
        background-color: #333740;
    }
    
    #footerFrame {
        border-top: 1px solid #5c5c5c;
        background-color: #333740;
    }
    
}
"""
