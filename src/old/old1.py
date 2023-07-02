import sys
import datetime
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFrame, QFileDialog
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from threading import Thread
import time
import seabreeze.spectrometers as sb
import csv

class SpectrometerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.spectrometer = None
        self.is_measuring = False
        self.thread = None
        self.measurement_counter = 0
        self.data = []
        self.file_name = ""
        self.wavelengths = []
        
        self.setWindowTitle("ISpectra")
        
        central_widget = QWidget(self)1
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        
        # Sidebar
        sidebar = QFrame(self)
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setFixedWidth(150)
        
        sidebar_layout = QVBoxLayout(sidebar)
        
        # Device info
        device_label = QLabel("Device:")
        sidebar_layout.addWidget(device_label)
        
        self.device_info_label = QLabel("")
        sidebar_layout.addWidget(self.device_info_label)
        
        sidebar_layout.addStretch()
        
        # Integration time input
        integration_label = QLabel("Integration time: [3.8 < i-time < 10000]")
        sidebar_layout.addWidget(integration_label)
        
        self.integration_time_input = QLineEdit()
        self.integration_time_input.setText("3.8")
        sidebar_layout.addWidget(self.integration_time_input)
        
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
        
        start_button = QPushButton("Start")
        start_button.clicked.connect(self.start_continuous_reading)
        sidebar_layout.addWidget(start_button)
        
        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.stop_continuous_reading)
        sidebar_layout.addWidget(stop_button)
        
        sidebar_layout.addStretch()
        
        layout.addWidget(sidebar)
        
        # Main plot area
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        
        self.measurement_counter_label = QLabel("Measurements: 0")
        self.measurement_counter_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(self.measurement_counter_label)
        
        self.show()
        
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.file_name = f"{folder}/{self.file_name_input.text()}.csv"
    
    def start_continuous_reading(self):
        if self.is_measuring:
            return
        
        if not self.file_name:
            self.show_alert("Select destination folder first.")
            return
        
        devices = sb.list_devices()
        if len(devices) > 0:
            self.spectrometer = sb.Spectrometer(devices[0])
            self.device_info_label.setText(self.spectrometer.model)
            self.is_measuring = True
            self.thread = Thread(target=self.continuous_reading)
            self.thread.start()
            
            self.data = []
            self.wavelengths = self.spectrometer.wavelengths()
            self.data.append(self.wavelengths)
            
            self.measurement_counter = 0
            self.measurement_counter_label.setText(f"Measurements: {self.measurement_counter}")
        else:
            self.device_info_label.setText("No device detected.")
    
    def stop_continuous_reading(self):
        if self.is_measuring:
            self.is_measuring = False
            self.thread.join()
            self.spectrometer.close()
            self.spectrometer = None
    
    def continuous_reading(self):
        while self.is_measuring:
            intensities = self.spectrometer.intensities()
            
            self.ax.cla()
            self.ax.plot(self.wavelengths, intensities)
            self.ax.set_xlabel("Wavelength (nm)")
            self.ax.set_ylabel("Intensity")
            self.ax.set_title("Spectrum")
            self.canvas.draw()
            
            self.data.append(intensities)
            self.measurement_counter += 1
            self.measurement_counter_label.setText(f"Measurements: {self.measurement_counter}")
            
            time.sleep(0.5)
            
            if self.measurement_counter >= 10:  # Change this number as needed
                self.save_data()
                self.data = [self.wavelengths]
                self.measurement_counter = 0
                self.measurement_counter_label.setText(f"Measurements: {self.measurement_counter}")
    
    def save_data(self):
        if self.data:
            with open(self.file_name, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(zip(*self.data))
    
    def closeEvent(self, event):
        self.stop_continuous_reading()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectrometerApp()
    sys.exit(app.exec_())
