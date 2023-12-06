# Handleiding #

Methoden volledige documentatie: [`fpdf.FPDF` API doc](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Tuto 1 - Minimaal voorbeeld ##

Eerste, het klassieke voorbeeld:

```python
{% include "../tutorial/tuto1.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto1.pdf)

Nadat u het bibliotheekbestand hebt toegevoegd, maakt u een `FPDF`-object. De
[FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) constructor wordt hier gebruikt met de standaardwaarden:
pagina's zijn in A4 staand en de maateenheid is millimeter. 
Het had expliciet vermeld kunnen worden met:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

Het is mogelijk om de PDF in landscape-modus (`L`) te zetten of om andere paginaformaten te gebruiken
(zoals `Letter` en `Legal`) en maateenheden (`pt`, `cm`, `in`).

Er is momenteel geen pagina, dus we moeten er een toevoegen 
[add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). De oorsprong bevindt zich in de linkerbovenhoek en de
de huidige positie wordt standaard op 1 cm van de randen geplaatst; de marges kunnen worden gewijzigd 
met [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins).

Voordat we tekst kunnen afdrukken, is het verplicht om een lettertype te selecteren 
[set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), anders zou het document ongeldig zijn.
Wij kiezen voor Helvetica bold 16:

```python
pdf.set_font('helvetica', 'B', 16)
```

We hadden cursief kunnen specificeren met `I`, onderstreept met `U` of een gewoon lettertype
met een lege string (of een combinatie daarvan). Houd er rekening mee dat de lettergrootte is opgegeven
punten, geen millimeters (of een andere gebruikerseenheid); het is de enige uitzondering.
De andere ingebouwde lettertypen zijn `Times`, `Courier`, `Symbol` en `ZapfDingbats`.

We kunnen nu een cel afdrukken met [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell).Een cel is een rechthoekig gebied,
eventueel omkaderd, dat wat tekst bevat. Het wordt weergegeven op de huidige positie. 
We specificeren de afmetingen, de tekst (gecentreerd of uitgelijnd), of er randen moeten worden getekend 
en waar de huidige positie daarnaheen beweegt (naar rechts, onder of naar het begin van de volgende regel). 
Om een frame toe te voegen, doen we dit:

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

Om er een nieuwe cel met gecentreerde tekst naast toe te voegen en naar de volgende regel te gaan, wij
zou doen:

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**Remark**: the line break can also be done with . This
method allows to specify in addition the height of the break.

Finally, the document is closed and saved under the provided file path using
. Without any parameter provided, `output()`
returns the PDF `bytearray` buffer.

**Let op!**: het regeleinde kan ook met [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). Dit
methode maakt het mogelijk om bovendien de hoogte van de pauze te specificeren.

Ten slotte wordt het document gesloten en opgeslagen onder het opgegeven bestandspad met behulp van
[output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Zonder dat er een parameter is opgegeven, wordt `output()`
retourneert de PDF `bytearray`-buffer.

## Tuto 2 - Koptekst, voettekst, pagina-einde en afbeelding ##

Hier is een voorbeeld van twee pagina's met koptekst, voettekst en logo:

```python
{% include "../tutorial/tuto2.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto2.pdf)

Dit voorbeeld maakt gebruik van de [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) en 
[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer)  methoden om paginakop- en voetteksten te verwerken. Zij
worden automatisch gebeld. Ze bestaan al in de FPDF-klasse, maar doen niets,
daarom moeten we de klasse uitbreiden en overschrijven.

Het logo wordt afgedrukt met de methode [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) door op te geven
de linkerbovenhoek en de breedte ervan. De hoogte wordt automatisch berekend respecteer de beeldverhoudingen.

Om het paginanummer af te drukken, wordt een nulwaarde doorgegeven als celbreedte. Het betekent
dat de cel zich moet uitstrekken tot aan de rechtermarge van de pagina; het is handig om
middelste tekst. Het huidige paginanummer wordt geretourneerd door
de [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) methode; wat betreft
het totale aantal pagina's wordt verkregen door middel van de speciale waarde `{nb}`
die wordt vervangen bij het sluiten van het document (deze speciale waarde kan worden gewijzigd door
[alias_nb_pages()](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)).

Let op het gebruik van de [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) methode waarmee
positie op een absolute locatie op de pagina, beginnend vanaf de bovenkant of de
onderkant.

Hier wordt een andere interessante functie gebruikt: het automatisch afbreken van pagina's. Zo snel
omdat een cel een limiet op de pagina zou overschrijden (op 2 centimeter van de onderkant door
standaard), wordt er een pauze uitgevoerd en wordt het lettertype hersteld. Hoewel de kop en
voettekst hun eigen lettertype selecteren (`helvetica`), de hoofdtekst gaat verder met `Times`.
Dit mechanisme van automatisch herstel is ook van toepassing op kleuren en lijndikte.
Met de limiet waarmee pagina-einden worden geactiveerd, kan worden ingesteld
[set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).


## Tuto 3 - Line breaks and colors ##

Laten we doorgaan met een voorbeeld waarin uitgevulde alinea's worden afgedrukt. Het ook
illustreert het gebruik van kleuren.

```python
{% include "../tutorial/tuto3.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne text](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

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
Text is justified by default.
Each time a line reaches the right extremity of the cell or a carriage return character (`\n`) is met,
a line break is issued and a new cell automatically created under the current one.
An automatic break is performed at the location of the nearest space or soft-hyphen (`\u00ad`) character before the right limit.
A soft-hyphen will be replaced by a normal hyphen when triggering a line break, and ignored otherwise.

Met de methode [get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) kunt u bepalen
de lengte van een string in het huidige lettertype, die hier wordt gebruikt om de
positie en de breedte van het kader rond de titel. Vervolgens worden de kleuren ingesteld
(via [set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color),
[set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) en
[set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)) en de dikte van de lijn is ingesteld
tot 1 mm (standaard tegen 0,2) met
[set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). Ten slotte voeren we de cel uit (de
laatste parameter op true geeft aan dat de achtergrond moet worden gevuld).

De methode die wordt gebruikt om de alinea's af te drukken is [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell). 
Tekst wordt standaard uitgevuld. Elke keer dat een regel het rechteruiteinde van de cel bereikt of een regelterugloopteken (`\n`) wordt tegengekomen,
er wordt een regeleinde weergegeven en er wordt automatisch een nieuwe cel aangemaakt onder de huidige.
Er wordt automatisch een pauze uitgevoerd op de locatie van de dichtstbijzijnde spatie of het zachte koppelteken (`\u00ad`) vóór de rechterlimiet.
Een zacht afbreekstreepje wordt vervangen door een normaal afbreekstreepje bij het activeren van een regeleinde, en wordt anders genegeerd.

Er worden twee documenteigenschappen gedefinieerd: de titel
([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) en de auteur
([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Eigenschappen kunnen op twee manieren worden bekeken.
Ten eerste opent u het document rechtstreeks met Acrobat Reader, ga naar het menu Bestand
en kies de optie Documenteigenschappen. De tweede, ook verkrijgbaar bij de
plug-in, is door met de rechtermuisknop te klikken en Documenteigenschappen te selecteren.


## Tuto 4 - Meerdere kolommen ##

Dit voorbeeld is een variant van het vorige en laat zien hoe u de tekst over meerdere kolommen kunt plaatsen.

```python
{% include "../tutorial/tuto4.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne text](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

Het belangrijkste verschil met de vorige tutorial is het gebruik van de 
[`text_columns`](fpdf/fpdf.html#fpdf.fpdf.FPDF.text_column) methode. 
Het verzamelt alle tekst, mogelijk in stappen, en verdeelt deze over het gevraagde aantal kolommen, waarbij 
indien nodig automatisch pagina-einden worden ingevoegd. Houd er rekening mee dat, hoewel de instantie `TextColumns`
actief is als contextmanager, tekststijlen en andere lettertype-eigenschappen kunnen worden gewijzigd. 
Deze wijzigingen zullen in de context worden opgenomen. Zodra het wordt gesloten, worden de vorige instellingen 
hersteld.


## Tuto 5 - Tabellen maken ##

In deze tutorial wordt uitgelegd hoe u twee verschillende tabellen kunt maken,
  om te demonstreren wat met enkele eenvoudige aanpassingen kan worden bereikt.

```python
{% include "../tutorial/tuto5.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Countries CSV data](https://github.com/py-pdf/fpdf2/raw/master/tutorial/countries.txt)

Het eerste voorbeeld wordt op de meest basale manier gerealiseerd, door gegevens toe te voeren [`FPDF.table()`](https://py-pdf.github.io/fpdf2/Tables.html). 
Het resultaat is rudimentair, maar zeer snel te verkrijgen.

De tweede tabel brengt enkele verbeteringen met zich mee: kleuren, beperkte tafelbreedte, verminderde lijnhoogte,
gecentreerde titels, kolommen met aangepaste breedtes, cijfers rechts uitgelijnd...
Bovendien zijn horizontale lijnen verwijderd.
Dit werd gedaan door een `borders_layout` te kiezen uit de beschikbare waarden:
 [`TableBordersLayout`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TableBordersLayout).

## Tuto 6 - Koppelingen maken en tekststijlen mixen ##

In deze tutorial worden verschillende manieren uitgelegd om links in een pdf-document in te voegen,
evenals het toevoegen van links naar externe bronnen.

Het laat ook verschillende manieren zien waarop we verschillende tekststijlen kunnen gebruiken,
(vet, cursief, onderstreept) binnen dezelfde tekst.

```python
{% include "../tutorial/tuto6.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://raw.githubusercontent.com/py-pdf/fpdf2/master/docs/fpdf2-logo.png)

De nieuwe methode die hier wordt getoond om tekst af te drukken is
 [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
. Het lijkt erg op
 [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
 , de belangrijkste verschillen zijn:

- Het einde van de regel bevindt zich aan de rechtermarge en de volgende regel begint aan de linkerkant marge.
- De huidige positie wordt naar het einde van de tekst verplaatst.

Met deze methode kunnen we dus een stuk tekst schrijven, de lettertypestijl wijzigen, en ga verder vanaf 
de exacte plek waar we gebleven waren. Aan de andere kant is het belangrijkste nadeel dat we de tekst 
niet kunnen rechtvaardigen wij doen met de
 [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
 methode.

Op de eerste pagina van het voorbeeld gebruikten we
 [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
 for this purpose. The beginning of the sentence is written in regular style
 text, then using the
 [set_font()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
 method, we switched to underline and finished the sentence.

Om een interne link toe te voegen die naar de tweede pagina verwijst, hebben we de
 [add_link()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link)
methode, die een klikbaar gebied creëert dat we "link" noemden en dat naar een andere pagina 
in het document verwijst.

Om de externe link te maken met behulp van een afbeelding, hebben we gebruikt
 [image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image)
. De methode heeft de mogelijkheid om een link als een van zijn argumenten door te geven. 
De link kan zowel intern als extern zijn.

Als alternatief is een andere optie om de lettertypestijl te wijzigen en links toe te voegen 
het gebruik van de methode `write_html()`. Het is een html-parser waarmee u tekst kunt toevoegen, 
de lettertypestijl kunt wijzigen en links kunt toevoegen met behulp van html.
