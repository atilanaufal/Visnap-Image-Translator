from PySide6.QtGui import QPainter, QPixmap, QColor, QFont
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt, QRect
from PIL import Image
from deep_translator import GoogleTranslator as Translator
import pytesseract


class Translate:
    def __init__(self, parent):
        self.parent = parent
        self.translator = Translator(source="auto", target="id")
        self.cache = {}

    # =========================================================
    def translate_image(self):
        """Ambil gambar dari viewer dan jalankan translasi."""
        label = getattr(self.parent.viewer, "label", None)
        if not label or not label.pixmap():
            QMessageBox.warning(self.parent, "No Image", "Tidak ada gambar untuk diterjemahkan.")
            return

        qimage = label.pixmap().toImage()
        pil_image = Image.fromqimage(qimage)

        translated_pixmap = self.replace_translate_perline_fast(pil_image, label.pixmap())
        label.setPixmap(translated_pixmap)

    # =========================================================
    def replace_translate_perline_fast(self, pil_image, base_pixmap):
        """
        Mode replace-only tapi translate per baris, bukan per kata.
        Cepat (batch translation), hasil rapi kayak teks paragraf.
        """
        data = pytesseract.image_to_data(pil_image, lang="eng", output_type=pytesseract.Output.DICT)
        num_boxes = len(data["text"])

        if num_boxes == 0:
            QMessageBox.information(self.parent, "No Text Found", "Tidak ada teks terdeteksi pada gambar.")
            return base_pixmap

        translated_pixmap = QPixmap(base_pixmap)
        painter = QPainter(translated_pixmap)
        painter.setRenderHint(QPainter.TextAntialiasing)

        label = self.parent.viewer.label
        src = label.pixmap().toImage()

        # === 1. Gabungkan kata per baris ===
        lines = {}
        for i in range(num_boxes):
            word = data["text"][i].strip()
            if not word:
                continue
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            lines.setdefault(key, []).append({
                "x": data["left"][i],
                "y": data["top"][i],
                "w": data["width"][i],
                "h": data["height"][i],
                "text": word
            })

        # === 2. Hitung area dan teks tiap baris ===
        line_rects = []
        for key, words in lines.items():
            x1 = min(w["x"] for w in words)
            y1 = min(w["y"] for w in words)
            x2 = max(w["x"] + w["w"] for w in words)
            y2 = max(w["y"] + w["h"] for w in words)
            text = " ".join(w["text"] for w in words)
            rect = QRect(x1, y1, x2 - x1, y2 - y1)
            line_rects.append((rect, text))

        # === 3. Batch translate semua baris ===
        texts_to_translate = [text for _, text in line_rects if text.strip()]
        translated_results = []

        if texts_to_translate:
            try:
                joined_text = " || ".join(texts_to_translate)
                translated_batch = self.translator.translate(joined_text)
                translated_results = [t.strip() for t in translated_batch.split("||")]
            except Exception:
                translated_results = [self.translator.translate(t) for t in texts_to_translate]

        # === 4. Render tiap baris di posisi aslinya ===
        for (rect, orig_text), translated in zip(line_rects, translated_results):
            translated = translated.strip() if translated else orig_text
            translated = translated[0].upper() + translated[1:] if len(translated) > 1 else translated

            # Ambil warna background rata-rata area teks
            bg = self._avg_bg(src, rect)
            painter.fillRect(rect, bg)

            # Pilih warna teks kontras
            lum = 0.2126 * bg.redF() + 0.7152 * bg.greenF() + 0.0722 * bg.blueF()
            text_color = QColor(0, 0, 0) if lum > 0.6 else QColor(255, 255, 255)
            painter.setPen(text_color)

            # Font adaptif
            font = QFont("Arial", max(10, int(rect.height() * 0.8)), QFont.Bold)
            painter.setFont(font)
            fm = painter.fontMetrics()

            # Tambah padding biar teks gak nempel tepi
            padded_rect = QRect(
                rect.left() + int(rect.width() * 0.05),
                rect.top() + int(rect.height() * 0.05),
                int(rect.width() * 0.9),
                int(rect.height() * 0.9)
            )

            # Shrink otomatis jika teks terlalu tinggi
            while (
                fm.boundingRect(padded_rect, Qt.TextWordWrap | Qt.AlignCenter, translated).height() > padded_rect.height() * 0.9
            ) and font.pointSize() > 7:
                font.setPointSize(font.pointSize() - 1)
                painter.setFont(font)
                fm = painter.fontMetrics()

            # Gambar teks hasil translate di posisi tengah baris
            painter.drawText(padded_rect, Qt.TextWordWrap | Qt.AlignCenter, translated)

        painter.end()
        return translated_pixmap

    # =========================================================
    def _avg_bg(self, src, rect):
        """Ambil warna background rata-rata di area teks (untuk menimpa teks asli)."""
        r = rect.intersected(QRect(0, 0, src.width(), src.height()))
        rs = gs = bs = cnt = 0
        step_x = max(1, r.width() // 10)
        step_y = max(1, r.height() // 6)
        for yy in range(r.top(), r.bottom(), step_y):
            for xx in range(r.left(), r.right(), step_x):
                c = src.pixelColor(xx, yy)
                rs += c.red()
                gs += c.green()
                bs += c.blue()
                cnt += 1
        if cnt == 0:
            return QColor(255, 255, 255)
        return QColor(rs // cnt, gs // cnt, bs // cnt)
