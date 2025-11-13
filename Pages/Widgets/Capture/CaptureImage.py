from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import random

class CaptureImage(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(1920, 1080)
        # self.setWindowFlags(
        #     Qt.WindowStaysOnTopHint
        #     | Qt.FramelessWindowHint
        #     | Qt.Tool  # so it doesn't show in taskbar
        # )
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.Tool  # so it doesn't show in taskbar
        )
        self.count = random.randint(0,199999999999)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: rgba(0, 0, 0, 0);")
        self.setGeometry(self._all_screens_geometry())
        self.rubber = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()
        self.is_selecting = False
        self.setWindowOpacity(0.1)
        self.hint = QLabel("- Drag area to capture image -", self)
        self.hint.setStyleSheet("color: white; background: rgba(0,0,0,500); padding:25px; border-radius:5px;")
        self.hint.move(500, 30)
        self.hint.show()   
        

    def _all_screens_geometry(self):
        # union bounding rect of all screens so overlay covers multi-monitor
        screens = QGuiApplication.screens()
        if not screens:
            return QApplication.primaryScreen().geometry()
        rect = screens[0].geometry()
        for s in screens[1:]:
            rect = rect.united(s.geometry())
        return rect

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubber.setGeometry(QRect(self.origin, QSize()))
            self.rubber.show()
            self.is_selecting = True

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            rect = QRect(self.origin, event.pos()).normalized()
            self.rubber.setGeometry(rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.selected_rect = self.rubber.geometry()
            if hasattr(self, "selected_rect") and not self.selected_rect.isNull():
                pix = self.capture_rect(self.selected_rect)
                # save file or show preview
                self.count += 1
                pix.save(f"capture{self.count}.png", "PNG")
                print(f"Saved capture{self.count}.png")
            self.setAttribute(Qt.WA_DeleteOnClose) 
            self.close()
            # keep rubber visible until user confirm; optionally auto-capture here
            # self.capture_and_save(self.selected_rect)

    def keyPressEvent(self, event):
        # Enter => capture selection, Esc => cancel
        # if event.key() in (Qt.Key_Return, Qt.Key_Enter):

        if event.key() == Qt.Key_Escape:
            print("Cancelled.")
            self.setAttribute(Qt.WA_DeleteOnClose) 
            self.close()

    def capture_rect(self, rect: QRect) -> QPixmap:
        """
        Grab the underlying screen pixels for the selected rectangle.
        Rect is in overlay coordinates (global coordinates), so map to screen coordinates.
        """
        # find screen under mouse (works multi-monitor)
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos)

        # If multiple monitors placed with offsets, grabWindow uses global coords with offsets.
        # Use grabWindow(0, x, y, w, h)
        global_top_left = self.mapToGlobal(rect.topLeft())
        x = global_top_left.x()
        y = global_top_left.y()
        w = rect.width()
        h = rect.height()

        return screen.grabWindow(0, x, y, w, h)