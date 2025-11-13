from PySide6.QtWidgets import QFileDialog
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QMessageBox

def upload_image(parent):
    file_path, _ = QFileDialog.getOpenFileName(parent, "Select Image", "", "Images (*.png *.jpg *.jpeg)")
    if file_path:
        img = QImage(file_path)
        pixmap = QPixmap.fromImage(img)
        parent.viewer.label.setPixmap(pixmap.scaledToWidth(
            parent.viewer.scroll_area.viewport().width(), Qt.SmoothTransformation
        ))


def save_file(parent):
    pixmap = parent.viewer.label.pixmap()
    if not pixmap:
        return
    path, _ = QFileDialog.getSaveFileName(parent, "Save Image", "", "Images (*.png *.jpg *.jpeg)")
    if path:
        ext = path.split(".")[-1].upper()
        pixmap.save(path, ext)