# Vodič #

Metode – popolna dokumentacija: [`fpdf.FPDF` API doc](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

## Vodič 1 - Minimalni primer ##

Začnimo s klasičnim primerom:

```python
{% include "../tutorial/tuto1.py" %}
```

[Rezultatni PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto1.pdf)

Po vključitvi datoteke knjižnice ustvarimo objekt `FPDF`. Konstruktor
[FPDF](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF) se tu uporablja
z privzetimi vrednostmi: strani so v pokončni postavitvi A4 in merska enota je
milimeter. To bi lahko eksplicitno določili z:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

Možno je nastaviti PDF v ležeči način (`L`) ali uporabiti druge formate strani (npr.
`Letter` in `Legal`) ter merske enote (`pt`, `cm`, `in`).

Zaenkrat ni strani, zato jo moramo dodati z
[add_page](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). Izvor je v zgornjem levem kotu, trenutni
položaj pa je privzeto nastavljen na 1 cm od robov; robove lahko spremenimo z
[set_margins](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins).

Pred tiskanjem besedila je obvezno izbrati pisavo z
[set_font](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), sicer
dokument ne bi bil veljaven. Izberemo Helvetica krepko 16:

```python
pdf.set_font('Helvetica', style='B', size=16)
```

Določimo lahko tudi ležečo (`I`), podčrtano (`U`) ali običajno pisavo (prazno niz
ali katerokoli kombinacijo). Velikost pisave je izražena v pikah, ne v milimetrih
(ali drugi merski enoti); to je edina izjema. Druge vgrajene pisave so `Times`,
`Courier`, `Symbol` in `ZapfDingbats`.

Zdaj lahko natisnemo celico z
[cell](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). Celica je
pravokotno področje, morda z okvirjem, ki vsebuje nekaj besedila. Izriše se na
trenutnem položaju. Določimo njene dimenzije, besedilo (poravnano ali centrirano),
ali naj se narišejo obrobe in kam se trenutni položaj premakne po tem (na desno,
spodaj ali na začetek naslednje vrstice). Da bi dodali okvir, naredimo to:

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

Za dodajanje nove celice poleg nje s centriranim besedilom in premik v novo vrstico:

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**Opomba**: prelom vrstice lahko izvedemo tudi z
[ln](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). Ta metoda omogoča
tudi določitev višine preloma.

Nazadnje je dokument zaprt in shranjen pod navedeno potjo datoteke z uporabo
[output](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Brez
navedenega parametra `output()` vrne PDF `bytearray` medpomnilnik.

## Vodič 2 - Glava, noga, prelom strani in slika ##

Tukaj je primer dvostranskega dokumenta z glavo, nogo in logotipom:

```python
{% include "../tutorial/tuto2.py" %}
```

[Rezultatni PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto2.pdf)

Ta primer uporablja [header](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.header) in
[footer](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) za obdelavo
glav in nog dokumenta. Kličeta se samodejno. V osnovnem razredu `FPDF` že obstajata,
a vendar ne izvajata ničesar, zato je razred potrebno razširiti in metodi prepisati.

Logotip je natisnjen z [image](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image),
kjer določimo zgornji levi kot in širino. Višina se izračuna samodejno, da ostanejo
razmerja slike nespremenjena.

Za izpis številke strani se kot širino celice poda `None`. To pomeni, da se celica
raztegne do desnega roba strani; to je priročno za centriranje besedila. Trenutno
številko strani vrne [page_no](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no),
medtem ko skupno število strani dobimo z uporabo posebne vrednosti `{nb}`, ki se
nadomesti ob zapiranju dokumenta (to vrednost lahko spremenimo z
[alias_nb_pages()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)).
Omeniti velja tudi uporabo [set_y](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y),
ki omogoča nastavitev navpičnega položaja na absolutno lokacijo strani, pričenši
na vrhu ali dnu.

Zanimiva možnost, uporabljena tukaj, je samodejno prelamljanje strani. Takoj, ko bi
celica presegla dno strani (privzeto 2 centimetra od roba), se ustvari nov prelom
strani in pisava se povrne na prejšnje stanje. Čeprav glava in noga uporabljata
svojo pisavo (`helvetica`), se v telesu uporabi `Times`. Ta mehanizem samodejnega
obnavljanja velja tudi za barve in širino črte. Mejo, ki sproži prelom strani,
lahko nastavimo z [set_auto_page_break](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).

## Vodič 3 - Prelomi vrstic in barve ##

Nadaljujmo s primerom, ki natisne poravnane odstavke in ilustrira rabo barv.

```python
{% include "../tutorial/tuto3.py" %}
```

[Rezultatni PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne besedilo](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

[get_string_width](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) omogoča določitev dolžine
niza v trenutni pisavi, kar nam pomaga izračunati položaj in širino okvira, ki
obdaja naslov. Nato se nastavijo barve preko
[set_draw_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color),
[set_fill_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) in
[set_text_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color),
pa tudi debelina črte z
[set_line_width](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width)
na 1 mm (privzeta je 0,2 mm). Na koncu izpišemo celico (zadnji parameter `True`
nakazuje, da se okno obarva).

Metoda, uporabljena za tiskanje odstavkov, je
[multi_cell](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell).
Besedilo je privzeto poravnano. Vsakič, ko vrstica doseže desni rob celice ali
se pojavi znak za prelom vrstice (`\n`), se vrstice prelomi in nova celica se
ustvari pod trenutnim položajem. Samodejni prelom se izvrši na lokaciji
najbližjega presledka ali mehke črtice (`\u00ad`) pred desnim robom. Mehka
črtica se ob prelomu vrstice spremeni v običajno črtico, sicer pa se ignorira.

Dve lastnosti dokumenta sta določeni: naslov
[set_title](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title) in
avtor [set_author](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author).
Do njih se lahko dostopa na dva načina: dokument se odpre neposredno v Acrobat
Readerju in v meniju File izbere Document Properties ali pa se z desno tipko
miške izbere Document Properties.

## Vodič 4 - Večstolpčno besedilo ##

Ta primer je različica prejšnjega, prikazuje, kako razdeliti besedilo v več stolpcev.

```python
{% include "../tutorial/tuto4.py" %}
```

[Rezultatni PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne besedilo](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

Ključna razlika od prejšnjega vodiča je uporaba metode
[`text_columns`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.text_column).
Zbira vse besedilo, po potrebi po delih, in ga razdeli čez zahtevano število
stolpcev, pri čemer samodejno vstavi prelome strani, kjer je to potrebno. Upoštevajte,
da dokler je `TextColumns` instanca aktivna kot upravljavec konteksta, lahko
spreminjate slog besedila in druge lastnosti pisave, te spremembe pa bodo
veljale samo znotraj tega konteksta. Ko je enkrat zaprt, se obnovijo prejšnje
nastavitve.

## Vodič 5 - Ustvarjanje tabel ##

Ta vodič bo razložil, kako ustvariti dve različni tabeli, da prikaže, kaj je
mogoče doseči z nekaj osnovnimi prilagoditvami.

```python
{% include "../tutorial/tuto5.py" %}
```

[Rezultatni PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Countries CSV data](https://github.com/py-pdf/fpdf2/raw/master/tutorial/countries.txt)

Prvi primer je izveden na najbolj osnovni način, saj se podatki predajo metodi
[`FPDF.table()`](https://py-pdf.github.io/fpdf2/Tables.html). Rezultat je precej
preprost, vendar hitro dosegljiv.

Druga tabela prinaša nekaj izboljšav: barve, omejeno širino tabele, zmanjšano
višino vrstic, centrirane naslove, stolpce s prilagojeno širino, desno poravnane
številke ... Poleg tega so odstranjene vodoravne črte. Dosegli smo to z izbiro
`borders_layout` med razpoložljivimi vrednostmi:
[`TableBordersLayout`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TableBordersLayout).

## Vodič 6 - Ustvarjanje povezav in mešanje slogov besedila ##

Ta vodič bo razložil več načinov, kako vstaviti povezave v PDF dokument,
pa tudi, kako dodati povezave na zunanje vire.

Poleg tega bo pokazal več načinov uporabe različnih slogov besedila
(krepko, ležeče, podčrtano) znotraj istega besedila.

```python
{% include "../tutorial/tuto6.py" %}
```

[Rezultatni PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://py-pdf.github.io/fpdf2/fpdf2-logo.png)

Nova metoda, prikazana tukaj za izpis besedila, je
[write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write).
Zelo je podobna metodi
[multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell),
vendar sta tu dve ključni razliki:

- Konec vrstice je na desnem robu, naslednja vrstica se začne na levem robu.
- Trenutni položaj se premakne na konec izpisanega besedila.

Ta metoda nam tako omogoča napisati kos besedila, spremeniti slog pisave in
nadaljevati natanko tam, kjer smo ostali. Njena glavna slabost pa je, da ne
omogoča poravnavanja besedila (justify) tako kot
[multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell).

Na prvi strani primera smo za ta namen uporabili
[write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write).
Začetek stavka je bil napisan z običajnim slogom pisave, nato smo z
[set_font()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
preklopili na podčrtano in dokončali stavek.

Za dodajanje notranje povezave, ki kaže na drugo stran, smo uporabili
[add_link()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link),
ki ustvari klikabilno območje z imenom "link", ki vodi na drugo stran
v dokumentu.

Za izdelavo zunanje povezave z uporabo slike smo uporabili
[image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image).
Metoda ima parameter link, ki omogoča nastavitev povezave (lahko je interna
ali eksterna).

Kot alternativa je na voljo še en način za spreminjanje sloga pisave in
vstavljanje povezav: metoda `write_html()`, ki je HTML razčlenjevalnik in
omogoča vstavljanje besedila, spreminjanje sloga pisave in povezav
preko HTML kode.

