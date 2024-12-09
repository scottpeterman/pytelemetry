# main.py example:
from PyQt6.QtWidgets import QApplication
import sys
from device_dashboard import DeviceDashboard

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DeviceDashboard()
    window.show()
    sys.exit(app.exec())

