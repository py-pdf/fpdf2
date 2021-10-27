# Tutorial #

Versión en español: [Tutorial-es](Tutorial-es.md)

हिंदी संस्करण: [Tutorial-हिंदी](Tutorial-हिंदी.md)

Documentation complète des méthodes : [`fpdf.FPDF` API doc](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Tuto 1 - Exemple minimal ##

Commençons par un exemple classique :

```python
{% include "../tutorial/tuto1.py" %}
```

[PDF généré](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

Après avoir inclu la librairie, on créé un objet `FPDF`. Le constructeur [FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) est utilisé avec ses valeurs par défaut : 
les pages sont en format portrait A4 et l'unité de mesure est le millimètre.
Cela peut également être spéficié de cette manière :

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

Il est possible de créer un PDF en format paysage (`L`) ou encore d'utiliser d'autres formats (par exemple `Letter` et `Legal`) et unités de mesure (`pt`, `cm`, `in`).

Il n'y a pas encore de page, il faut donc en créer une avec [add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). Le coin en haut à gauche correspond à l'origine, et le curseur (c'est-à-dire la position actuelle où l'on va afficher un élément) est placé par défaut à 1 cm des bords; les marges peuvent être modifiées avec [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins).

Avant de pouvoir afficher du texte, il faut obligatoirement choisir une police de caractères avec [set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), sinon le document sera invalide.
Choisissons Helvetica bold 16:

```python
pdf.set_font('helvetica', 'B', 16)
```

On aurait pu spécifier une police en italique avec `I`; soulignée avec `U` ou une police normale avec une chaine de caractères vide. Il est aussi possible de combiner les effets en combinant les caractères. Notez que la taille des caractères est à spécifier en points (pts), pas en millimètres (ou tout autre unité); c'est la seule exception.
Les autres polices fournies par défaut sont `Times`, `Courier`, `Symbol` et `ZapfDingbats`.

On peut maintenant afficher une cellule avec [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). Une cellule est une zone rectangulaire, avec ou sans cadre, qui contient du texte. Elle est affichée à la position actuelle du curseur. On spécifie ses dimensions, le texte (centré ou aligné), si y il a une bordure ou non, ainsi que la position du curseur après avoir affiché la cellule (s'il se déplace à droite, vers le bas ou au début de la ligne suivante). Pour ajouter un cadre, on utilise ceci :

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

Pour ajouter une nouvelle cellule avec un texte centré, et déplacer le curseur à la ligne suivante on utilise cela :

```python
pdf.cell(60, 10, 'Powered by FPDF.', ln=1, align='C')
```

**Remarque** : le saut de ligne peut aussi être fait avec [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). Cette méthode permet de spécifier la hauteur du saut.

Enfin, le document est sauvegardé à l'endroit spécifié en utilisant [output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Sans aucun paramètre, `output()` retourne le buffer `bytearray` du PDF.

## Tuto 2 - Header, footer, page break and image ##

Here is a two page example with header, footer and logo:

```python
{% include "../tutorial/tuto2.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)

This example makes use of the [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) and 
[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) methods to process page headers and footers. They
are called automatically. They already exist in the FPDF class but do nothing,
therefore we have to extend the class and override them.

The logo is printed with the [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) method by specifying
its upper-left corner and its width. The height is calculated automatically to
respect the image proportions.

To print the page number, a null value is passed as the cell width. It means
that the cell should extend up to the right margin of the page; it is handy to
center text. The current page number is returned by
the [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) method; as for
the total number of pages, it is obtained by means of the special value `{nb}`
which will be substituted on document closure (provided you first called 
[alias_nb_pages](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)).
Note the use of the [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) method which allows to set
position at an absolute location in the page, starting from the top or the
bottom.

Another interesting feature is used here: the automatic page breaking. As soon
as a cell would cross a limit in the page (at 2 centimeters from the bottom by
default), a break is performed and the font restored. Although the header and
footer select their own font (`helvetica`), the body continues with `Times`.
This mechanism of automatic restoration also applies to colors and line width.
The limit which triggers page breaks can be set with 
[set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).


## Tuto 3 - Line breaks and colors ##

Let's continue with an example which prints justified paragraphs. It also
illustrates the use of colors.

```python
{% include "../tutorial/tuto3.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

The [get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) method allows determining
the length of a string in the current font, which is used here to calculate the
position and the width of the frame surrounding the title. Then colors are set
(via [set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color),
[set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) and 
[set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)) and the thickness of the line is set
to 1 mm (against 0.2 by default) with
[set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). Finally, we output the cell (the
last parameter to true indicates that the background must be filled).

The method used to print the paragraphs is [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell).
Each time a line reaches the right extremity of the cell or a carriage return
character is met, a line break is issued and a new cell automatically created
under the current one. Text is justified by default.

Two document properties are defined: the title 
([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) and the author 
([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Properties can be viewed by two means.
First is to open the document directly with Acrobat Reader, go to the File menu
and choose the Document Properties option. The second, also available from the
plug-in, is to right-click and select Document Properties.

## Tuto 4 - Multi Columns ##

 This example is a variant of the previous one, showing how to lay the text across multiple columns.

```python
{% include "../tutorial/tuto4.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

The key difference from the previous tutorial is the use of the 
[accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) and the set_col methods.

Using the [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) method, once 
the cell crosses the bottom limit of the page, it will check the current column number. If it 
is less than 2 (we chose to divide the page in three columns) it will call the set_col method, 
increasing the column number and altering the position of the next column so the text may continue there.

Once the bottom limit of the third column is reached, the 
[accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) method will reset and go 
back to the first column and trigger a page break.

## Tuto 5 - Creating Tables ##

This tutorial will explain how to create tables easily.

The code will create three different tables to explain what
 can be achieved with some simple adjustments.

```python
{% include "../tutorial/tuto5.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Countries text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/countries.txt)

Since a table is just a collection of cells, it is natural to build one
 from them.

The first example is achieved in the most basic way possible: simple framed
 cells, all of the same size and left aligned. The result is rudimentary but
 very quick to obtain.

The second table brings some improvements: each column has its own width,
 titles are centered and figures right aligned. Moreover, horizontal lines have
 been removed. This is done by means of the border parameter of the Cell()
 method, which specifies which sides of the cell must be drawn. Here we want
 the left (L) and right (R) ones. Now only the problem of the horizontal line
 to finish the table remains. There are two possibilities to solv it: check
 for the last line in the loop, in which case we use LRB for the border
 parameter; or, as done here, add the line once the loop is over.

The third table is similar to the second one but uses colors. Fill, text and
 line colors are simply specified. Alternate coloring for rows is obtained by
 using alternatively transparent and filled cells.

## Tuto 6 - Creating links and mixing text styles ##

This tutorial will explain several ways to insert links inside a pdf document,
 as well as adding links to external sources.

 It will also show several ways we can use different text styles,
 (bold, italic, underline) within the same text.

```python
{% include "../tutorial/tuto6.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://raw.githubusercontent.com/PyFPDF/fpdf2/master/docs/fpdf2-logo.png)

The new method shown here to print text is
 [write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
. It is very similar to
 [multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
 , the key differences being:

- The end of line is at the right margin and the next line begins at the left
 margin.
- The current position moves to the end of the text.

The method therefore allows us to write a chunk of text, alter the font style,
 and continue from the exact place we left off.
On the other hand, its main drawback is that we cannot justify the text like
 we do with the
 [multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
 method.

In the first page of the example, we used
 [write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
 for this purpose. The beginning of the sentence is written in regular style
 text, then using the
 [set_font()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
 method, we switched to underline and finished the sentence.

To add an internal link pointing to the second page, we used the
 [add_link()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link)
 method, whch creates a clickable area which we named "link" that directs to
 another place within the document. On the second page, we used
 [set_link()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_link)
 to define the destination area for the link we just created.

To create the external link using an image, we used
 [image()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image)
. The method has the
 option to pass a link as one of its arguments. The link can be both internal
 or external.

As an alternative, another option to change the font style and add links is to
 use the `write_html()` method. It is an html parser, which allows adding text,
 changing font style and adding links using html.
