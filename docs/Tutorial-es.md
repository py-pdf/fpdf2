Los diferentes ejemplos muestran rápidamente como usar fpdf2. Encontrará todas las características principales explicadas.

English version: [Tutorial](Tutorial.md)

Version en français : [Tutorial-fr](Tutorial-fr.md)

Deutsche Version: [Tutorial-de](Tutorial-de.md)

हिंदी संस्करण: [Tutorial-हिंदी](Tutorial-हिंदी.md)

Versione in italiano: [Tutorial-it](Tutorial-it.md)

Versão em português: [Tutorial-pt](Tutorial-pt.md)

Версия на русском: [Tutorial-ru](Tutorial-ru.md)

[TOC]

## Ejemplo básico ##

Empecemos con el ejemplo clásico: 

```python
{% include "../tutorial/tuto1.py" %}
```

[Demo](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

Luego de incluir la biblioteca, creamos un objeto FPDF. El constructor [FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) es usado aquí con los valores predeterminados: páginas en A4 portrait -vertical- y la unidad de medida en milímetros. Podría haberlos especificado explícitamente: 

```python
pdf=FPDF('P', 'mm', 'A4')
```

Es posible usar landscape -horizontal- (L), otros formatos de página (como Letter -carta- y Legal -oficio-) y unidad de medida (pt, cm, in). 

Por el momento no hay una página, entonces tenemos que agregar una con [add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). El origen es la esquina superior-izquierda y la posición actual está ubicada a 1 cm de los bordes; los márgenes pueden ser cambiados con [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins). 

Antes de que podamos imprimir texto, es obligatorio seleccionar una fuente con [set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), de lo contrario, el documento será inválido. Elegimos helvetica bold 16: 

```python
pdf.set_font('helvetica', 'B', 16)
```

Podríamos haber especificado italic -cursiva- con I, underline -subrayado- con U o fuente regular con string vacío (o cualquier combinación). Notar que el tamaño de la fuente es dado en puntos, no milímetros (u otra unidad de medida del usuario); ésta es la única excepción. Las otras fuentes estándar son Times, Courier, Symbol y ZapfDingbats. 

Podemos ahora imprimir una celda con [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). Una celda es un área rectangular, posiblemente enmarcada, que contiene algún texto. Se imprime en la posición actual. Especificamos sus dimensiones, su texto (centrado o alineado), si los bordes deberían ser dibujados, y donde la posición actual se mueve después (a la derecha, abajo o al principio de la próxima linea). Para agregar un marco, haremos: 

```python
pdf.cell(40, 10, 'Hola mundo !', 1)
```

Para agregar una nueva celda próxima a ella, con texto centrado y luego ir a la siguiente línea, haríamos: 

```python
pdf.cell(60, 10, 'Hecho con FPDF.', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
```

*Nota*: el salto de línea puede hacerse también con [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). Este método permite especificar adicionalmente la altura del salto. 

Finalmente, el documento es cerrado y enviado al explorador con [output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Podemos haberlo grabado a un fichero al pasarle el nombre de archivo. 

*Precaución*: en caso cuando el PDF es enviado al explorador, nada más debe ser enviado a la salida, ni antes ni después (el mínimo caracter importa). 


## Encabezado, pie de página, salto de página e imagen ##

Aquí hay un ejemplo de dos páginas con encabezado, pie y logo: 

```python
{% include "../tutorial/tuto2.py" %}
```
[Demo](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)

Este ejemplo hace uso de métodos  [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) y  [footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) para procesar el encabezado y pie de página. Son llamados automáticamente. Ya existen en la clase FPDF pero no hacen nada por sí solos, por lo tanto tenemos que extender la clase y sobreescribirlos. 

El logo es impreso con el método [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) especificando su esquina superior izquierda y su ancho. La altura es calculada automáticamente para respetar las proporciones de la imagen. 

Para imprimir el número de página, un valor nulo es pasado como ancho de celda. Significa que la celda deberá ser extendida hasta el margen derecho de la página; es útil centrar texto. El número de página actual es devuelto por el método [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no); y para el número total de páginas, éste será obtenido mediante el valor especial {nb} que será sustituido al cerrar el documento (si de antemano se llamó [alias_nb_pages](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)). 
Notar el uso del método [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) que permite establecer la posición en una ubicación absoluta en la página, empezando desde arriba hacia abajo. 

Otra característica interesante es usada aquí: el salto de página automático. Tan pronto una celda cruza el límite de una página (por defecto a 2 centímetros desde abajo), un salto es realizado y la fuente es restaurada. Aunque el encabezado y pie de página tienen su propia fuente (helvetica), el cuerpo continúa en Times. Este mecanismo de restauración automática también se aplica a los colores y el ancho de la línea. El límite que dispara los saltos de página puede establecerse con [set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).


## Saltos de línea y colores ##

Continuemos con un ejemplo que imprime párrafos justificados. También ilustra el uso de colores.
```python
{% include "../tutorial/tuto3.py" %}
```
[Demo](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto3.pdf)

El método [get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) permite determinar la longitud de una cadena en la fuente actual, usado aquí para calcular la posición y el ancho del marco que rodea al título. Los colores son establecidos (vía [set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), [set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) y [set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)) y el grosor de la línea es establecido a 1 mm (contra 0.2 por defecto) con [set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). Finalmente, emitimos la celda (el último parámetro es True para indicar que el fondo debe ser rellenado). 

El método usado para imprimir párrafos es [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell). Cada vez que una línea alcanza el extremo derecho de la celda o un caracter de retorno de línea, un salto de línea es emitido y una nueva celda es automáticamente creada bajo la actual. El texto es justificado por defecto. 

Dos propiedades del documento son definidas: el título ([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) y el autor ([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Las propiedades pueden ser vistas de dos formas. La primera es abrir el documento directamente con Acrobat Reader, ir al menú Archivo y elegir la opción Propiedades del Documento. La segunda, también disponible en el plug-in, es hacer clic izquierdo y seleccionar Propiedades del documento (Document Properties).
