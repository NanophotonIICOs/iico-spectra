import sys
import os
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton,
    QSlider, QStyleFactory, QFrame, QLineEdit, QSpacerItem, QSizePolicy, QMessageBox, QFileDialog
)
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QThreadPool, QThread,QMutex,QMutexLocker,pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap, QFont, QFontDatabase

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import seabreeze.spectrometers as sb
from datetime import date
import csv

# matplotlib params:
import matplotlib.pyplot as plt
plt.rcParams['lines.linewidth']   = 2
plt.rcParams['axes.linewidth']    = 1.5
plt.rcParams['axes.grid.which']   = 'both'
plt.rcParams['axes.labelsize']    = 15
plt.rcParams['xtick.direction']   = 'in'
plt.rcParams['xtick.labelsize']   = 13
plt.rcParams['ytick.labelsize']   = 13
plt.rcParams['ytick.direction']   = 'in'
plt.rcParams['xtick.major.size']  = 5
# mpl.rcParams['xtick.minor.size']  = 2.5
plt.rcParams['xtick.major.width'] = 1.5
# mpl.rcParams['xtick.minor.width'] = 1.5
plt.rcParams['ytick.major.size']  = 5
# mpl.rcParams['ytick.minor.size']  = 2.5
plt.rcParams['ytick.major.width'] = 1.5
# mpl.rcParams['ytick.minor.width'] = 1.5






def npath(p):
    s = "\\" if sys.platform == "win32" else "/"
    ruta = p.split(s)
    part1 = "C:\\".join(ruta[:3]) if sys.platform == "win32" else "/".join(ruta[:3])
    part2 = "\\".join(ruta[-2:]) if sys.platform == "win32" else "/".join(ruta[-2:])
    new_path = part1 + f"{s}...{s}" + part2
    return new_path

def save_file_with_number(name,it, path):
    base_name = name 
    ext = ".csv"
    today_date = date.today().strftime('%Y-%m-%d')

    counter = 0

    new_name = f"{base_name}-{it}ms-{today_date}{ext}"
    complete_path = os.path.join(path, new_name)

    while os.path.exists(complete_path):
        counter += 1
        new_name = f"{base_name}{counter}-{it}ms-{today_date}{ext}"
        complete_path = os.path.join(path, new_name)

    return complete_path


class WorkerSignals(QObject):
    measurementFinished = pyqtSignal(list)

class MeasurementThread(QThread):
    measurementFinished = pyqtSignal(list)

    def __init__(self, spectrometer, integration_time):
        super().__init__()
        self.spectrometer = spectrometer
        self.integration_time = integration_time
        self.is_running = True

    def run(self):
        self.spectrometer.integration_time_micros(self.integration_time * 1000)
        while self.is_running:
            wavelengths = self.spectrometer.wavelengths()
            intensities = self.spectrometer.intensities()
            self.measurementFinished.emit([wavelengths, intensities])
            QThread.msleep(100)  # Pequeña pausa para permitir que el hilo principal responda

    def stop(self):
        self.is_running = False
        self.wait()  # Esperar a que el hilo finalice completamente
        

        
class SpectrometerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.spectrometer = None
        self.is_measuring = False
        self.thread = None
        self.worker = None
        self.measurement_thread = None
        self.threadpool = QThreadPool()  # Agregar esta línea
        self.measurement_counter = 0
        self.data = []
        self.file_name = ""
        self.file_path = ""
        self.wavelengths = []
        self.integration_time = 3.8
        self.save_file = False
        self.setWindowTitle("IICO-Spectra")
        icon = QIcon("utils/icons/icon.ico")
        self.setWindowIcon(icon)        
        
        # Obtener el tamaño del monitor
        desktop = QApplication.desktop()
        screen_rect = desktop.screenGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        # Calcular el tamaño de la ventana y el sidebar proporcionalmente
        self.window_width = int(screen_width * 0.55)
        self.window_height = int(screen_height * 0.5)
        self.sidebar_width = int(self.window_width * 0.3)
        self.plot_width = self.window_width - self.sidebar_width
        self.plot_height = self.window_height 
        self.resize(self.window_width, self.window_height)

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
        sidebar.setMinimumWidth(self.sidebar_width)  
        sidebar.setMaximumWidth(self.sidebar_width)  
        
        font_id = QFontDatabase.addApplicationFont("utils/icons/fonts/Ubuntu-Bold.ttf")  
        if font_id != -1:
            font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
            labels_font = QFont(font_name) 
        else:
            font_name = "Serif"
            labels_font = QFont(font_name, 10) 
            
        sidebar.setFont(labels_font)
        sidebar_layout = QVBoxLayout(sidebar)

        
        # logo image
        logo_label = QLabel()
        logo_image = QPixmap("utils/icons/logo.png")
        logo_label.setPixmap(logo_image)
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        block_font = QFont("Times", 15)  
        label0 = QLabel("Experiment parameters")
        #label0.setAlignment(Qt.AlignCenter)
        label0.setStyleSheet("background-color:none; color: blue;")
        label0.setFont(block_font)

        sidebar_layout.addWidget(label0)
        
        #------------------------------------- box 0-------------------------------------------------------------       
        box0_layout = QHBoxLayout()
        sidebar_layout.addLayout(box0_layout)
        # Device name label
        self.device_name_label = QLabel("Device: N/A")
        box0_layout.addWidget(self.device_name_label)
        
        # Save file radiobox
        self.save_file_radio = QRadioButton("Save File")
        self.save_file_radio.setChecked(False)
        box0_layout.addWidget(self.save_file_radio)
       
       
        #------------------------------------- box 1-------------------------------------------------------------       
        name_and_dir_layout = QHBoxLayout()
        sidebar_layout.addLayout(name_and_dir_layout)
        # File name input
        file_name_label = QLabel("File Name:")
        name_and_dir_layout.addWidget(file_name_label)

        self.file_name_input = QLineEdit()
        self.file_name_input.setText("exp")
        name_and_dir_layout.addWidget(self.file_name_input)

        # Select destination folder button
        select_folder_button = QPushButton("Select Destination Folder")
        select_folder_button.clicked.connect(self.select_folder)
        name_and_dir_layout.addWidget(select_folder_button)
        self.file_path_label = QLabel("")
        sidebar_layout.addWidget(self.file_path_label)
        
        #-----------------------------------------------------------------------------------------------------  
        
        #------------------------------------- box 2-------------------------------------------------------------  
        int_time_layout = QHBoxLayout()
        sidebar_layout.addLayout(int_time_layout)
        # Integration time input
        integration_label = QLabel("Integration time (ms):\n[3.8 <= t <= 10000]")
        int_time_layout.addWidget(integration_label)

        self.integration_time_input = QLineEdit()
        self.integration_time_input.setText("3.8")
        int_time_layout.addWidget(self.integration_time_input)
        
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.HLine)
        separator1.setFrameShadow(QFrame.Sunken)
        sidebar_layout.addWidget(separator1)
        #-----------------------------------------------------------------------------------------------------  


        label1 = QLabel("Run Experiments")
        #label1.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(label1)
        label1.setStyleSheet("background-color:none; color: blue;")
        label1.setFont(block_font)
        
        #------------------------------------- box 3------------------------------------------------------------- 
        run_layout = QHBoxLayout()
        sidebar_layout.addLayout(run_layout)
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_measurement)
        run_layout.addWidget(self.start_button)
        
        # stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_measurement)
        run_layout.addWidget(self.stop_button)
        self.measurement_counter_label = QLabel("Measurements: 0")
        #self.measurement_counter_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.measurement_counter_label)
        
        
        
        
        # expander_sidebars0= QSpacerItem(self.sidebar_width, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # sidebar_layout.addItem(expander_sidebars0)

        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        sidebar_layout.addWidget(separator2)
        #------------------------------------------------------------------------------------------------------ 
        
        
        #------------------------------------- box 4------------------------------------------------------------- 
        
       
        label2 = QLabel("Plot Parameters")
        #label1.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(label2)
        label2.setStyleSheet("background-color:none; color: blue;")
        label2.setFont(block_font)
        
        
        xslider_layout = QHBoxLayout()
        sidebar_layout.addLayout(xslider_layout)
        # Sliders
        xlim_min_slider_label = QLabel("xmin:")
        xslider_layout.addWidget(xlim_min_slider_label)
        self.xlim_min_slider = QSlider(Qt.Horizontal)
        self.xlim_min_slider.setMinimum(195)
        self.xlim_min_slider.setMaximum(558)
        self.xlim_min_slider.setValue(195)
        self.xlim_min_slider.valueChanged.connect(self.update_xlim)
        xslider_layout.addWidget(self.xlim_min_slider)
        
        xlim_max_slider_label = QLabel("xmax:")
        xslider_layout.addWidget(xlim_max_slider_label)
        self.xlim_max_slider = QSlider(Qt.Horizontal)
        self.xlim_max_slider.setMinimum(559)
        self.xlim_max_slider.setMaximum(1118)
        self.xlim_max_slider.setValue(1200)
        self.xlim_max_slider.valueChanged.connect(self.update_xlim)
        xslider_layout.addWidget(self.xlim_max_slider)

        yslider_layout = QHBoxLayout()
        sidebar_layout.addLayout(yslider_layout)
        ylim_min_slider_label = QLabel("ymin:")
        yslider_layout.addWidget(ylim_min_slider_label)
        self.ylim_min_slider = QSlider(Qt.Horizontal)
        self.ylim_min_slider.setMinimum(0)
        self.ylim_min_slider.setMaximum(999)
        self.ylim_min_slider.valueChanged.connect(self.update_ylim)
        yslider_layout.addWidget(self.ylim_min_slider)
        
        ylim_max_slider_label = QLabel("ymax")
        yslider_layout.addWidget(ylim_max_slider_label)
        self.ylim_max_slider = QSlider(Qt.Horizontal)
        self.ylim_max_slider.setMinimum(1000)
        self.ylim_max_slider.setMaximum(16383)
        self.ylim_max_slider.setValue(16383)
        self.ylim_max_slider.valueChanged.connect(self.update_ylim)
        yslider_layout.addWidget(self.ylim_max_slider)
        
        
        # expander_sidebars1= QSpacerItem(self.sidebar_width, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        # sidebar_layout.addItem(expander_sidebars1)
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setFrameShadow(QFrame.Sunken)
        sidebar_layout.addWidget(separator3)
        

        #------------------------------------------------------------------------------------------------------ 

        expander_exit = QSpacerItem(self.sidebar_width, 150, QSizePolicy.Minimum, QSizePolicy.Expanding)
        sidebar_layout.addItem(expander_exit)
        # exit button
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.exit_application)
        sidebar_layout.addWidget(exit_button)
        
        #sidebar_layout.addStretch()
        layout.addWidget(sidebar)

        # Plot area
        self.plot_layout = QVBoxLayout()  # Cambio a QVBoxLayout
        self.fig = Figure(figsize=(10, 6))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.plot_layout.addWidget(self.canvas)
        self.plot_layout.addWidget(self.toolbar)  # Agregar el toolbar al layout
        layout.addLayout(self.plot_layout)
        self.show()
        
        self.mutex = QMutex()  # Crear una instancia de QMutex
        self.check_spectrometers()

    def check_spectrometers(self):
        spec_list = sb.list_devices()
        if len(spec_list) == 0:
            QMessageBox.warning(self, "No spectrometers found", "No spectrometers found connected. Please check the connection and try again.")
        else:
            # select the spectometer
            self.spectrometer = sb.Spectrometer(spec_list[0])
            self.device_name_label.setText(f"Device: {self.spectrometer.model}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.file_path = folder
            fpath = f"{self.file_path}"
            self.file_path_label.setText(f"File Path: {npath(fpath)}")
            self.file_path_label.setStyleSheet("background-color:none; color: blue;")
            
            
    def start_measurement(self):
        with QMutexLocker(self.mutex):  # Bloquear el mutex
            if self.is_measuring:
                self.show_alert("Measurement already in progress.")
                return

            if not self.file_path:
                self.show_alert("Select destination folder first.")
                return

            self.file_name = self.file_name_input.text()
            try:
                self.integration_time = float(self.integration_time_input.text())
            except ValueError:
                self.show_alert("Integration time value is wrong!. Check Please!")
                return

            if not (3.8 <= self.integration_time <= 10000):
                self.show_alert("Integration time must be between 3.8 and 10000.")
                return

            if self.measurement_thread is not None:  # Detener el hilo de medición existente si lo hay
                self.stop_measurement()

            self.is_measuring = True
            self.measurement_counter = 0
            self.data = []
            self.wavelengths = []
            self.measurement_thread = MeasurementThread(self.spectrometer, self.integration_time)
            self.measurement_thread.measurementFinished.connect(self.process_measurement)
            self.measurement_thread.start()
            self.update_ui_state()



            
    def update_ui_state(self):
        if self.is_measuring:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

            
    def handle_measurement_finished(self, measurement_data):
        wavelengths, intensities = measurement_data
        self.wavelengths = wavelengths
        self.data.append(intensities)
        self.measurement_counter += 1
        self.measurement_counter_label.setText(f"Measurements: {self.measurement_counter}")
        self.update_plot()

    def stop_measurement(self):
        with QMutexLocker(self.mutex):
            if self.is_measuring:
                self.is_measuring = False
                self.measurement_thread.stop()
                self.measurement_thread.wait()  # Esperar a que el hilo finalice completamente
                self.measurement_thread.deleteLater()  # Eliminar el hilo de medición
                self.measurement_thread = None
                self.update_ui_state()
                QMessageBox.information(self, "Measurement Finished", "Measurement finished successfully.")
                
                if self.save_file_radio.isChecked():
                    if self.save_data():
                        self.show_alert("Measurement finished. Data saved successfully.")
                        self.data_saved = True
                    else:
                        self.show_alert("Measurement finished. Error occurred while saving the data.")
                        self.data_saved = False
            else:
                self.show_alert("No measurement in progress.")
                self.data_saved = False

    @pyqtSlot(list)
    def process_measurement(self, measurement_data):
        wavelengths, intensities = measurement_data
        self.data.append(intensities.copy())  # add a copy of intensity list
        self.wavelengths = wavelengths

        self.ax.clear()
        self.ax.plot(wavelengths, intensities, color='tab:blue',label=f"Measure:{self.measurement_counter}")
        self.ax.set_xlabel('Wavelength (nm)')
        self.ax.set_ylabel('Intensity')
        self.ax.set_xlim([self.xlim_min_slider.value(), self.xlim_max_slider.value()])
        self.ax.set_ylim([self.ylim_min_slider.value(), self.ylim_max_slider.value()])
        self.canvas.draw()
        self.measurement_counter += 1
        self.measurement_counter_label.setText(f"Measurements: {self.measurement_counter}")
        self.update()



    def measurement_finished(self):
        self.thread.deleteLater()
        self.thread = None
        QMessageBox.information(self, "Measurement Finished", "Measurement finished successfully.")
        
 
        
    def update_xlim(self, value):
        try:
            if self.ax.lines:
                self.ax.set_xlim([self.xlim_min_slider.value(), self.xlim_max_slider.value()])
                self.canvas.draw()
        except IndexError:
            pass


    def update_ylim(self, value):
        try:
            if self.ax.lines:
                self.ax.set_ylim([self.ylim_min_slider.value(), self.ylim_max_slider.value()])
                self.canvas.draw()
        except IndexError:
            pass


    def save_data(self):
        if self.data and self.save_file_radio.isChecked():
            self.file_name_data = save_file_with_number(self.file_name,self.integration_time,self.file_path)
            try:
                with open(self.file_name_data, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Wavelength (nm)"] + [f"m-{i}" for i in range(len(self.data))])
                    writer.writerows(zip(self.wavelengths, *self.data))
                return True
            except IOError:
                return False
        else:
            return False
        
    def exit_application(self):
        if self.is_measuring:
            confirm_exit = QMessageBox.question(
                self, "Confirm Exit", "Measurement in progress. Do you want to stop and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm_exit == QMessageBox.Yes:
                self.stop_measurement()  # Detener la medición en curso
                self.close()  # Cerrar la ventana principal
        else:
            confirm_exit = QMessageBox.question(
                self, "Confirm Exit", "Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm_exit == QMessageBox.Yes:
                self.close()  # Cerrar la ventana principal
    
    def show_alert(self, message):
        alert = QMessageBox()
        alert.setIcon(QMessageBox.Information)
        alert.setText(message)
        alert.setWindowTitle("Alert")
        alert.exec_()
            
            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpectrometerApp()
    window.show()
    sys.exit(app.exec_())