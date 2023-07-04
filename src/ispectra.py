import sys
import os
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFrame, QFileDialog, QMessageBox, QRadioButton, QSlider,QStyleFactory)
from PyQt5.QtCore import Qt,QThread
from PyQt5.QtGui import QPixmap, QIcon
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from threading import Thread
import seabreeze.spectrometers as sb
import csv
from datetime import date

# matplotlib params:
# import matplotlib.pyplot as plt
# plt.rcParams["font.family"] = "sans-serif"





def npath(p):
    s = "\\" if sys.platform == "win32" else "/"
    ruta = p.split(s)
    part1 = "C:\\".join(ruta[:3]) if sys.platform == "win32" else "/".join(ruta[:3])
    part2 = "\\".join(ruta[-2:]) if sys.platform == "win32" else "/".join(ruta[-2:])
    new_path = part1 + f"{s}...{s}" + part2
    return new_path


def save_file_with_number(file_name, routh):
    cont = 0
    base_name, ext = os.path.splitext(file_name)
    new_name = file_name

    while os.path.exists(os.path.join(routh, new_name)):
        cont += 1
        new_name = f"{base_name}-{cont}{ext}"

    complet_r = os.path.join(routh, new_name)
    return complet_r

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
        self.save_file = False
        self.setWindowTitle("IICO-Spectra")
        icon = QIcon("utils/icons/logo.ico")
        self.setWindowIcon(icon)
        self.resize(900, 600)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        styles = QStyleFactory.keys()
        style = "Fusion"  
        if style in styles:
            QApplication.setStyle(QStyleFactory.create(style))
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


        self.measurement_counter_label = QLabel("Measurements: 0")
        sidebar_layout.addWidget(self.measurement_counter_label)
        
        
        # stop button
        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.stop_continuous_reading)
        sidebar_layout.addWidget(stop_button)

        # Sliders
        xlim_slider_label = QLabel("X-axis limits:")
        sidebar_layout.addWidget(xlim_slider_label)
        self.xlim_min_slider = QSlider(Qt.Horizontal)
        self.xlim_min_slider.setMinimum(200)
        self.xlim_min_slider.setMaximum(600)
        self.xlim_min_slider.setValue(200)
        self.xlim_min_slider.valueChanged.connect(self.update_xlim)
        sidebar_layout.addWidget(self.xlim_min_slider)
        
        self.xlim_max_slider = QSlider(Qt.Horizontal)
        self.xlim_max_slider.setMinimum(600)
        self.xlim_max_slider.setMaximum(1120)
        self.xlim_max_slider.setValue(1200)
        self.xlim_max_slider.valueChanged.connect(self.update_xlim)
        sidebar_layout.addWidget(self.xlim_max_slider)

        ylim_slider_label = QLabel("Y-axis limits:")
        sidebar_layout.addWidget(ylim_slider_label)
        self.ylim_min_slider = QSlider(Qt.Horizontal)
        self.ylim_min_slider.setMinimum(0)
        self.ylim_min_slider.setMaximum(1000)
        self.ylim_min_slider.valueChanged.connect(self.update_ylim)
        sidebar_layout.addWidget(self.ylim_min_slider)
        
        self.ylim_max_slider = QSlider(Qt.Horizontal)
        self.ylim_max_slider.setMinimum(1000)
        self.ylim_max_slider.setMaximum(16383)
        self.ylim_max_slider.setValue(16383)
        self.ylim_max_slider.valueChanged.connect(self.update_ylim)
        sidebar_layout.addWidget(self.ylim_max_slider)
        
        # exit button
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.exit_application)
        sidebar_layout.addWidget(exit_button)
        
        sidebar_layout.addStretch()
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
                self.ax.set_xlim([self.xlim_min_slider.value(), self.xlim_max_slider.value()])
                self.ax.set_ylim([self.ylim_min_slider.value(), self.ylim_max_slider.value()])
                self.ax.legend(frameon=False,loc='upper right')

                self.canvas.draw()
                self.measurement_counter += 1
                self.measurement_counter_label.setText(f"Measurements: {self.measurement_counter}")
                self.update()
                QThread.msleep(100)

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

    def update_xlim(self, value):
        if self.ax.lines:
            self.ax.set_xlim([self.xlim_min_slider.value(), self.xlim_max_slider.value()])
            self.canvas.draw()


    def update_ylim(self, value):
        if self.ax.lines:
            self.ax.set_ylim([self.ylim_min_slider.value(), self.ylim_max_slider.value()])
            self.canvas.draw()


    def save_data(self):
        if self.data and self.save_file_radio.isChecked():
            today = date.today()
            datet = today.strftime("%Y-%m-%d")
            file_path = f"{self.file_name}-{self.integration_time}ms-{datet}.csv"
            file_path = save_file_with_number(file_path,self.file_path)
            try:
                with open(file_path, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Wavelength (nm)"] + list(range(len(self.data))))
                    writer.writerows(zip(self.wavelengths, *self.data))
                self.show_alert(f"{file_path} data saved successfully.")
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
