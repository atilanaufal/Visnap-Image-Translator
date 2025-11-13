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
        """Entry point — ambil gambar dari viewer dan jalankan translasi."""
        label = getattr(self.parent.viewer, "label", None)
        if not label or not label.pixmap():
            QMessageBox.warning(self.parent, "No Image", "Tidak ada gambar untuk diterjemahkan.")
            return

        qimage = label.pixmap().toImage()
        pil_image = Image.fromqimage(qimage)

        translated_pixmap = self.adaptive_translate(pil_image, label.pixmap())
        label.setPixmap(translated_pixmap)

    # =========================================================
    def adaptive_translate(self, pil_image, base_pixmap):
        """Mode adaptif: otomatis pilih mode text padat atau comic speech bubble."""
        data = pytesseract.image_to_data(pil_image, lang="eng", output_type=pytesseract.Output.DICT)
        words = [t.strip() for t in data["text"] if t.strip()]
        num_words = len(words)

        if num_words == 0:
            QMessageBox.information(self.parent, "No Text Found", "Tidak ada teks terdeteksi pada gambar.")
            return base_pixmap

        # Auto mode selection
        mode = "text" if num_words > 30 else "comic"
        print(f"[Adaptive Mode] Detected {num_words} words  Mode: {mode}")

        translated_pixmap = QPixmap(base_pixmap)
        painter = QPainter(translated_pixmap)
        painter.setRenderHint(QPainter.TextAntialiasing)

        if mode == "text":
            self._translate_fulltext(painter, pil_image)
        else:
            self._translate_bubblewise(painter, data)

        painter.end()
        return translated_pixmap

    # =========================================================
    def _translate_fulltext(self, painter, pil_image):
        """Mode teks padat (artikel atau paragraf)."""
        text = pytesseract.image_to_string(pil_image, lang="eng").strip()
        if not text:
            return

        translated = self._cached_translate(text)
        viewport = painter.viewport()

        # Bersihkan area full background
        painter.fillRect(viewport, QColor(255, 255, 255))

        # Auto fit font agar teks muat di gambar
        font = QFont("Arial", 18)
        painter.setFont(font)
        fm = painter.fontMetrics()
        rect_height = fm.boundingRect(viewport, Qt.TextWordWrap, translated).height()

        while rect_height > viewport.height() * 0.9 and font.pointSize() > 8:
            font.setPointSize(font.pointSize() - 1)
            painter.setFont(font)
            fm = painter.fontMetrics()
            rect_height = fm.boundingRect(viewport, Qt.TextWordWrap, translated).height()

        painter.setPen(QColor(0, 0, 0))
        painter.drawText(viewport, Qt.TextWordWrap | Qt.AlignTop, translated)

    # =========================================================
    def _translate_bubblewise(self, painter, data):
        """Mode comic — translate teks per baris, auto-expand rect kiri-kanan-atas-bawah."""
        translator = self.translator
        cache = self.cache
        label = self.parent.viewer.label
        src = label.pixmap().toImage()
        img_w, img_h = src.width(), src.height()

        # === 1. Kelompokkan kata per baris ===
        lines = {}
        for i in range(len(data["text"])):
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

        # === 2. Ubah ke QRect dan gabungkan kata ===
        rects = []
        for key, words in lines.items():
            x1 = min(w["x"] for w in words)
            y1 = min(w["y"] for w in words)
            x2 = max(w["x"] + w["w"] for w in words)
            y2 = max(w["y"] + w["h"] for w in words)
            text = " ".join(w["text"] for w in words)
            rects.append((QRect(x1, y1, x2 - x1, y2 - y1), text))

        # === Helper: Expand rect ke kiri, kanan, atas, bawah ===
        def expand_rect(rect: QRect, pad_ratio_w=0.25, pad_ratio_h=0.35, min_pad=8):
            pad_x = max(min_pad, int(rect.width() * pad_ratio_w))
            pad_y = max(min_pad, int(rect.height() * pad_ratio_h))
            x1 = max(0, rect.left() - pad_x)
            y1 = max(0, rect.top() - pad_y)
            x2 = min(img_w - 1, rect.right() + pad_x)
            y2 = min(img_h - 1, rect.bottom() + pad_y)
            return QRect(x1, y1, x2 - x1, y2 - y1)

        # === Helper: Gabungkan rect yang overlap atau saling dekat ===
        def merge_overlapping_rects(rect_text_list, gap_threshold=12):
            if not rect_text_list:
                return []
            rect_text_list.sort(key=lambda x: (x[0].top(), x[0].left()))
            merged = [rect_text_list[0]]
            for r, t in rect_text_list[1:]:
                last_r, last_t = merged[-1]
                horiz_close = r.left() <= last_r.right() + gap_threshold
                vert_close = r.top() <= last_r.bottom() + gap_threshold
                if horiz_close and vert_close:
                    merged[-1] = (last_r.united(r), f"{last_t} {t}")
                else:
                    merged.append((r, t))
            return merged

        # === 3. Expand dan merge rect ===
        expanded = [(expand_rect(r), t) for r, t in rects]
        merged = merge_overlapping_rects(expanded)

        # === Helper: Ambil warna rata-rata background ===
        def avg_bg_color(rect: QRect):
            r = rect.intersected(QRect(0, 0, src.width(), src.height()))
            if r.isEmpty():
                return QColor(255, 255, 255)
            step_x, step_y = max(1, r.width() // 10), max(1, r.height() // 5)
            rs = gs = bs = cnt = 0
            for yy in range(r.top(), r.bottom(), step_y):
                for xx in range(r.left(), r.right(), step_x):
                    c = src.pixelColor(xx, yy)
                    rs += c.red()
                    gs += c.green()
                    bs += c.blue()
                    cnt += 1
            return QColor(rs // cnt, gs // cnt, bs // cnt) if cnt else QColor(255, 255, 255)

        # === 4. Render tiap bubble teks ===
        for rect, raw_text in merged:
            if not raw_text.strip():
                continue

            # Translate line (pakai cache)
            if raw_text in cache:
                translated = cache[raw_text]
            else:
                try:
                    translated = translator.translate(raw_text)
                except Exception:
                    translated = raw_text
                if not translated:
                    translated = raw_text
                cache[raw_text] = translated

            translated = str(translated).title()

            # Ambil warna background dan isi area teks
            bg = avg_bg_color(rect)
            painter.fillRect(rect, bg)

            # Pilih warna teks kontras
            lum = 0.2126 * bg.redF() + 0.7152 * bg.greenF() + 0.0722 * bg.blueF()
            text_color = QColor(0, 0, 0) if lum > 0.6 else QColor(255, 255, 255)
            painter.setPen(text_color)

            # Ukuran font adaptif
            font = QFont("Arial", int(rect.height() * 0.55), QFont.Bold)
            painter.setFont(font)
            fm = painter.fontMetrics()
            while fm.boundingRect(rect, Qt.TextWordWrap | Qt.AlignCenter, translated).height() > rect.height() * 0.9 and font.pointSize() > 7:
                font.setPointSize(font.pointSize() - 1)
                painter.setFont(font)
                fm = painter.fontMetrics()

            # Gambar teks di tengah area
            painter.drawText(rect, Qt.TextWordWrap | Qt.AlignCenter, translated)

    # =========================================================
    def _cached_translate(self, text):
        """Gunakan cache agar terjemahan cepat dan hemat API call."""
        if text in self.cache:
            return self.cache[text]
        try:
            result = self.translator.translate(text)
        except Exception:
            result = text
        self.cache[text] = result
        return result
