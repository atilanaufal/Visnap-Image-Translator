import os
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from Func.translate_image import Translate
from Pages.Widgets.Capture.CaptureWidget import CaptureWidget
from Pages.Widgets.ToolBar.ToolBar import ToolBarMixin
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ViSnap - Translator")
        self.setMinimumSize(700, 360)
        self.windows = []
        self.capture_widget = CaptureWidget(self)
        self.translate = Translate(self)
        self.tool_bar = ToolBarMixin(self)
        self.setup_ui()

    def setup_ui(self):
        self.overlay = QStackedLayout()
        self.img_to_text = QLabel("NO TEXT")

        tool_bar = self.tool_bar.create_toolbar()
        self.addToolBar(tool_bar)

        translate_btn = QPushButton("Translate")
        translate_btn.clicked.connect(self.translate.translate_image)

        self.imgscroll = QScrollArea()
        container = QWidget()
        self.setCentralWidget(self.imgscroll)
        self.imgscroll.setWidget(container)
        self.imgscroll.setWidgetResizable(True)
        self.imgscroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.imgscroll.setViewportMargins(50, 0, 50, 0)
        self.imgscroll.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.imgscroll.setStyleSheet("background: rgba(0, 0, 0, 0);")

        row = QVBoxLayout(container)
        self.noimagetxt = QLabel("No images to translate, please capture an image first")
        self.noimagetxt.setAlignment(Qt.AlignCenter)
        self.noimagetxt.setWordWrap(True)

        row.addWidget(translate_btn)
        row.addWidget(self.noimagetxt)

        # File watcher agar update otomatis saat ada file baru
        self.watcher = QFileSystemWatcher(self)
        self.watcher.addPath(os.getcwd())
        self.watcher.fileChanged.connect(self.showimage)
        self.watcher.directoryChanged.connect(self.showimage)

    
    def showimage(self):
        """Tampilkan gambar hasil capture."""
        if hasattr(self.capture_widget, "capture") and self.capture_widget.capture:
            path = f"capture{self.capture_widget.capture.count}.png"
            if os.path.isfile(path):
                img = QImage(path)
                pixmap = QPixmap.fromImage(img)
                self.noimagetxt.setPixmap(pixmap.scaledToWidth(self.imgscroll.viewport().width(), Qt.SmoothTransformation))

  


