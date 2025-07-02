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
        background-color: #2e4430; /* dark green */ /*TODO this is not working*/
    }
    
    QWidget#availableFalse {
        background-color: #442e2e; /* dark red */ /*TODO this is not working*/
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
        font-family: 'Segoe UI', sans-serif;
        font-size: 12px;
        color: #a3a0a0;
        background-color: #333740;
    }
    
    #footerFrame {
        border-top: 1px solid #5c5c5c;
        background-color: #333740;
    }
    
    #lastUpdateTime {
        background-color: #282C34;
        border-radius: 8px;
        padding: 5px
    }
    
    #filterPanel {
        background-color: #282C34;
        border: 1px solid #3c3f41;
        border-radius: 6px;
    }
    
    QCheckBox {
        color: #DDDDDD;
        padding-right: 20px;
    }

    /* The round “box” */
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 6px;
        border: 1px solid #5c5f61;        /* match your scrollbar handle */
        background-color: #3c3f41;        /* same as your card bg */
    }
    
    /* Hover state */
    QCheckBox::indicator:hover {
        border-color: #787b7d;            /* match scrollbar-hover */
        background-color: #45494b;
    }
    
    /* Checked state */
    QCheckBox::indicator:checked, QCheckBox::indicator:checked:hover {
        background-color: #388e3c;        /* accent green */
        border: 1px solid #2e7d32;
    }
    
    QComboBox {
        background-color: #3c3f41;       /* same as list cards */
        color: #DDDDDD;                  /* light text */
        border: 1px solid #5c5f61;       /* match scrollbar handle */
        border-radius: 4px;
        padding: 4px 30px 4px 8px;       /* space for arrow */
        min-height: 24px;
    }
    
    /* Hover state */
    QComboBox:hover {
        border-color: #787b7d;
    }
    
    /* Focused / open state */
    QComboBox:focus {
        border-color: #888;              /* subtle highlight */
    }
    
    /* The drop-down arrow area */
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid #5c5f61;
        background-color: transparent;
    }
    
    /* The arrow itself */
    QComboBox::down-arrow {
        image: url(:icons/images/icons/cil-arrow-bottom.png);  /* replace with your icon path */
        width: 12px;
        height: 12px;
    }
    
    /* Popup list view */
    QComboBox QAbstractItemView {
        background-color: #3c3f41;
        border: 1px solid #5c5f61;
        selection-background-color: #5c5f61;
        selection-color: #FFFFFF;
        color: #DDDDDD;
        outline: none;
    }
    
    /* Items hover in list */
    QComboBox QAbstractItemView::item:hover {
        background-color: #45494b;
    }
    
    /* Disabled state */
    QComboBox:disabled {
        background-color: #2e2f31;
        color: #555555;
        border-color: #444444;
    }
    
    QTableWidget {
        background-color: #3c3f41;
        color: #DDDDDD;
        border: 1px solid #555;
        gridline-color: #5c5f61;
        selection-background-color: #5c5f61;
        selection-color: white;
        font-size: 13px;
        border-radius: 6px;
    }
    
    QTableView {
        gridline-color: transparent;
    }
    
    QHeaderView::section {
        background-color: #21252B;
        color: #DDDDDD;
        padding: 6px;
        border: 1px solid #5c5f61;
        font-weight: bold;
    }
    
    QTableWidget::item {
        padding: 6px;
    }
    
    QTableCornerButton::section {
        background-color: #21252B;
        border: 1px solid #5c5f61;
    }
}
"""
