from PyQt5.QtWidgets import QApplication
from color_changer import ColorChangerApp

if __name__ == '__main__':
    app = QApplication([])
    window = ColorChangerApp()
    window.show()
    app.exec_()
