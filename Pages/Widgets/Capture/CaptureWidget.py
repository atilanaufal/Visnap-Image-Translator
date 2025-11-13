from Pages.Widgets.Capture.CaptureImage import CaptureImage

class CaptureWidget:
    def __init__(self, parent):
        self.parent = parent
        self.capture = None
        
    def open_overlay(self):
        self.capture = CaptureImage()
        self.parent.windows.append(self.capture)
        self.capture.showFullScreen()
        self.parent.hide()
        self.capture.destroyed.connect(self.cleanup)

    def cleanup(self):
        
        self.parent.show()
        if self.capture in self.parent.windows:
            self.parent.windows.remove(self.capture)
        self.parent.viewer.show_image() 
