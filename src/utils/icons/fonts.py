
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication

# Crear una instancia de QApplication o QGuiApplication
app = QApplication([])  # O bien, QGuiApplication([])

# Obtener una lista de todas las familias de fuentes disponibles
families = QFontDatabase().families()

# Imprimir la lista de familias de fuentes
for family in families:
    print(family)

# Ejecutar la aplicación
app.exec_()
