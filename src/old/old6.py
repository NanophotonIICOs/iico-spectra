import sys
import os
import datetime
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFrame, QFileDialog, QMessageBox, QRadioButton, QSlider
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
    s = "\\" if sys.platform == "win32" else "/"
    ruta = p.split(s)
    part1 = "C:\\".join(ruta[:3]) if sys.platform == "win32" else "/".join(ruta[:3])
    part2 = "\\".join(ruta[-2:]) if sys.platform == "win32" else "/".join(ruta[-2:])
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
        self.setWindowTitle("IICO-Spectra")
        icon = QIcon("utils/icons/logo.ico")
        self.setWindowIcon(icon)
        self.resize(1000, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # Sidebar
        sidebar = QFrame(self)
        sidebar.setFrameShape(QFrame.Panel)
        sidebar.setMinimumWidth(323)
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

        # Slider widgets
        sidebar_layout.addWidget(QLabel("Axis Limits"))
        self.xlim_min_slider = self.create_slider_with_label(sidebar_layout, "X Min:", 200, 500, 0)
        self.xlim_max_slider = self.create_slider_with_label(sidebar_layout, "X Max:", 500, 1120, 1120)
        self.ylim_min_slider = self.create_slider_with_label(sidebar_layout, "Y Min:", 0, 10000, 0)
        self.ylim_max_slider = self.create_slider_with_label(sidebar_layout, "Y Max:", 10000, 20000, 20000)

        layout.addWidget(sidebar)

        # Main plot area
        self.fig = Figure(figsize=(10, 8), dpi=100)
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

    def create_slider_with_label(self, layout, label_text, min_val, max_val, start_val):
        slider_layout = QVBoxLayout()
        label = QLabel(label_text)
        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(start_val)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.valueChanged.connect(self.update_axis_limits)
        slider_layout.addWidget(label)
        slider_layout.addWidget(slider)
        layout.addLayout(slider_layout)
        return slider

    def update_axis_limits(self):
        xlim_min = self.xlim_min_slider.value()
        xlim_max = self.xlim_max_slider.value()
        ylim_min = self.ylim_min_slider.value()
        ylim_max = self.ylim_max_slider.value()

        if xlim_min >= xlim_max or ylim_min >= ylim_max:
            self.show_alert("Invalid axis limits. Minimum value should be less than maximum value.")
            return

        self.ax.set_xlim(xlim_min, xlim_max)
        self.ax.set_ylim(ylim_min, ylim_max)
        self.canvas.draw()

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
                self.show_alert("No spectrometer found.")
                return

        self.is_measuring = True
        self.measurement_counter = 0
        self.data = []

        self.thread = Thread(target=self.continuous_reading)
        self.thread.start()

    def continuous_reading(self):
        while self.is_measuring:
            try:
                wavelengths = self.spectrometer.wavelengths()
                intensities = self.spectrometer.intensities(integration_time=self.integration_time)

                self.data.append((wavelengths, intensities))
                self.measurement_counter += 1

                self.ax.clear()
                for i in range(len(self.data)):
                    self.ax.plot(self.data[i][0], self.data[i][1])
                self.ax.set_xlim(self.xlim_min_slider.value(), self.xlim_max_slider.value())
                self.ax.set_ylim(self.ylim_min_slider.value(), self.ylim_max_slider.value())
                self.ax.set_xlabel("Wavelength (nm)")
                self.ax.set_ylabel("Intensity (counts)")
                self.ax.set_title("Spectrometer Reading")
                self.canvas.draw()

                self.measurement_counter_label.setText(f"Measurements: {self.measurement_counter}")
                time.sleep(0.1)
            except Exception as e:
                print(f"Error: {e}")
                self.show_alert("An error occurred while reading the spectrometer.")
                self.stop_continuous_reading()
                break

    def stop_continuous_reading(self):
        self.is_measuring = False
        if self.thread is not None:
            self.thread.join()
            self.thread = None

        if self.spectrometer is not None:
            self.spectrometer.close()
            self.spectrometer = None

        if self.save_file:
            if not self.file_path:
                self.show_alert("Select destination folder first.")
                return

            file_name = f"{self.file_path}/{self.file_name}.csv"
            with open(file_name, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['wavelength (nm)', 'intensity (counts)'])
                for i in range(len(self.data)):
                    writer.writerow(self.data[i][0])
                    writer.writerow(self.data[i][1])

            self.show_alert(f"Data saved to {npath(file_name)}")

    def exit_application(self):
        self.stop_continuous_reading()
        QApplication.quit()

    def show_alert(self, message):
        alert = QMessageBox()
        alert.setIcon(QMessageBox.Information)
        alert.setText(message)
        alert.setWindowTitle("Alert")
        alert.exec_()


if __name__ == "__main__":
    app = QApplication([])
    window = SpectrometerApp()
    app.exec_()
