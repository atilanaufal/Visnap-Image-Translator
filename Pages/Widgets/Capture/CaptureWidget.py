from Pages.Widgets.Capture.CaptureImage import CaptureImage
import sys

class CaptureWidget:
    def __init__(self, parent):
        self.parent = parent
        self.capture = None
        
    def open_overlay(self):
        self.capture = CaptureImage(getattr(self.parent, "capture_dir", None))
        self.parent.windows.append(self.capture)
        self.parent.hide()
        if sys.platform.startswith("win"):
            self.capture.showFullScreen()
        else:
            self.capture.show()
        self.capture.raise_()
        self.capture.activateWindow()
        self.capture.destroyed.connect(self.cleanup)

    def cleanup(self):
        
        self.parent.show()
        if self.capture in self.parent.windows:
            self.parent.windows.remove(self.capture)
        self.parent.viewer.show_image() 
