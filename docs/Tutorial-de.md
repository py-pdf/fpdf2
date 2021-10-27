# Anleitung #

Versión en español: [Tutorial-es](Tutorial-es.md)

हिंदी संस्करण: [Tutorial-हिंदी](Tutorial-हिंदी.md)

Vollständige Dokumentation der Methoden: [`fpdf.FPDF` API doc](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Lektion 1 - Minimalbeispiel ##

Beginnen wir mit dem Klassiker::

```python
{% include "../tutorial/tuto1.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

Nachdem wir die Bibliothek eingebunden haben, erstellen wir ein `FPDF` Objekt. Der 
[`FPDF`](fpdf/fpdf.html#fpdf.fpdf.FPDF) Konstruktor wird hier mit den Standardwerten verwendet: Die Seiten sind im A4-Hochformat und die Maßeinheit ist Millimeter.

Dies hätte auch explizit mit angegeben werden können:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```
Es ist auch möglich, die PDF-Datei im Querformat zu erstellen (`L`) sowie andere Seitenformate
(`Letter` und `Legal`) und Maßeinheiten (`pt`, `cm`, `in`) zu verwenden.

Bisher haben wir dem Dokument noch keine Seite hinzugefügt. Das können wir mit [`add_page`](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). nachholen.
Der Ursprung liegt in der oberen linken Ecke und die
aktuelle Position ist standardmäßig 1 cm von den Rändern entfernt. Die Randabstände können
können mit [`set_margins`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins) angespasst werden.

Bevor wir Text hinzufügen können, müssen wir zuerst mit [`set_font`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) eine Schriftart auswählen, um ein gültiges Dokument zu erzeugen.
Wir wählen Helvetica, fett in Schriftgröße 16:

```python
pdf.set_font('helvetica', 'B', 16)
```

Wir hätten auch kursiv mit `I`, unterstrichen mit `U` oder eine "normale" Darstellung
durch die Übergabe einer leeren Zeichenkette wählen können. Beliebige Kombinationen der drei Werte sind zulässig. Beachte, dass die Schriftgröße in
Punkten und nicht in Millimetern (oder einer anderen durch den Benutzer bei der Erstellung mit `unit=` festgelegten Maßeinheit) angegeben wird. 
Dies ist die einzige Ausnahme vom Grundsatz, dass immer die durch den Benutzer gewählte Maßeinheit bei der Verwendung von Maßangeben genutzt wird.
Die anderen eingebauten Schriftarten sind `Times`, `Courier`, `Symbol` und `ZapfDingbats`.

Wir können jetzt eine Zelle mit [`cell`](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) einfügen. Eine Zelle ist ein rechteckiger
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

**Anmerkung**: Der Zeilenumbruch kann auch mit [`ln`](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln) erfolgen. Diese
Methode erlaubt es, zusätzlich die Höhe des Umbruchs anzugeben.

Schließlich wird das Dokument mit [`output`](fpdf/fpdf.html#fpdf.fpdf.FPDF.output) geschlossen und unter dem angegebenen Dateipfad gespeichert. 
Ohne Angabe eines Parameters liefert `output()` den PDF `bytearray`-Puffer zurück.

## Lektion 2 - Kopfzeile, Fußzeile, Seitenumbruch und Bild ##

Hier ein zweiseitiges Beispiel mit Kopfzeile, Fußzeile und Logo:

```python
{% include "../tutorial/tuto2.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)

Dieses Beispiel verwendet die Methoden [`header`](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) und 
[`footer`](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer), um Kopf- und Fußzeilen zu verarbeiten. Sie
werden jeweils automatisch aufgerufen. Die Methoder 'header' direkt vor dem durch uns hinzugefügten Inhalt, die Methode 'footer' wenn die Bearbeitung einer Seite durch das Hinzufügen eienr weiteren Seite oder das Abspeichern des Dokuments abgeschlossen wird. 
Die Methoden existieren bereits in der Klasse FPDF, sind aber leer. Daher müssen wir die Klasse erweitern und sie überschreiben.

Das Logo wird mit der Methode [`image`](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) eingebunden, indem man seine linke obere Ecke und seine Breite angibt. 
Die Höhe wird automatisch berechnet, um die Bildproportionen beizubehalten.

Um die Seitenzahl einzufügenn, wird ein Nullwert als Breite der Zelle übergeben. Das bedeutet,
dass die Zelle bis zum rechten Rand der Seite reichen soll. Das ist besonders praktisch, um
Text zu zentrieren. Die aktuelle Seitenzahl wird durch
die Methode [`page_no`](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) zurückgegeben.
Die Gesamtseitenzahl wird mit Hilfe des speziellen Platzhalterwertes `{nb}` ermittelt,
der beim Schließen des Dokuments ersetzt wird (vorausgesetzt, du hast vorher 
[`alias_nb_pages`](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)) aufgerufen.
Beachte die Verwendung der Methode [`set_y`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y), mit der du die
Position an einer absoluten Stelle der Seite - von oben oder von
unten aus - setzen kannst. 

Eine weitere interessante Funktion wird hier ebenfalls verwendet: der automatische Seitenumbruch. Sobald
eine Zelle eine festgelegte Grenze in der Seite überschreitet (standardmäßig 2 Zentimeter vom unteren Rand), wird ein 
Umbruch durchgeführt und die Schrift auf der nächsten Seite automatisch beibehalten. Obwohl die Kopf- und
Fußzeile ihre eigene Schriftart (`Helvetica`) wählen, wird im Textkörper `Times` verwendet.
Dieser Mechanismus der automatischen Übernahme gilt auch für Farben und Zeilenbreite.
Der Grenzwert, der den Seitenumbruch auslöst, kann mit 
[`set_auto_page_break`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break) festgelegt werden .

## Lektion 3 - Zeilenumbrüche und Farben ##

Fahren wir mit einem Beispiel fort, das Absätze im Blocksatz ausgibt. Es demonstriert auch die Verwendung von Farben.

```python
{% include "../tutorial/tuto3.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

Die Methode [`get_string_width`](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) ermöglicht die Bestimmung
die Breite eines Strings in der aktuellen Schriftart. Das Beispiel nutzt sie zur Berechnung der
Position und die Breite des Rahmens, der den Titel umgibt. Anschließend werden mit [`set_draw_color`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), [`set_fill_color`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) und 
und [`set_text_color`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color) die Farben gesetzt und die Linienstärke mit [`set_line_width`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width)
auf 1 mm (Abweichend vom Standardwert von 0,2) festgelegt. Schließlich geben wir die Zelle aus 
(Der letzte Parameter True zeigt an, dass der Hintergrund gefüllt werden muss).

Zur Erstellung von Absätzen wir die Methode [`multi_cell`](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) genutzt.
Jedes Mal, wenn eine Zeile den rechten Rand der Zelle erreicht oder ein Zeilenumbruchzeichen im Text erkannt wird,
wird ein Zeilenumbruch durchgeführt und automatisch eine neue Zelle unterhalb der aktuellen Zelle erstellt. 
Der Text wird standardmäßig im Blocksatz ausgerichtet.

Es werden zwei Dokumenteigenschaften definiert: Titel 
([`set_title`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) und Autor 
([`set_author`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Dokumenteneigenschaften können auf zwei Arten eingesehen werden.
Man kann das Dokument mit dem Acrobat Reader öffnen und im Menü **Datei** die Option **Dokumenteigenschaften** auswählen. 
Alternativ kann man auch mit der rechten Maustaste auf das Dokument klicken und die Option Dokumenteigenschaften wählen.

## Lektion 4 - Mehrspaltiger Text ##

 Dieses Beispiel ist eine Abwandlung des vorherigen Beispiels und zeigt, wie man Text über mehrere Spalten verteilen kann.

```python
{% include "../tutorial/tuto4.py" %}
```

[Resultierendes PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne Text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

Der Hauptunterschied zur vorherigen Lektion ist die Verwendung der Methoden 
[`accept_page_break`](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) und `set_col`.

Wird [`accept_page_break`](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) verwedet, wird die aktuelle Spaltennummer überprüft, sobald 
die Zelle die untere Grenze der Seite überschreitet. Ist die Spaltennummer kleiner als 2 (wir haben uns entschieden, die Seite in drei Spalten zu unterteilen), wird die Methode `set_col` aufgerufen. Sie erhöht die Spaltennummer auf die nächsthöhere und setzt die Position auf den Anfang der nächsten Spalte, damit der Text dort fortgesetzt werden kann.

Sobald die untere Grenze der dritten Spalte erreicht ist, wird durch die Methode [`accept_page_break`](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) ein Seitenumbruch ausgelöst und die aktive Spalte zurückgesetzt.

## Lektion 5 - Tabellen erstellen ##

In dieser Lektion zeigen wir, wie man auf einfache Weise Tabellen erstellen kann.

Der Code wird drei verschiedene Tabellen erstellen, um zu zeigen, welche Effekte wir mit einigen einfachen Anpassungen erzielen können.

```python
{% include "../tutorial/tuto5.py" %}
```

[Resultierendes PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Länder](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/countries.txt)

Da eine Tabelle lediglich eine Sammlung von Zellen darstellt, ist es naheliegend, eine Tabelle aus den bereits bekannten Zellen aufzubauen.

Das erste Beispiel wird auf die einfachste Art und Weise realisiert: einfach gerahmte Zellen, die alle die gleiche Größe haben und linksbündig ausgerichtet sind. Das Ergebnis ist rudimentär, aber sehr schnell zu erzielen.

Die zweite Tabelle bringt einige Verbesserungen: Jede Spalte hat ihre eigene Breite,
 die Überschriften sind zentriert und die Zahlen rechtsbündig ausgerichtet. Außerdem wurden die horizontalen Linien
 entfernt. Dies geschieht mit Hilfe des Randparameters der Methode `cell()`, der angibt, welche Seiten der Zelle gezeichnet werden müssen. 
 Im Beispiel wählen wir die linke (L) und die rechte (R) Seite. Jetzt muss nur noch das Problem der horizontalen Linie
 zum Abschluss der Tabelle gelöst werden. Es gibt zwei Möglichkeiten, es zu lösen: In der Schleife prüfen, ob wir uns in der letzten Zeile befinden und den border Parameter als "LRB" übergeben oder, wie hier geschehen, die abschließende Zeile separat nach dem Durchlaufen der Schleife einfügen.

Die dritte Tabelle der zweiten sehr ähnlich, verwendet aber zusätzlich Farben. Füllung, Text und
 Linienfarben werden einfach mit den entsprechenden Methoden gesetzt. Eine wechselnde Färbung der Zeilen kann durch die abwechselnde Verwendung transparenter und gefüllter Zellen erreicht werden.



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
