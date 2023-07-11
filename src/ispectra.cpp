#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <chrono>

#include <QApplication>
#include <QMainWindow>
#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QPushButton>
#include <QRadioButton>
#include <QSlider>
#include <QStyleFactory>
#include <QFrame>
#include <QLineEdit>
#include <QSpacerItem>
#include <QSizePolicy>
#include <QMessageBox>
#include <QFileDialog>
#include <QCheckBox>
#include <QIcon>
#include <QPixmap>
#include <QFont>
#include <QFontDatabase>

#include <seabreeze/seabreeze.h>
#include <seabreeze/spectrometer.h>

// Add necessary includes and namespaces for matplotlib and CSV handling

class MeasurementThread : public QThread {
    Q_OBJECT

public:
    explicit MeasurementThread(seabreeze::Spectrometer* spectrometer, double integrationTime, int numMeasurements = -1)
        : spectrometer(spectrometer), integrationTime(integrationTime), numMeasurements(numMeasurements), isRunning(true) {}

    void run() override {
        spectrometer->setIntegrationTime(integrationTime * 1000);
        if (numMeasurements != -1) {
            for (int i = 0; i < numMeasurements; ++i) {
                if (!isRunning) break;
                std::vector<double> wavelengths = spectrometer->getWavelengths();
                std::vector<double> intensities = spectrometer->getIntensities();
                emit measurementFinished(wavelengths, intensities);
                QThread::msleep(100);
            }
        } else {
            while (isRunning) {
                std::vector<double> wavelengths = spectrometer->getWavelengths();
                std::vector<double> intensities = spectrometer->getIntensities();
                emit measurementFinished(wavelengths, intensities);
                QThread::msleep(100);
            }
        }
    }

    void stop() {
        isRunning = false;
        wait();
    }

signals:
    void measurementFinished(const std::vector<double>& wavelengths, const std::vector<double>& intensities);

private:
    seabreeze::Spectrometer* spectrometer;
    double integrationTime;
    int numMeasurements;
    bool isRunning;
};

class SpectrometerApp : public QMainWindow {
    Q_OBJECT

public:
    SpectrometerApp(QWidget* parent = nullptr)
        : QMainWindow(parent),
          spectrometer(nullptr),
          isMeasuring(false),
          thread(nullptr),
          measurementThread(nullptr),
          measurementCounter(0),
          data(),
          fileName(""),
          filePath(""),
          wavelengths(),
          integrationTime(3.8),
          saveFile(false) {
        // Set up the UI and connect signals/slots
        setupUi();
        connectSignalsSlots();
    }

private slots:
    void selectFolder() {
        QString folder = QFileDialog::getExistingDirectory(this, "Select Destination Folder");
        if (!folder.isEmpty()) {
            filePath = folder.toStdString();
            QString shortenedPath = shortenPath(QString::fromStdString(filePath));
            filePathLabel->setText("File Path: " + shortenedPath);
            filePathLabel->setStyleSheet("background-color:none; color: blue;");
        }
    }

    void handleNumMeasurementsCheckbox(int state) {
        numMeasurementsInput->setEnabled(state == Qt::Checked);
    }

    void startMeasurement() {
        if (isMeasuring) {
            showMessageBox("Measurement already in progress.");
            return;
        }

        if (filePath.empty()) {
            showMessageBox("Select destination folder first.");
            return;
        }

        fileName = fileNameInput->text().toStdString();
        bool ok;
        integrationTime = integrationTimeInput->text().toDouble(&ok);
        if (!ok) {
            showMessageBox("Integration time value is wrong! Check please!");
            return;
        }

        if (integrationTime < 3.8 || integrationTime > 10000) {
            showMessageBox("Integration time must be between 3.8 and 10000.");
            return;
        }

        int numMeasurements = numMeasurementsCheckbox->isChecked() ? numMeasurementsInput->text().toInt() : -1;

        if (measurementThread != nullptr) {
            stopMeasurement();
        }

        isMeasuring = true;
        measurementCounter = 0;
        data.clear();
        wavelengths.clear();
        measurementThread = new MeasurementThread(spectrometer, integrationTime, numMeasurements);
        connect(measurementThread, SIGNAL(measurementFinished(const std::vector<double>&, const std::vector<double>&)),
                this, SLOT(processMeasurement(const std::vector<double>&, const std::vector<double>&)));
        measurementThread->start();
        updateUIState();
    }

    void stopMeasurement() {
        if (isMeasuring) {
            isMeasuring = false;
            measurementThread->stop();
            measurementThread->wait();
            measurementThread->deleteLater();
            measurementThread = nullptr;
            updateUIState();
            QMessageBox::information(this, "Measurement Finished", "Measurement finished successfully.");

            if (saveFileRadio->isChecked()) {
                if (saveData()) {
                    showMessageBox("Measurement finished. Data saved successfully.");
                } else {
                    showMessageBox("Measurement finished. Error occurred while saving the data.");
                }
            }
        }
    }

    void processMeasurement(const std::vector<double>& wavelengths, const std::vector<double>& intensities) {
        data.push_back(intensities);
        this->wavelengths = wavelengths;

        // Update the plot with the new measurement data
        updatePlot(wavelengths, intensities);

        ++measurementCounter;
        measurementCounterLabel->setText("Measurements: " + QString::number(measurementCounter));
        update();
    }

private:
    void setupUi() {
        QWidget* centralWidget = new QWidget(this);
        setCentralWidget(centralWidget);
        QVBoxLayout* layout = new QVBoxLayout(centralWidget);

        QStringList styles = QStyleFactory::keys();
        QString style = "Fusion";
        if (styles.contains(style)) {
            QApplication::setStyle(QStyleFactory::create(style));
        }

        // Sidebar
        QFrame* sidebar = new QFrame(this);
        sidebar->setFrameShape(QFrame::Panel);
        sidebar->setMinimumWidth(sidebarWidth);
        sidebar->setMaximumWidth(sidebarWidth);
        QVBoxLayout* sidebarLayout = new QVBoxLayout(sidebar);

        // Logo image
        QLabel* logoLabel = new QLabel(this);
        QPixmap logoImage("utils/icons/logo.png");
        logoLabel->setPixmap(logoImage);
        logoLabel->setAlignment(Qt::AlignCenter);
        sidebarLayout->addWidget(logoLabel);

        // Experiment parameters
        QFont blockFont("Times", 15);
        QLabel* label0 = new QLabel("Experiment parameters", this);
        label0->setStyleSheet("background-color:none; color: blue;");
        label0->setFont(blockFont);
        sidebarLayout->addWidget(labelContinuación del código en C++:

```cpp)
        // Device name label
        deviceNameLabel = new QLabel("Device: N/A", this);
        sidebarLayout->addWidget(deviceNameLabel);

        // Save file radiobox
        saveFileRadio = new QRadioButton("Save File", this);
        saveFileRadio->setChecked(false);
        sidebarLayout->addWidget(saveFileRadio);

        // File name input
        QHBoxLayout* nameAndDirLayout = new QHBoxLayout();
        sidebarLayout->addLayout(nameAndDirLayout);
        QLabel* fileNameLabel = new QLabel("File Name:", this);
        nameAndDirLayout->addWidget(fileNameLabel);
        fileNameInput = new QLineEdit(this);
        fileNameInput->setText("exp");
        nameAndDirLayout->addWidget(fileNameInput);

        // Select destination folder button
        QPushButton* selectFolderButton = new QPushButton("Select Destination Folder", this);
        connect(selectFolderButton, SIGNAL(clicked()), this, SLOT(selectFolder()));
        nameAndDirLayout->addWidget(selectFolderButton);

        filePathLabel = new QLabel("", this);
        sidebarLayout->addWidget(filePathLabel);

        // Number of measurements checkbox
        QHBoxLayout* numMeasurementsLayout = new QHBoxLayout();
        sidebarLayout->addLayout(numMeasurementsLayout);
        numMeasurementsCheckbox = new QCheckBox("Multiple Measurements", this);
        numMeasurementsCheckbox->setChecked(false);
        connect(numMeasurementsCheckbox, SIGNAL(stateChanged(int)), this, SLOT(handleNumMeasurementsCheckbox(int)));
        numMeasurementsLayout->addWidget(numMeasurementsCheckbox);

        numMeasurementsInput = new QLineEdit(this);
        numMeasurementsInput->setText("1");
        numMeasurementsLayout->addWidget(numMeasurementsInput);

        // Integration time input
        QHBoxLayout* intTimeLayout = new QHBoxLayout();
        sidebarLayout->addLayout(intTimeLayout);
        QLabel* integrationLabel = new QLabel("Integration time (ms):\n[3.8 <= t <= 10000]", this);
        intTimeLayout->addWidget(integrationLabel);
        integrationTimeInput = new QLineEdit(this);
        integrationTimeInput->setText("3.8");
        intTimeLayout->addWidget(integrationTimeInput);

        // Separator line
        QFrame* separator1 = new QFrame(this);
        separator1->setFrameShape(QFrame::HLine);
        separator1->setFrameShadow(QFrame::Sunken);
        sidebarLayout->addWidget(separator1);

        // Run Experiments label
        QLabel* label1 = new QLabel("Run Experiments", this);
        label1->setStyleSheet("background-color:none; color: blue;");
        label1->setFont(blockFont);
        sidebarLayout->addWidget(label1);

        // Start button
        QHBoxLayout* runLayout = new QHBoxLayout();
        sidebarLayout->addLayout(runLayout);
        startButton = new QPushButton("Start", this);
        connect(startButton, SIGNAL(clicked()), this, SLOT(startMeasurement()));
        runLayout->addWidget(startButton);

        // Stop button
        stopButton = new QPushButton("Stop", this);
        connect(stopButton, SIGNAL(clicked()), this, SLOT(stopMeasurement()));
        runLayout->addWidget(stopButton);

        measurementCounterLabel = new QLabel("Measurements: 0", this);
        sidebarLayout->addWidget(measurementCounterLabel);

        // Plot area
        plotLayout = new QVBoxLayout();
        fig = new Figure();
        canvas = new FigureCanvas(fig);
        toolbar = new NavigationToolbar(canvas, this);
        plotLayout->addWidget(canvas);
        plotLayout->addWidget(toolbar);
        layout->addLayout(plotLayout);

        setWindowTitle("IICO-Spectra");
        setWindowIcon(QIcon("utils/icons/icon.ico"));
        resize(windowWidth, windowHeight);
        show();
    }

    void connectSignalsSlots() {
        connect(exitButton, SIGNAL(clicked()), this, SLOT(exitApplication()));
    }

    void updateUIState() {
        startButton->setEnabled(!isMeasuring);
        stopButton->setEnabled(isMeasuring);
    }

    void updatePlot(const std::vector<double>& wavelengths, const std::vector<double>& intensities) {
        // Update the plot with the new measurement data
        // You need to implement the code for updating the plot using a plotting library like QtCharts or matplotlib
    }

    bool saveData() {
        if (!data.empty() && saveFileRadio->isChecked()) {
            std::string filePathData = saveFileWithNumber(fileName, static_cast<int>(integrationTime), filePath);
            std::ofstream file(filePathData);
            if (file.is_open()) {
                // Write the data to the file
                // You need to implement the code for writing the data to a CSV file
                file.close();
                return true;
            } else {
                return false;
            }
        } else {
            return false;
        }
    }

    void showMessageBox(const std::string& message) {
        QMessageBox alert(this);
        alert.setIcon(QMessageBox::Information);
        alert.setText(QString::fromStdString(message));
        alert.setWindowTitle("Alert");
        alert.exec();
    }

    QString shortenPath(const QString& path) {
        // Implement code to shorten the path if needed
        return path;
    }

private:
    const int windowWidth = 800;
    const int windowHeight = 600;
    const int sidebarWidth = 240;

    seabreeze::Spectrometer* spectrometer;
    bool isMeasuring;
    QPushButton* startButton;
    QPushButton* stopButton;
    MeasurementThread* measurementThread;
    int measurementCounter;
    std::vector<std::vector<double>> data;
    std::string fileName;
    std::string filePath;
    std::vector<double> wavelengths;
    double integrationTime;
    bool saveFile;

    // Sidebar widgets
    QLabel* deviceNameLabel;
    QRadioButton* saveFileRadio;
    QLineEdit* fileNameInput;
    QLabel* filePathLabel;
    QCheckBox* numMeasurementsCheckbox;
    QLineEdit* numMeasurementsInput;
    QLineEdit* integrationTimeInput;
    QLabel* measurementCounterLabel;

    // Plot area widgets
    QVBoxLayout* plotLayout;
    Figure* fig;
    FigureCanvas* canvas;
    NavigationToolbar* toolbar;
};

int main(int argc, char** argv) {
    QApplication app(argc, argv);
    SpectrometerApp window;
    window.show();
    return app.exec();
}
