from PySide6.QtWidgets import QWidget, QLabel, QScrollArea, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage
import os

class ImageViewer(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.scroll_area = QScrollArea()
        self.container = QWidget()
        self.scroll_area.setWidget(self.container)
        self.scroll_area.setWidgetResizable(True)

        layout = QVBoxLayout(self.container)
        self.label = QLabel("No images to translate, please capture an image first")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)

        translate_btn = QPushButton("Translate")
        translate_btn.clicked.connect(self.parent.translate.translate_image)

        layout.addWidget(translate_btn)
        layout.addWidget(self.label)

    def show_image(self):
        if hasattr(self.parent.capture_widget, "capture") and self.parent.capture_widget.capture:
            path = f"capture{self.parent.capture_widget.capture.count}.png"
            if os.path.isfile(path):
                img = QImage(path)
                pixmap = QPixmap.fromImage(img)
                self.label.setPixmap(pixmap.scaledToWidth(self.scroll_area.viewport().width(), Qt.SmoothTransformation))
