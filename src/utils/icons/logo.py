import io
import IPython.display
import cairocffi as cairo
import svgwrite
from PIL import Image

# Crear el archivo de imagen en memoria
w = 330
h = 100
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)

# Crear el contexto de dibujo
context = cairo.Context(surface)

# Establecer el tamaño y tipo de fuente
font_path = "caprasimo.ttf"  # Replace with the path to your font file
context.set_font_size(55)
context.select_font_face("Times", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
context.set_font_options(cairo.FontOptions())

# Establecer el color del rectángulo
context.set_source_rgb(0.2, 0.4, 0.6)

# Dibujar el rectángulo de fondo
context.rectangle(0.0 * w, 0.0 * h, 1 * w, 1 * h)
context.fill()

# Establecer el color del texto (blanco opaco)
context.set_source_rgba(1, 1, 1, 1)
text = "IICO-Spectra"

# Obtener las dimensiones del texto
x_bearing, y_bearing, text_width, text_height = context.text_extents(text)[:4]

# Calcular la posición del texto en el centro del logo
x = (w - text_width) / 2 - x_bearing
y = (h - text_height) / 2 - y_bearing

# Dibujar el texto con un color de relleno blanco opaco
context.move_to(x, y)
context.show_text(text)
context.fill()

# Establecer el color del texto (blanco transparente)
context.set_source_rgba(1, 1, 1, 0)
context.move_to(x, y)
context.show_text(text)
context.fill()

# Guardar el archivo de imagen en disco
filename = "logo.png"
surface.write_to_png(filename)

# Guardar el archivo de imagen en disco en formato ICO
filename_ico = "logo.ico"
with open(filename_ico, "wb") as f:
    surface.write_to_png(f)

# Convertir el archivo ICO a la imagen de icono utilizando Pillow
image = Image.open(filename_ico)
image.save("logo.ico")

# Mostrar la imagen en Jupyter Notebook
IPython.display.Image(filename)
