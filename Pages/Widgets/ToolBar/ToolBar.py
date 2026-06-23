from PySide6.QtWidgets import QToolBar, QComboBox, QWidget, QHBoxLayout, QSizePolicy, QSpacerItem, QInputDialog
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QSize
from Func.Tool_Func import upload_image, save_file, load_image_from_link
import os


class ToolBarMixin:
    def __init__(self, parent):
        self.parent = parent

    def create_toolbar(self):
        tool_bar = QToolBar("Toolbar", self.parent)
        tool_bar.setIconSize(QSize(35, 35))
        tool_bar.setMovable(False)
        base_dir = getattr(self.parent, "base_dir", os.getcwd())

        # Helper function buat tambah tombol biar singkat
        def add_action(icon, text, callback):
            icon_path = os.path.join(base_dir, "Assets", "Icons", f"{icon}.svg")
            action = tool_bar.addAction(QIcon(icon_path), text)
            action.triggered.connect(callback)
            tool_bar.addSeparator()
            return action

        # Tambahkan semua tombol
        add_action("capture", "Capture", self.parent.capture_widget.open_overlay )
        def open_link_dialog():
            link, ok = QInputDialog.getText(self.parent, "Insert Image Link", "Link")
            if ok:
                load_image_from_link(self.parent, link)

        add_action("link", "Link", open_link_dialog)
        add_action("upload2", "Upload", lambda: upload_image(self.parent))
        
        # Dropdown bahasa
        for langs in (["English", "Japanese", "Indonesia", "Chinese"],) * 2:
            combo = QComboBox()
            combo.addItems(langs)
            tool_bar.addWidget(combo)

        # Spacer agar tombol Save di kanan
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tool_bar.addWidget(spacer)

        add_action("save", "Save", lambda: save_file(self.parent))

        return tool_bar
