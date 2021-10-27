# Anleitung #

Versión en español: [Tutorial-es](Tutorial-es.md)

हिंदी संस्करण: [Tutorial-हिंदी](Tutorial-हिंदी.md)

Vollständige Dokumentation der Methoden: [`fpdf.FPDF` API doc](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Anleitung 1 - Minimalbeispiel ##

Beginnen wir mit dem Klassiker::

```python
{% include "../tutorial/tuto1.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

Nachdem wir die Bibliothek eingebunden haben, erstellen wir ein `FPDF` Objekt. Der 
[FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) Konstruktor wird hier mit den Standardwerten verwendet: Die Seiten sind im A4-Hochformat und die Maßeinheit ist Millimeter.

Dies hätte auch explizit mit angegeben werden können:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```
Es ist auch möglich, die PDF-Datei im Querformat zu erstellen (`L`) sowie andere Seitenformate
(`Letter` und `Legal`) und Maßeinheiten (`pt`, `cm`, `in`) zu verwenden.

Bisher haben wir dem Dokument noch keine Seite hinzugefügt. Das können wir mit [add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). nachholen.
Der Ursprung liegt in der oberen linken Ecke und die
aktuelle Position ist standardmäßig 1 cm von den Rändern entfernt. Die Randabstände können
können mit [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins) angespasst werden.

Bevor wir Text hinzufügen können, müssen wir zuerst mit [set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) eine Schriftart auswählen, um ein gültiges Dokument zu erzeugen.
Wir wählen Helvetica, fett in Schriftgröße 16:

```python
pdf.set_font('helvetica', 'B', 16)
```

Wir hätten auch kursiv mit `I`, unterstrichen mit `U` oder eine normale Schriftart
durch die Übergabe einer leeren Zeichenkette wählen können. Beliebige Kombinationen der drei Werte sind zulässig. Beachte, dass die Schriftgröße in
Punkten und nicht in Millimetern (oder einer anderen durch den Benutzer bei der Erstellung mit `unit=` festgelegten Maßeinheit) angegeben wird. 
Dies ist die einzige Ausnahme vom Grundsatz, dass immer die durch den Benutzer gewählte Maßeinheit bei der Verwendung von Maßangeben genutzt wird.
Die anderen eingebauten Schriftarten sind `Times`, `Courier`, `Symbol` und `ZapfDingbats`.

Wir können jetzt eine Zelle mit [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) einfügen. Eine Zelle ist ein rechteckiger
Bereich, optional umrahmt, der Text enthält. Sie wird an der aktuellen Position gerendert. Wir können die Abmessungen, den Text (zentriert oder ausgerichtet), eine gewünschten Rahmung
und wohin sich die aktuelle Position nach der Zelle bewegt (nach rechts,
unten oder an den Anfang der nächsten Zeile) bestimmen. 

Um einen Rahmen hinzuzufügen, würden wir die Methode folgendermaßen einbinden:

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

Um eine neue Zelle mit zentriertem Text hinzuzufügen und anschließend in die nächste Zeile zu springen, können wir Folgendes schreiben:

```python
pdf.cell(60, 10, 'Powered by FPDF.', ln=1, align='C')
```

**Anmerkung**: Der Zeilenumbruch kann auch mit [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln) erfolgen. Diese
Methode erlaubt es, zusätzlich die Höhe des Umbruchs anzugeben.

Schließlich wird das Dokument mit [output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output) geschlossen und unter dem angegebenen Dateipfad gespeichert. 
Ohne Angabe eines Parameters liefert `output()` den PDF `bytearray`-Puffer zurück.

## Anleitung 2 - HKopfzeile, Fußzeile, Seitenumbruch und Bild ##

Hier ein zweiseitiges Beispiel mit Kopfzeile, Fußzeile und Logo:

```python
{% include "../tutorial/tuto2.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)

Dieses Beispiel verwendet die Methoden [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) und 
[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer), um Kopf- und Fußzeilen zu verarbeiten. Sie
werden jeweils automatisch aufgerufen. Die Methoden existieren bereits in der FPDF-Klasse, tun aber nichts,
daher müssen wir die Klasse erweitern und sie überschreiben.

Das Logo wird mit der Methode [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) eingebunden, indem man seine linke obere Ecke und seine Breite angibt. 
Die Höhe wird automatisch berechnet, um die Bildproportionen beizubehalten.

Um die Seitenzahl einzufügenn, wird ein Nullwert als Breite der Zelle übergeben. Das bedeutet,
dass die Zelle bis zum rechten Rand der Seite reichen soll. Das ist besonders praktisch, um
Text zu zentrieren. Die aktuelle Seitenzahl wird durch
die Methode [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) zurückgegeben.
Die Gesamtseitenzahl wird mit Hilfe des speziellen Platzhalterwertes `{nb}` ermittelt,
der beim Schließen des Dokuments ersetzt wird (vorausgesetzt, du hast vorher 
[alias_nb_pages](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)) aufgerufen.
Beachte die Verwendung der Methode [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y), mit der du die
Position an einer absoluten Stelle der Seite - von oben oder von
unten aus - setzen kannst. 

Eine weitere interessante Funktion wird hier ebenfalls verwendet: der automatische Seitenumbruch. Sobald
eine Zelle eine festgelegte Grenze in der Seite überschreitet (standardmäßig 2 Zentimeter vom unteren Rand), wird ein 
Umbruch durchgeführt und die Schrift auf der nächsten Seite automatisch beibehalten. Obwohl die Kopf- und
Fußzeile ihre eigene Schriftart (`Helvetica`) wählen, wird im Textkörper `Times` verwendet.
Dieser Mechanismus der automatischen Übernahme gilt auch für Farben und Zeilenbreite.
Der Grenzwert, der den Seitenumbruch auslöst, kann mit 
[set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break) festgelegt werden .

## Anleitung 3 - Zeilenumbrüche und Farben ##

Fahren wir mit einem Beispiel fort, das Absätze im Blocksatz ausgibt. Es demonstriertt auch die Verwendung von Farben.

```python
{% include "../tutorial/tuto3.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

Die Methode [get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) ermöglicht die Bestimmung
die Breite eines Strings in der aktuellen Schriftart. Das Beispiel nutzt sie zur Berechnung der
Position und die Breite des Rahmens, der den Titel umgibt. Anschließend werden mit [set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), [set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) und 
und [set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color) die Farben gesetzt und die Linienstärke mit [set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width)
auf 1 mm (Abweichend vom Standardwert von 0,2) festgelegt. Schließlich geben wir die Zelle aus 
(Der letzte Parameter True zeigt an, dass der Hintergrund gefüllt werden muss).

Zur Erstellung von Absätzen wir die Methode [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) genutzt.
Jedes Mal, wenn eine Zeile den rechten Rand der Zelle erreicht oder ein Zeilenumbruchzeichen im Text erkannt wird,
wird ein Zeilenumbruch durchgeführt und automatisch eine neue Zelle unterhalb der aktuellen Zelle erstellt. 
Der Text wird standardmäßig im Blocksatz ausgerichtet.

Es werden zwei Dokumenteigenschaften definiert: Titel 
([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) und Autor 
([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Dokumenteneigenschaften können auf zwei Arten eingesehen werden.
Man kann das Dokument mit dem Acrobat Reader öffnen und im Menü **Datei** die Option **Dokumenteigenschaften** auswählen. 
Alternativ Die zweite Möglichkeit, die auch über das
Plug-in, indem Sie mit der rechten Maustaste auf das Dokument klicken und die Option Dokumenteigenschaften wählen.








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
