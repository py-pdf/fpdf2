# Kurzanleitung #

Vollständige Dokumentation der Methoden: [`fpdf.FPDF` API doc](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Lektion 1 - Minimalbeispiel ##

Beginnen wir mit dem Klassiker:

```python
{% include "../tutorial/tuto1.py" %}
```

[Erzeugtes PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

Nachdem wir die Bibliothek eingebunden haben, erstellen zuerst wir ein `FPDF` Objekt. Der 
[`FPDF`](fpdf/fpdf.html#fpdf.fpdf.FPDF) Konstruktor wird hier mit den Standardwerten verwendet: Das Seitenformat wird auf A4-Hochformat gesetzt und als Maßeinheit  Millimeter festgelegt.

Diese Werte hätten wir auch explizit angegeben können:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```
Es ist auch möglich, eine PDF-Datei im Querformat zu erstellen (`L`), sowie andere Seitenformate
(`Letter` und `Legal`) und Maßeinheiten (`pt`, `cm`, `in`) zu verwenden.

Bisher haben wir dem Dokument noch keine Seite hinzugefügt. Um eine Seite hinzuzufügen, verwenden wir [`add_page`](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page).
Der Ursprung der Koordinaten liegt in der oberen linken Ecke und die aktuelle Schreibposition ist standardmäßig jeweils 1 cm von den Rändern entfernt. Diese Randabstände können mit [`set_margins`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins) angespasst werden.

Bevor wir Text hinzufügen können, müssen wir zuerst mit [`set_font`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) eine Schriftart festlegen, um ein gültiges Dokument zu erzeugen.
Wir wählen Helvetica, fett in Schriftgröße 16 pt:

```python
pdf.set_font('helvetica', 'B', 16)
```

Anstelle von `B` hätten wir mit `I` kursiv , `U` unterstichen oder durch die Übergabe einer leeren Zeichenkette einen "normale" Textstil wählen können. Beliebige Kombinationen der drei Werte sind zulässig. Beachte, dass die Schriftgröße in Punkt und nicht in Millimetern (oder einer anderen durch den Benutzer bei der Erstellung mit `unit=` festgelegten Maßeinheit) angegeben wird. 
Dies ist die einzige Ausnahme vom Grundsatz, dass immer die durch den Benutzer gewählte Maßeinheit bei der Festlegung von Positions- oder Größenangaben genutzt wird. Neben `Helvetica` stehen `Times`, `Courier`, `Symbol` und `ZapfDingbats` als Standardschriftarten zur Verfügung.

Wir können jetzt eine erste Textzelle mit [`cell`](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) einfügen. Eine Zelle ist ein rechteckiger
Bereich - optional umrahmt - der Text enthalten kann. Sie wird an der jeweils aktuellen Schreibposition gerendert. Wir können die Abmessungen der Zelle, den Text und dessen Formatierung (zentriert oder ausgerichtet), einen ggf. gewünschten Rahmen und die Festlegung der neuen Schreibposition nach dem Schreiben der Zelle (rechts, unten oder am Anfang der nächsten Zeile) bestimmen. 

Um einen Rahmen hinzuzufügen, würden wir die Methode folgendermaßen einbinden:

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

Um eine neue Zelle mit zentriertem Text hinzuzufügen und anschließend in die nächste Zeile zu springen, können wir Folgendes schreiben:

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
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

[Erzeugtes PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)

Dieses Beispiel verwendet die Methoden [`header`](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) und 
[`footer`](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer), um Kopf- und Fußzeilen zu verarbeiten. Sie
werden jeweils automatisch aufgerufen. Die Methode 'header' direkt nach dem Hinzugügen einer neuen Seite, die Methode 'footer' wenn die Bearbeitung einer Seite durch das Hinzufügen einer weiteren Seite oder das Abspeichern des Dokuments abgeschlossen wird. 
Die Methoden existieren bereits in der Klasse FPDF, sind aber leer. Um sie zu nutzen, müssen wir die Klasse erweitern und sie überschreiben.

Das Logo wird mit der Methode [`image`](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) eingebunden, und auf der Seite durch die Angabe der Position der linken oberen Ecke und die gewünschte Bildbreite platziert. Die Höhe wird automatisch berechnet, um die Proportionen des Bildes zu erhalten.

Um die Seitenzahl einzufügenn, übergeben wir zuerst der Zelle einen Nullwert als Breite der Zelle. Das bedeutet,
dass die Zelle bis zum rechten Rand der Seite reichen soll. Das ist besonders praktisch, um
Text zu zentrieren. Die aktuelle Seitenzahl wird durch
die Methode [`page_no`](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) ermittelt und in die Zelle geschrieben.
Die Gesamtseitenzahl wird mit Hilfe des speziellen Platzhalterwertes `{nb}` ermittelt,
der beim Schließen des Dokuments ersetzt wird aufgerufen.
Beachte die Verwendung der Methode [`set_y`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y), mit der du die
vertikale Schreibposition an einer absoluten Stelle der Seite - von oben oder von
unten aus - setzen kannst. 

Eine weitere interessante Funktion wird hier ebenfalls verwendet: der automatische Seitenumbruch. Sobald
eine Zelle eine festgelegte Grenze in der Seite überschreitet (standardmäßig 2 Zentimeter vom unteren Rand), wird ein 
Seitenumbruch durchgeführt und die Einstellungen der gewahlten Schrift auf der nächsten Seite automatisch beibehalten. Obwohl die Kopf- und
Fußzeilen ihre eigene Schriftart (`Helvetica`) wählen, wird im Textkörper `Times` verwendet.
Dieser Mechanismus der automatischen Übernahme der Einstellungen nach Seitenumbruch gilt auch für Farben und Zeilenbreite.
Der Grenzwert, der den Seitenumbruch auslöst, kann mit [`set_auto_page_break`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break) festgelegt werden .

## Lektion 3 - Zeilenumbrüche und Farben ##

Fahren wir mit einem Beispiel fort, das Absätze im Blocksatz ausgibt. Es demonstriert auch die Verwendung von Farben.

```python
{% include "../tutorial/tuto3.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

Die Methode [`get_string_width`](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) ermöglicht die Bestimmung
die Breite des übergebenen Textes in der aktuellen Schriftart. Das Beispiel nutzt sie zur Berechnung der
Position und der Breite des Rahmens, der den Titel umgibt. Anschließend werden die Farben mit [`set_draw_color`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), [`set_fill_color`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) und 
und [`set_text_color`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color) gesetzt und die Linienstärke mit [`set_line_width`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width) auf 1 mm (Abweichend vom Standardwert von 0,2) festgelegt. Schließlich geben wir die Zelle aus 
(Der letzte Parameter True zeigt an, dass der Hintergrund gefüllt werden muss).

Zur Erstellung von Absätzen wir die Methode [`multi_cell`](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) genutzt.
Jedes Mal, wenn eine Zeile den rechten Rand der Zelle erreicht oder ein Zeilenumbruchzeichen `\\n` im Text erkannt wird,
wird ein Zeilenumbruch durchgeführt und automatisch eine neue Zelle unterhalb der aktuellen Zelle erstellt. 
Der Text wird standardmäßig im Blocksatz ausgerichtet.

Es werden zwei Dokumenteigenschaften definiert: Titel 
([`set_title`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) und Autor 
([`set_author`](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Dokumenteneigenschaften können auf zwei Arten eingesehen werden.
Man kann das Dokument mit dem Acrobat Reader öffnen und im Menü **Datei** die Option **Dokumenteigenschaften** auswählen. 
Alternativ kann man auch mit der rechten Maustaste auf das Dokument klicken und die Option Dokumenteigenschaften wählen.

## Lektion 4 - Mehrspaltiger Text ##

 Dieses Beispiel ist eine Abwandlung des vorherigen Beispiels und zeigt, wie sich Text über mehrere Spalten verteilen lässt.

```python
{% include "../tutorial/tuto4.py" %}
```

[Erzeugtes PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne Text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

Der Hauptunterschied zur vorherigen Lektion ist die Verwendung der Methoden 
[`accept_page_break`](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) und `set_col`.

Wird [`accept_page_break`](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) verwendet, wird die aktuelle Spaltennummer überprüft, sobald 
die Zelle den zur Auslösung eines Seitenumbruchs festgelegten Abstand zum unteren Seitenrand (Standard 2cm) überschreitet. Ist die Spaltennummer kleiner als 2 (wir haben uns entschieden, die Seite in drei Spalten zu unterteilen), wird die Methode `set_col` aufgerufen. Sie erhöht die Spaltennummer auf die nächsthöhere und setzt die Schreibposition auf den Anfang der nächsten Spalte, damit der Text dort fortgesetzt werden kann.

Sobald det Text der dritten den oben beschriebenen Abstand zum Seitenende erreicht, wird durch die Methode [`accept_page_break`](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) ein Seitenumbruch ausgelöst und die aktive Spalte sowie Schreibposition zurückgesetzt.

## Lektion 5 - Tabellen erstellen ##

In dieser Lektion zeigen wir, wie man auf einfache Weise Tabellen erstellen kann.

Der Code wird drei verschiedene Tabellen erstellen, um zu zeigen, welche Effekte wir mit einigen einfachen Anpassungen erzielen können.

```python
{% include "../tutorial/tuto5.py" %}
```

[Erzeugtes PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Länder](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/countries.txt)

Da eine Tabelle lediglich eine Sammlung von Zellen darstellt, ist es naheliegend, eine Tabelle aus den bereits bekannten Zellen aufzubauen.

Das erste Beispiel wird auf die einfachste Art und Weise realisiert. Einfach gerahmte Zellen, die alle die gleiche Größe haben und linksbündig ausgerichtet sind. Das Ergebnis ist rudimentär, aber sehr schnell zu erzielen.

Die zweite Tabelle bringt einige Verbesserungen: Jede Spalte hat ihre eigene Breite,
 die Überschriften sind zentriert und die Zahlen rechtsbündig ausgerichtet. Außerdem wurden die horizontalen Linien
 entfernt. Dies geschieht mit Hilfe des Randparameters der Methode `cell()`, der angibt, welche Seiten der Zelle gezeichnet werden müssen. 
 Im Beispiel wählen wir die linke (L) und die rechte (R) Seite. Jetzt muss nur noch das Problem der horizontalen Linie
 zum Abschluss der Tabelle gelöst werden. Es gibt zwei Möglichkeiten, es zu lösen: In der Schleife prüfen, ob wir uns in der letzten Zeile befinden und dann "LRB" als Rahmenparameter übergeben oder, wie hier geschehen, eine abschließende Zelle separat nach dem Durchlaufen der Schleife einfügen.

Die dritte Tabelle der zweiten sehr ähnlich, verwendet aber zusätzlich Farben. Füllung, Text und
 Linienfarben werden einfach mit den entsprechenden Methoden gesetzt. Eine wechselnde Färbung der Zeilen wird durch die abwechselnde Verwendung transparenter und gefüllter Zellen erreicht.

## Lektion 6 - Links erstellen und Textstile mischen ##

In dieser Lektion werden verschiedene Möglichkeiten der Erstellung interner und externer Links beschrieben.

Es wird auch gezeigt, wie man verschiedene Textstile (fett, kursiv, unterstrichen) innerhalb eines Textes verwenden kann.

```python
{% include "../tutorial/tuto6.py" %}
```

[Erzeugtes PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://raw.githubusercontent.com/PyFPDF/fpdf2/master/docs/fpdf2-logo.png)

Die hier gezeigte neue Methode zur Einbindung von Text lautet
 [`write()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write). Sie ähnelt der bereits bekannten
 [`multi_cell()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell). Die wichtigsten Unterschiede sind:

- Das Ende der Zeile befindet sich am rechten Rand und die nächste Zeile beginnt am linken
 Rand.
- Die aktuelle Position wird an das Textende gesetzt.

Die Methode ermöglicht es uns somit, zuerst einen Textabschnitt zu schreiben, dann den Schriftstil zu ändern
und genau an der Stelle fortzufahren, an der wir aufgehört haben.
Der größte Nachteil ist jedoch, dass die von [`multi_cell()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) bekannte Möglichkeit zur Festlegung der Textausrichtung fehlt.

Auf der ersten Seite des Beispiels nutzen wir [`write()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write).
Der Anfang des Satzes wird in "normalem" Stil geschrieben, dann mit der Methode
 [`set_font()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) auf Unterstreichung umgestellt und der Satz beendet.

Um einen internen Link hinzuzufügen, der auf die zweite Seite verweist, nutzen wir die Methode
 [`add_link()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link), die einen anklickbaren Bereich erzeugt, 
 den wir "link" nennen und der auf eine andere Stelle innerhalb des Dokuments verweist.

Um einen externen Link mit Hilfe eines Bildes zu erstellen, verwenden wir [`image()`](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image). Es besteht die Möglichkeit, der Methode ein Linkziel als eines ihrer Argumente zu übergeben. Der Link kann sowohl einer interner als auch ein externer sein.

Eine weitere Möglichkeit, den Schriftstil zu ändern und Links hinzuzufügen, stellt die Verwendung der Methode `write_html()` dar. Sie ist ein HTML-Parser, der das Hinzufügen von Text, Änderung des Schriftstils und Erstellen von Links mittels HTML ermöglicht.
