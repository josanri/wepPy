import sys

from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QPushButton, QVBoxLayout, QFileDialog, QLabel, QWidget, QMessageBox, QCheckBox, QSpinBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThreadPool

from worker import Worker
from pyqextra import QHLine

class UIMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pool = QThreadPool().globalInstance()
        self.initUI()

    def initUI(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()

        instruction_label = QLabel(
            "<h2>Instructions:</h2>"
            "<ol>"
            "<li>Click the <span style='color: #2D7632; font-weight: bold;'>Select images</span> button to choose the images you want to transform.</li>"
            "<li>The files will be generated next to the original with the '.webp' suffix.</li>"
            "<li>You can also turned all your images inside a folder to webp at the second button.</li>"
            "</ol>"
        )
        instruction_label.setStyleSheet("QLabel { color: #333; }")
        instruction_label.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(instruction_label)
        
        self.separator = QHLine()
        self.layout.addWidget(self.separator)

        self.advanced_settings = QLabel("Advanced settings:")
        self.advanced_settings.setStyleSheet("QLabel { color: #4f4f4f; }")
        self.layout.addWidget(self.advanced_settings)

        self.warning_enabled = QCheckBox("Show results at the end")
        self.warning_enabled.setChecked(True)
        self.layout.addWidget(self.warning_enabled)

        self.overwrite_enabled = QCheckBox("Overwrite files if the file already exist")
        self.overwrite_enabled.setChecked(False)
        self.layout.addWidget(self.overwrite_enabled)

        self.compression_layout = QGridLayout()

        self.quality = QLabel("Quality (0-100):")
        self.compression_layout.addWidget(self.quality, 0, 0, 1, 1)

        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(0, 100)
        self.quality_spin.setValue(80)
        self.compression_layout.addWidget(self.quality_spin, 0, 1)
        
        self.loseless_enabled = QCheckBox("Loseless conversion")
        self.loseless_enabled.setChecked(False)
        self.loseless_enabled.clicked.connect(lambda: self.quality_spin.setValue(100))
        self.compression_layout.addWidget(self.loseless_enabled, 1, 1)

        self.layout.addLayout(self.compression_layout)

        self.select_images_button = QPushButton("Select images in formats like .png, .jpeg or .jpg")
        self.select_images_button.setStyleSheet("QPushButton { background-color: #7DCE82; color: black; border-radius: 5px; padding: 5px; }")
        self.select_images_button.clicked.connect(lambda: self.webp_process_files(self.get_files_by_images))
        self.layout.addWidget(self.select_images_button)

        self.select_folder_button = QPushButton("Select folder to turn all the images inside to .webp")
        self.select_folder_button.setStyleSheet("QPushButton { background-color: #2D7632; color: white; border-radius: 5px; padding: 5px; }")
        self.select_folder_button.clicked.connect(lambda: self.webp_process_files(self.get_files_by_folder))
        self.layout.addWidget(self.select_folder_button)

        self.central_widget.setLayout(self.layout)

    def closeEvent(self, event):
        self.pool.clear()
        event.accept()

    def show_result(self, unprocessed_files):
        if self.warning_enabled.isChecked():
            msg = QMessageBox()
            if len(unprocessed_files) > 0:
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText(f"Could not process the next file{'s' if len(unprocessed_files) > 1 else ''}:\n{','.join(unprocessed_files)}")
                msg.setWindowTitle("Warning")
            else:
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText("Files processed without issues")
                msg.setWindowTitle("Info")
            msg.exec_()

    def webp_process_files(self, file_getter):
        filenames = file_getter()
        if len(filenames) == 0:
            return
        if self.pool.activeThreadCount() >= self.pool.maxThreadCount():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText(f"Please, wait till othes thread finish")
            msg.setWindowTitle("Warning")
            msg.exec_()
        else:
            worker_thread = Worker(filenames,
                                    **{
                                        "overwrite": self.overwrite_enabled.isChecked(),
                                        "quality": self.quality_spin.value(),
                                        "loseless": self.loseless_enabled.isChecked()
                                    }
            )
            worker_thread.signals.result.connect(self.show_result)
            self.pool.start(worker_thread)
    
    def get_files_by_images(self) -> [str]:
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        filenames, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Image Files (*.ico *.png *.jpg *.jpeg *.bmp);;All Files (*)", options=options)
        return filenames
    
    def get_files_by_folder(self) -> [str]:
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        directory_folder = QFileDialog.getExistingDirectory(self, "Select Folder", "", options=options)
        if not directory_folder:
            return []
        extensions = ["png", "jpeg", "jpg"]
        filenames = []

        for ext in extensions:
            filenames.extend(file.resolve() for file in Path(directory_folder).glob(f"**/*.{ext}"))

        return filenames
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet("QMainWindow { background-color: #f0f0f0; }")

    window = UIMainWindow()
    window.setWindowTitle("WepPy - A Webp converter")
    window.setGeometry(100, 100, 300, 200)

    icon = QIcon("assets/favicon.ico.web")
    if len(icon.availableSizes()) == 0:
        icon = QIcon("assets/favicon.ico")
    window.setWindowIcon(icon)

    window.show()
    sys.exit(app.exec_())
