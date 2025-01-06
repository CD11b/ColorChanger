from PyQt5.QtCore import QThread, pyqtSignal

class FileTypeScanner(QThread):
    fileTypesSignal = pyqtSignal(list)  # Signal to send back file types
    
    def __init__(self, directory):
        super().__init__()
        self._directory = directory

    def run(self):
        """Search for file types in the directory."""
        fileTypes = set()  # To store unique file types

        for root, dirs, files in os.walk(self._directory):
            for file in files:
                fileExtension = os.path.splitext(file)[1]
                if fileExtension:
                    fileTypes.add(fileExtension.lower())  # Convert to lowercase for consistency

        # Emit the signal with the found file types
        self.fileTypesSignal.emit(list(fileTypes))

