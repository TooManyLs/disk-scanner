from ctypes import windll
from string import ascii_uppercase
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QWidget, QGridLayout, QSpacerItem, QSizePolicy
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QObject, Signal, QThread, QSize
from PySide6.QtGui import QIcon
import os
import sys
import atexit

from main import run_scan, resource_path

class ScanWorker(QObject):
    finished = Signal()
    def __init__(self, drive):
        super().__init__()
        self.drive = drive

    def run(self):
        run_scan(self.drive)
        print("done.")
        self.finished.emit()

class MainWindow(QMainWindow):
    html = resource_path("html/disk.html")
    load = resource_path("html/loading.html")
    start_screen = resource_path("html/start.html")
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Disk scanner")
        self.setWindowIcon(QIcon(resource_path("disk_scan.ico")))
        if os.name == 'nt':
            myappid = 'toomanyls_.disk_scanner.0.0.1'
            windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        self.view = QWebEngineView()
        
        drives = []
        if os.name =="nt":
            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in ascii_uppercase:
                if bitmask & 1:
                    drives.append(f"{letter}:/")
                bitmask >>= 1
        elif os.name == "posix":
            drives.append("/")
        else:
            raise NotImplementedError(f"Unsupported platform: {os.name}")

        if not os.path.exists(self.html):
            self.view.load(QUrl.fromLocalFile(self.start_screen))
        else:
            self.view.load(QUrl.fromLocalFile(self.html))

        layout = QGridLayout()

        layout.addWidget(self.view, 0, 0, -1, -1)

        button_layout = QVBoxLayout()
        self.buttons = []
        for i, drive in enumerate(drives):
            button = QPushButton(f"{drive}")
            button.clicked.connect(lambda checked=False, drive=drive: self.load_scan(drive))
            button.setFixedWidth(70)
            button.setFixedHeight(30)
            button_layout.addWidget(button)
            self.buttons.append(button)

        # Add a vertical spacer at the top of the button layout
        button_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        layout.addLayout(button_layout, 1, 1)

        load_html_button = QPushButton("")
        load_html_button.clicked.connect(self.home)
        load_html_button.setFixedWidth(70)
        load_html_button.setFixedHeight(70)
        load_html_button.setIcon(QIcon(resource_path("public/home.png")))
        load_html_button.setIconSize(QSize(30, 30))

        button_layout.addWidget(load_html_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        atexit.register(self.cleanup)

    def load_scan(self, drive):
        self.view.load(QUrl.fromLocalFile(self.load))
        print(f"scanning {drive}...")
        for button in self.buttons:
            button.setEnabled(False)
        self.worker = ScanWorker(drive)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.on_scan_finished)
        self.thread.started.connect(self.worker.run)
        self.thread.start()
    
    def on_scan_finished(self):
        self.view.load(QUrl.fromLocalFile(self.html))
        self.thread.deleteLater()
        self.worker.deleteLater()
        for button in self.buttons:
            button.setEnabled(True)

    def home(self):
        if os.path.exists(self.html):
            self.view.load(QUrl.fromLocalFile(self.html))

    def cleanup(self):
        if os.path.exists(self.html):
            os.remove(self.html)

app = QApplication(sys.argv)

window = MainWindow()
window.resize(900,800)
window.show()
sys.exit(app.exec())