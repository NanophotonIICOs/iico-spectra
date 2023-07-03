import sys
import os
import datetime
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFrame, QFileDialog, QMessageBox, QRadioButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from threading import Thread
import time
import seabreeze.spectrometers as sb
import csv
from datetime import date

# matplotlib params:
import matplotlib as plt
plt.rcParams["font.family"] = "sans-serif"
import matplotlib.colors as mcolors


def npath(p):
    s = "\\" if sys.platform == "Windows" else "/"
    ruta = p.split(s)
    part1 = "C:\\".join(ruta[:3]) if sys.platform == "Windows" else "/".join(ruta[:3])
    part2 = "\\".join(ruta[-2:]) if sys.platform == "Windows" else "/".join(ruta[-2:])
    new_path = part1 + f"{s}...{s}" + part2
    return new_path


class SpectrometerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.spectrometer = None
        self.is_measuring = False
        self.thread = None
        self.measurement_counter = 0
        self.data = []
        self.file_name = ""
        self.file_path = ""
        self.wavelengths = []
        self.integration_time = 3.8
        self.save_file = True
        self.setWindowTitle("ISpectra")
        icon = QIcon("utils/icons/logo.ico")
        self.setWindowIcon(icon)
        self.resize(900, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Sidebar
        sidebar = QFrame(self)
        # sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setFrameShape(QFrame.Panel)
        sidebar.setMinimumWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        # logo image
        logo_label = QLabel()
        logo_image = QPixmap("utils/icons/logo.png")
        logo_label.setPixmap(logo_image)
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        label0 = QLabel("Experiment parameters")
        label0.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(label0)
        # Device name label
        self.device_name_label = QLabel("Device: N/A")
        sidebar_layout.addWidget(self.device_name_label)

        # File name input
        file_name_label = QLabel("File Name:")
        sidebar_layout.addWidget(file_name_label)

        self.file_name_input = QLineEdit()
        self.file_name_input.setText("data")
        sidebar_layout.addWidget(self.file_name_input)

        # Select destination folder button
        select_folder_button = QPushButton("Select Destination Folder")
        select_folder_button.clicked.connect(self.select_folder)
        sidebar_layout.addWidget(select_folder_button)

        self.file_path_label = QLabel("")
        sidebar_layout.addWidget(self.file_path_label)

        # Save file radiobox
        self.save_file_radio = QRadioButton("Save File")
        self.save_file_radio.setChecked(True)
        sidebar_layout.addWidget(self.save_file_radio)

        # Integration time input
        integration_label = QLabel("Integration time:\n [3.8 <= i-time <= 10000]")
        sidebar_layout.addWidget(integration_label)

        self.integration_time_input = QLineEdit()
        self.integration_time_input.setText("3.8")
        sidebar_layout.addWidget(self.integration_time_input)

        label1 = QLabel("Run Experiments")
        label1.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(label1)
        start_button = QPushButton("Start")
        start_button.clicked.connect(self.start_continuous_reading)
        sidebar_layout.addWidget(start_button)

        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.stop_continuous_reading)
        sidebar_layout.addWidget(stop_button)

        sidebar_layout.addStretch()

        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.exit_application)
        sidebar_layout.addWidget(exit_button)

        self.measurement_counter_label = QLabel("Measurements: 0")
        sidebar_layout.addWidget(self.measurement_counter_label)

        layout.addWidget(sidebar)

        # Main plot area
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        self.show()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.file_path = folder
            fpath = f"{self.file_path}/{self.file_name_input.text()}.csv"
            self.file_path_label.setText(f"File Path: {npath(fpath)}")

    def start_continuous_reading(self):
        if not self.file_path:
            self.show_alert("Select destination folder first.")
            return

        self.file_name = self.file_name_input.text()

        integration_time = float(self.integration_time_input.text())
        if 3.8 <= integration_time <= 10000:
            self.integration_time = integration_time
        else:
            self.show_alert("Integration time must be between 3.8 and 10000.")
            return

        if self.spectrometer is None:
            try:
                self.spectrometer = sb.Spectrometer.from_first_available()
                self.device_name_label.setText(f"Device: {self.spectrometer.model}")
            except sb.SeaBreezeError:
                self.show_alert("No spectrometer device found. Please connect a device.")
                return

        self.spectrometer.integration_time_micros(int(self.integration_time * 1000))
        self.is_measuring = True
        self.data = []
        self.thread = Thread(target=self.continuous_reading)
        self.thread.start()

    def continuous_reading(self):
        intensities = []
        while self.is_measuring:
            try:
                wavelengths = self.spectrometer.wavelengths()
                intensities = self.spectrometer.intensities()
                self.data.append(intensities.copy())  # Agregar una copia de las intensidades a la lista de datos
                self.wavelengths = wavelengths

                self.ax.cla()
                self.ax.plot(wavelengths, intensities, color='tab:blue', label=self.measurement_counter)
                self.ax.set_xlabel('Wavelength (nm)')
                self.ax.set_ylabel('Intensity')
                self.ax.set_title('Spectrum')
                #self.ax.set_ylim([0,16383])
                self.ax.legend(frameon=False,loc='upper right')
                
                self.canvas.draw()
                self.measurement_counter += 1
                self.measurement_counter_label.setText(f"Measurements: {self.measurement_counter}")
                time.sleep(0.1)

            except sb.SeaBreezeError:
                self.show_alert("Device disconnected.")
                self.stop_continuous_reading()
                break

    def stop_continuous_reading(self):
        if not self.is_measuring:
            return

        self.is_measuring = False
        self.thread.join()
        self.save_data()
        self.measurement_counter = 0
        self.measurement_counter_label.setText(f"Measurements: {self.measurement_counter}")

    def save_data(self):
        if self.data and self.save_file_radio.isChecked():
            today = date.today()
            datet = today.strftime("%Y-%m-%d")
            current_time = datetime.datetime.now()
            file_path = f"{self.file_path}/{self.file_name}-{datet}-{current_time.hour}:{current_time.minute}:{current_time.second}.csv"
            try:
                with open(file_path, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Wavelength (nm)"] + list(range(len(self.data))))
                    writer.writerows(zip(self.wavelengths, *self.data))
                self.show_alert("Data saved successfully.")
            except IOError:
                self.show_alert("Error occurred while saving the data.")
        else:
            self.show_alert("No data to save.")

    def exit_application(self):
        sys.exit()

    def show_alert(self, message):
        alert = QMessageBox()
        alert.setIcon(QMessageBox.Information)
        alert.setText(message)
        alert.setWindowTitle("Alert")
        alert.exec_()

app = QApplication(sys.argv)
spectrometer_app = SpectrometerApp()
sys.exit(app.exec_())
