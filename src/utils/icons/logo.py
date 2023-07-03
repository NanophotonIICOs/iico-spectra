import io
import IPython.display
import cairo
import svgwrite

# Crear el archivo de imagen en memoria
w = 250
h = 100
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)

# Crear el contexto de dibujo
context = cairo.Context(surface)

# Establecer el tamaño y tipo de fuente
context.set_font_size(55)
context.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

# Establecer el color del rectángulo
context.set_source_rgb(0.2, 0.4, 0.6)

# Dibujar el rectángulo de fondo
context.rectangle(0.0 * w, 0.0 * h, 1 * w, 1 * h)
context.fill()

# Establecer el color del texto
context.set_source_rgb(1, 1, 1)

# Obtener las dimensiones del texto
text = "ISpectra"
x_bearing, y_bearing, text_width, text_height = context.text_extents(text)[:4]

# Calcular la posición del texto en el centro del logo
x = (w - text_width) / 2 - x_bearing
y = (h - text_height) / 2 - y_bearing

# Dibujar el texto con una máscara invertida
context.set_operator(cairo.OPERATOR_CLEAR)
context.move_to(x, y)
context.show_text(text)
context.fill()
context.set_operator(cairo.OPERATOR_OVER)

# Guardar el archivo de imagen en disco
filename = "logo.png"
surface.write_to_png(filename)

# filename_svg = "logo.svg"
# dwg = svgwrite.Drawing(filename_svg, profile='tiny')
# dwg.add(dwg.rect((0, 0), (w, h), fill='rgb(0.2, 0.4, 0.6)'))
# dwg.add(dwg.text(text, insert=((w - text_width) / 2, (h + text_height) / 2), font_size="50px", fill='rgb(1, 1, 1)'))
# dwg.save()


# Mostrar la imagen en Jupyter Notebook
IPython.display.Image(filename)
