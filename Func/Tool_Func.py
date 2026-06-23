from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QImage, QPixmap
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
import os
import tempfile

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg)"
FORMAT_BY_EXT = {
    ".png": "PNG",
    ".jpg": "JPG",
    ".jpeg": "JPG",
}

def upload_image(parent):
    file_path, _ = QFileDialog.getOpenFileName(parent, "Select Image", "", IMAGE_FILTER)
    if file_path:
        if not parent.viewer.set_image_path(file_path):
            QMessageBox.warning(parent, "Upload Failed", "File gambar tidak bisa dibuka.")


def load_image_from_link(parent, link):
    link = link.strip()
    if not link:
        return

    try:
        request = Request(link, headers={"User-Agent": "ViSnap/1.0"})
        with urlopen(request, timeout=20) as response:
            content_type = response.headers.get("Content-Type", "")
            data = response.read(15 * 1024 * 1024)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        QMessageBox.warning(parent, "Link Failed", f"Gagal membuka link gambar:\n{exc}")
        return

    image = QImage()
    if not image.loadFromData(data):
        QMessageBox.warning(parent, "Link Failed", "Link tidak berisi gambar yang bisa dibuka.")
        return

    suffix = ".png"
    if "jpeg" in content_type or "jpg" in content_type:
        suffix = ".jpg"
    fd, path = tempfile.mkstemp(prefix="linked_image_", suffix=suffix, dir=getattr(parent, "capture_dir", None))
    os.close(fd)
    if not image.save(path):
        QMessageBox.warning(parent, "Link Failed", "Gambar dari link berhasil dibaca, tapi gagal disimpan sementara.")
        return

    parent.viewer.set_pixmap(QPixmap.fromImage(image), path)


def save_file(parent):
    pixmap = parent.viewer.label.pixmap()
    if not pixmap or pixmap.isNull():
        QMessageBox.information(parent, "No Image", "Tidak ada gambar untuk disimpan.")
        return
    path, selected_filter = QFileDialog.getSaveFileName(parent, "Save Image", "", IMAGE_FILTER)
    if path:
        root, ext = os.path.splitext(path)
        if not ext:
            ext = ".png" if "png" in selected_filter.lower() else ".jpg"
            path = root + ext

        fmt = FORMAT_BY_EXT.get(ext.lower())
        if not fmt:
            QMessageBox.warning(parent, "Save Failed", "Gunakan ekstensi .png, .jpg, atau .jpeg.")
            return

        if not pixmap.save(path, fmt):
            QMessageBox.warning(parent, "Save Failed", f"Gagal menyimpan gambar ke:\n{path}")
