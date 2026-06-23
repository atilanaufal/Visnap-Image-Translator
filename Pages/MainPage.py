import os
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from Func.translate_image import Translate
from Pages.Widgets.Capture.CaptureWidget import CaptureWidget
from Pages.Widgets.ToolBar.ToolBar import ToolBarMixin
from Pages.Widgets.ImageViewer import ImageViewer  # ✅ tambahkan import ini


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ViSnap - Translator")
        self.setMinimumSize(700, 360)
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.capture_dir = os.path.join(self.base_dir, "captures")
        self.current_image_path = None
        os.makedirs(self.capture_dir, exist_ok=True)

        # === inisialisasi komponen utama ===
        self.windows = []
        self.capture_widget = CaptureWidget(self)
        self.translate = Translate(self)
        self.tool_bar = ToolBarMixin(self)
        self.viewer = ImageViewer(self)   # ✅ gunakan ImageViewer sebagai tampilan utama

        self.setup_ui()

    def setup_ui(self):
        # Toolbar
        self.addToolBar(self.tool_bar.create_toolbar())

        # Jadikan viewer sebagai central widget
        self.setCentralWidget(self.viewer.scroll_area)

        # File watcher — update otomatis bila ada file baru
        self.watcher = QFileSystemWatcher(self)
        self.watcher.addPath(self.capture_dir)
        self.watcher.directoryChanged.connect(self.viewer.show_image)  # ✅ gunakan viewer
