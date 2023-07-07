import imgkit
from PIL import Image

def convertir_html_a_png(html_file,type='png',width=300,height=70):
    if type=='png':
        image_export = 'logo.png'
    elif type=='ico':
         image_export = 'icon.ico'

    options = {
        'format': type,
        'width': width,
        'height': height
    }

    imgkit.from_file(html_file,image_export, options=options)
    image = Image.open(image_export)
    new_image = image.resize((width, height))
    new_image.save(image_export)
  

convertir_html_a_png('logo.html')

convertir_html_a_png('icon.html',type='ico',width=24,height=24)
