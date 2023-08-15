# Tutorial #

Documentación completa de los métodos: [Documentación de la API de `fpdf.FPDF`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Tutorial 1 - Ejemplo básico ##

Empecemos con el ejemplo clásico: 

```python
{% include "../tutorial/tuto1.py" %}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto1.pdf)

Luego de incluir la biblioteca, creamos un objeto `FPDF`. El constructor 
[FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) es usado aquí con los valores predeterminados: 
Las páginas están en A4 vertical y la unidad de medida es milímetros.
Podría haberse especificado explícitamente con: 

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

Es posible configurar el PDF en modo horizontal (`L`) o usar otros formatos de página 
como carta (`Letter`) y oficio (`Legal`) y unidades de medida (`pt`, `cm`, `in`).

Por el momento no hay una página, entonces tenemos que agregar una con 
[add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). El origen es la esquina superior izquierda y la 
posición actual está ubicada por defecto a 1 cm de los bordes; los márgenes pueden 
ser cambiados con [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins). 

Antes de que podamos imprimir texto, es obligatorio seleccionar una fuente con 
[set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), de lo contrario, el documento sería inválido. 
Elegimos helvetica en negrita 16: 

```python
pdf.set_font('helvetica', 'B', 16)
```

Podríamos haber especificado cursiva con `I`, subrayado con `U` o fuente regular 
con una cadena de texto vacía (o cualquier combinación). Nota que el tamaño de la fuente es dado en 
puntos, no en milímetros (u otra unidad de medida del usuario); ésta es la única excepción. 
Las otras fuentes estándar son `Times`, `Courier`, `Symbol` y `ZapfDingbats`. 

Podemos ahora imprimir una celda con [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). Una celda es un área 
rectangular, posiblemente enmarcada, que contiene algún texto. Se imprime en la posición 
actual. Especificamos sus dimensiones, su texto (centrado o alineado), si los bordes 
deberían ser dibujados, y a donde la posición actual se mueve después (a la derecha, 
abajo o al principio de la próxima linea). Para agregar un marco, haremos esto: 

```python
pdf.cell(40, 10, '¡Hola mundo!', 1)
```

Para agregar una nueva celda próxima a él, con texto centrado y luego ir a la siguiente línea, 
haríamos: 

```python
pdf.cell(60, 10, 'Hecho con FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**Nota**: el salto de línea puede hacerse también con [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). Este 
método permite especificar adicionalmente la altura del salto. 

Finalmente, el documento es cerrado y guardado en la ruta provista usando 
[output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Sin ningún parámetro provisto, `output()` 
devuelve el búfer `bytearray` del PDF.

## Tutorial 2 - Encabezado, pie de página, salto de página e imagen ##

Aquí hay un ejemplo de dos páginas con encabezado, pie de página y logo: 

```python
{% include "../tutorial/tuto2.py" %}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto2.pdf)

Este ejemplo hace uso de los métodos [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) y 
[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) para procesar encabezados y pies de página. Estos 
son invocados automáticamente. Ellos ya existen en la clase FPDF pero no hacen nada, 
por lo tanto tenemos que extender la clase y sobreescribirlos. 

El logo es impreso con el método [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) especificando 
su esquina superior izquierda y su ancho. La altura es calculada automáticamente para 
respetar las proporciones de la imagen. 

Para imprimir el número de página, un valor nulo es pasado como ancho de celda. Esto significa 
que la celda deberá ser extendida hasta el margen derecho de la página; es útil para 
centrar texto. El número de página actual es devuelto por el método 
[page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no); respecto 
al número total de páginas, éste es obtenido mediante el valor especial `{nb}` 
que será sustituido al cerrar el documento (este valor especial puede ser cambiado con 
[alias_nb_pages()](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)). 
Nota el uso del método [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) que permite establecer 
la posición en una ubicación absoluta en la página, empezando desde arriba o desde 
abajo. 

Otra característica interesante es usada aquí: el salto de página automático. Tan pronto 
como una celda cruzaría el límite de la página (por defecto a 2 centímetros del borde 
inferior), un salto es realizado y la fuente es restaurada. Aunque el encabezado y 
pie de página tienen su propia fuente (`helvetica`), el cuerpo continúa en `Times`. 
Este mecanismo de restauración automática también se aplica a los colores y al ancho de la línea. 
El límite que dispara los saltos de página puede establecerse con 
[set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).


## Tutorial 3 - Saltos de línea y colores ##

Continuemos con un ejemplo que imprime párrafos justificados. También 
ilustra el uso de colores.

```python
{% include "../tutorial/tuto3.py" %}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto3.pdf)

[Texto de Julio Verne](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

El método [get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) permite determinar 
la longitud de una cadena de texto en la fuente actual, usada aquí para calcular la 
posición y el ancho del marco que rodea al título. Los colores son establecidos 
(vía [set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), 
[set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) y 
[set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)) y el grosor de la línea es establecido 
a 1 mm (contra 0.2 por defecto) con 
[set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). Finalmente, emitimos la celda (el 
último parámetro en `True` para indicar que el fondo debe ser rellenado). 

El método usado para imprimir párrafos es [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell). El texto es justificado por defecto. 
Cada vez que una línea alcanza el extremo derecho de la celda o un caracter de retorno de línea (`\n`) es encontrado, 
un salto de línea es emitido y una nueva celda es automáticamente creada bajo la actual. 
Un salto automático es realizado en la ubicación del espacio o guión suave (`\u00ad`) más cercano antes del límite derecho.
Un guión suave será reemplazado por un guión normal cuando un salto de línea se dispara, e ignorado en cualquier otro caso.

Dos propiedades del documento son definidas: el título 
([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) y el autor 
([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Las propiedades pueden ser vistas de dos formas. 
La primera es abrir el documento directamente con Acrobat Reader, ir al menú Archivo 
y elegir la opción Propiedades del Documento. La segunda, también disponible desde el 
complemento, es hacer clic derecho y seleccionar Propiedades del documento.

## Tutorial 4 - Múltiples columnas ##

Este ejemplo es una variante del anterior, mostrando cómo poner el texto en múltiples columnas.

```python
{% include "../tutorial/tuto4.py" %}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto4.pdf)

[Texto de Julio Verne](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

La diferencia clave con el tutorial anterior es el uso de los métodos 
[accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) y set_col.

Utilizando el método [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break), una vez 
la celda cruce el límite inferior de la página, éste comprobará el número de la columna actual. Si 
es menor que 2 (decidimos dividir la página en tres columnas) éste invocará al método set_col, 
incrementando el número de columna y alterando la posición de la siguiente columna tal que el texto pueda continuar aquí.

Una vez el límite inferior de la tercera columna es alcanzado, el 
método [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) se reiniciará y 
volverá a la primera columna, desencadenando un salto de página.

## Tutorial 5 - Creando tablas ##

```python
{% include "../tutorial/tuto5.py" %}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Archivo de texto con países](https://github.com/py-pdf/fpdf2/raw/master/tutorial/countries.txt)

_⚠️ This section has changed a lot and requires a new translation: <https://github.com/py-pdf/fpdf2/issues/267>_

English versions:

* [Tuto 5 - Creating Tables](https://py-pdf.github.io/fpdf2/Tutorial.html#tuto-5-creating-tables)
* [Documentation on tables](https://py-pdf.github.io/fpdf2/Tables.html)

## Tutorial 6 - Creando enlaces y combinando estilos de texto ##

Este tutorial explicará varias formas de insertar enlaces dentro de un documento pdf, 
al igual que cómo agregar enlaces a recursos externos.

También mostrará muchas formas en que podemos usar los diferentes estilos de texto 
(negrita, cursiva, subrayado) dentro del mismo texto.

```python
{% include "../tutorial/tuto6.py" %}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto6.pdf) -
[Logo de fpdf2](https://raw.githubusercontent.com/py-pdf/fpdf2/master/docs/fpdf2-logo.png)

El nuevo método mostrado aquí para imprimir texto es
 [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
. Es muy similar a
 [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
, siendo las diferencias clave:
 
 - El final de línea está en el margen derecho y la siguiente línea comienza en el margen
  izquierdo.
 - La posición actual se desplaza al final del texto.

El método por tanto nos permite escribir un trozo de texto, alterar el estilo de la fuente,
 y continuar desde el lugar exacto donde quedamos.
Por otro lado, su principal desventaja es que no podemos justificar el texto como
 hacemos con el
 método
 [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell).

En la primera página del ejemplo usamos
 [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
 para este propósito. El comienzo de la oración está escrito usando texto en estilo
 regular, luego usando el método
 [set_font()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
 cambiamos a subrayado y terminamos la oración.

Para agregar un enlace interno apuntando a la segunda página, usamos el método
 [add_link()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link)
, el cual crea un área clicable a la que nombramos "link" que redirige a
 otro lugar dentro del documento.

Para crear un enlace externo usando una imagen, usamos
 [image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image)
. El método tiene la
 opción de recibir un enlace como uno de sus argumentos. El enlace puede ser tanto interno
 como externo.

Como alternativa, otra opción para cambiar el estilo de fuente y agregar enlaces es
 usar el método `write_html()`. Este es un analizador de html que permite agregar texto,
 cambiar el estilo de fuente y agregar enlaces usando html.
