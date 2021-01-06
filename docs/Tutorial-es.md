Los diferentes ejemplos muestran rápidamente como usar PyFPDF. Encontrará todas las características principales explicadas.

English: [Tutorial](Tutorial.md)

[TOC]

## Ejemplo básico ##

Empecemos con el ejemplo clásico: 

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font('Arial', 'B', 16)
pdf.cell(40, 10, 'Hola Mundo!')
pdf.output('tuto1.pdf', 'F')
```

[Demo](https://github.com/reingart/pyfpdf/raw/master/tutorial/tuto1.pdf)

Luego de incluir la biblioteca, creamos un objeto FPDF. El constructor [FPDF](reference/FPDF.md) es usado aquí con los valores predeterminados: páginas en A4 portrait -vertical- y la unidad de medida en milímetros. Podría haberlos especificado explícitamente: 

```python
pdf=FPDF('P', 'mm', 'A4')
```

Es posible usar landscape -horizontal- (L), otros formatos de página (como Letter -carta- y Legal -oficio-) y unidad de medida (pt, cm, in). 

Por el momento no hay una página, entonces tenemos que agregar una con [add_page](reference/add_page.md). El origen es la esquina superior-izquierda y la posición actual está ubicada a 1 cm de los bordes; los márgenes pueden ser cambiados con [set_margins](reference/set_margins.md). 

Antes de que podamos imprimir texto, es obligatorio seleccionar una fuente con [set_font](reference/set_font.md), de lo contrario, el documento será inválido. Elegimos Arial bold 16: 

```python
pdf.set_font('Arial', 'B', 16)
```

Podríamos haber especificado italic -cursiva- con I, underline -subrayado- con U o fuente regular con string vacío (o cualquier combinación). Notar que el tamaño de la fuente es dado en puntos, no milímetros (u otra unidad de medida del usuario); ésta es la única excepción. Las otras fuentes estándar son Times, Courier, Symbol y ZapfDingbats. 

Podemos ahora imprimir una celda con [cell](reference/cell.md). Una celda es un área rectangular, posiblemente enmarcada, que contiene algún texto. Se imprime en la posición actual. Especificamos sus dimensiones, su texto (centrado o alineado), si los bordes deberían ser dibujados, y donde la posición actual se mueve después (a la derecha, abajo o al principio de la próxima linea). Para agregar un marco, haremos: 

```python
pdf.cell(40, 10, 'Hola mundo !', 1)
```

Para agregar una nueva celda próxima a ella, con texto centrado y luego ir a la siguiente línea, haríamos: 

```python
pdf.cell(60, 10, 'Hecho con FPDF.', 0, 1, 'C')
```

*Nota*: el salto de línea puede hacerse también con [ln](reference/ln.md). Este método permite especificar adicionalmente la altura del salto. 

Finalmente, el documento es cerrado y enviado al explorador con [output](reference/output.md). Podemos haberlo grabado a un fichero al pasarle el nombre de archivo. 

*Precaución*: en caso cuando el PDF es enviado al explorador, nada más debe ser enviado a la salida, ni antes ni después (el mínimo caracter importa). 


## Encabezado, pie de página, salto de página e imagen ##

Aquí hay un ejemplo de dos páginas con encabezado, pie y logo: 

```python
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        # Logo
        self.image('logo_pb.png', 10, 8, 33)
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Moverse a la derecha
        self.cell(80)
        # Título
        self.cell(30, 10, 'Title', 1, 0, 'C')
        # Salto de línea(Line break)
        self.ln(20)

    # Pie de página
    def footer(self):
        # Posicionamiento a 1.5 cm desde el fin de página
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Número de página
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

# Instanciación de clase heredada
pdf = PDF()
pdf.alias_nb_pages()
pdf.add_page()
pdf.set_font('Times', '', 12)
for i in range(1, 41):
    pdf.cell(0, 10, 'Printing line number ' + str(i), 0, 1)
pdf.output('tuto2.pdf', 'F')
```
[Demo](https://github.com/reingart/pyfpdf/raw/master/tutorial/tuto2.pdf)

Este ejemplo hace uso de métodos  [header](reference/header.md) y  [footer](reference/footer.md) para procesar el encabezado y pie de página. Son llamados automáticamente. Ya existen en la clase FPDF pero no hacen nada por sí solos, por lo tanto tenemos que extender la clase y sobreescribirlos. 

El logo es impreso con el método [image](reference/image.md) especificando su esquina superior izquierda y su ancho. La altura es calculada automáticamente para respetar las proporciones de la imagen. 

Para imprimir el número de página, un valor nulo es pasado como ancho de celda. Significa que la celda deberá ser extendida hasta el margen derecho de la página; es útil centrar texto. El número de página actual es devuelto por el método [page_no](reference/page_no.md); y para el número total de páginas, éste será obtenido mediante el valor especial {nb} que será sustituido al cerrar el documento (si de antemano se llamó [alias_nb_pages](reference/alias_nb_pages.md)). 
Notar el uso del método [set_y](reference/set_y.md) que permite establecer la posición en una ubicación absoluta en la página, empezando desde arriba hacia abajo. 

Otra característica interesante es usada aquí: el salto de página automático. Tan pronto una celda cruza el límite de una página (por defecto a 2 centímetros desde abajo), un salto es realizado y la fuente es restaurada. Aunque el encabezado y pie de página tienen su propia fuente (Arial), el cuerpo continúa en Times. Este mecanismo de restauración automática también se aplica a los colores y el ancho de la línea. El límite que dispara los saltos de página puede establecerse con [set_auto_page_break](reference/set_auto_page_break.md).


## Saltos de línea y colores ##

Continuemos con un ejemplo que imprime párrafos justificados. También ilustra el uso de colores.
```python
from fpdf import FPDF

title = '20000 Leagues Under the Seas'

class PDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font('Arial', 'B', 15)
        # Calcular ancho del texto (title) y establecer posición
        w = self.get_string_width(title) + 6
        self.set_x((210 - w) / 2)
        # Colores del marco, fondo y texto
        self.set_draw_color(0, 80, 180)
        self.set_fill_color(230, 230, 0)
        self.set_text_color(220, 50, 50)
        # Grosor del marco (1 mm)
        self.set_line_width(1)
        # Título
        self.cell(w, 9, title, 1, 1, 'C', 1)
        # Salto de línea
        self.ln(10)

    def footer(self):
        # Posición a 1.5 cm desde abajo
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Color de texto en gris
        self.set_text_color(128)
        # Número de pagina
        self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

    def chapter_title(self, num, label):
        # Arial 12
        self.set_font('Arial', '', 12)
        # Color de fondo
        self.set_fill_color(200, 220, 255)
        # Título
        self.cell(0, 6, 'Chapter %d : %s' % (num, label), 0, 1, 'L', 1)
        # Salto de línea
        self.ln(4)

    def chapter_body(self, name):
        # Leer archivo de texto
        with open(name, 'rb') as fh:
            txt = fh.read().decode('latin-1')
        # Times 12
        self.set_font('Times', '', 12)
        # Emitir texto justificado
        self.multi_cell(0, 5, txt)
        # Salto de línea
        self.ln()
        # Mención en italic -cursiva-
        self.set_font('', 'I')
        self.cell(0, 5, '(end of excerpt)')

    def print_chapter(self, num, title, name):
        self.add_page()
        self.chapter_title(num, title)
        self.chapter_body(name)

pdf = PDF()
pdf.set_title(title)
pdf.set_author('Jules Verne')
pdf.print_chapter(1, 'A RUNAWAY REEF', '20k_c1.txt')
pdf.print_chapter(2, 'THE PROS AND CONS', '20k_c2.txt')
pdf.output('tuto3.pdf', 'F')
```
[Demo](https://github.com/reingart/pyfpdf/raw/master/tutorial/tuto3.pdf)

El método [get_string_width](reference/get_string_width.md) permite determinar la longitud de una cadena en la fuente actual, usado aquí para calcular la posición y el ancho del marco que rodea al título. Los colores son establecidos (vía [set_draw_color](reference/set_draw_color.md), [set_fill_color](reference/set_fill_color.md) y [set_text_color](reference/set_text_color.md)) y el grosor de la línea es establecido a 1 mm (contra 0.2 por defecto) con [set_line_width](reference/set_line_width.md). Finalmente, emitimos la celda (el último parámetro es True para indicar que el fondo debe ser rellenado). 

El método usado para imprimir párrafos es [multi_cell](reference/multi_cell.md). Cada vez que una línea alcanza el extremo derecho de la celda o un caracter de retorno de línea, un salto de línea es emitido y una nueva celda es automáticamente creada bajo la actual. El texto es justificado por defecto. 

Dos propiedades del documento son definidas: el título ([set_title](reference/set_title.md)) y el autor ([set_author](reference/set_author.md)). Las propiedades pueden ser vistas de dos formas. La primera es abrir el documento directamente con Acrobat Reader, ir al menú Archivo y elegir la opción Propiedades del Documento. La segunda, también disponible en el plug-in, es hacer clic izquierdo y seleccionar Propiedades del documento (Document Properties).

## Notas de instalación ##

Anteriormente, para importar el objeto se debía usar el paquete pyfpdf:

```python
from pyfpdf import FPDF
```

A partir de la versión 1.7, para importar el objeto se debe usar el paquete fpdf:

```python
from fpdf import FPDF
```




