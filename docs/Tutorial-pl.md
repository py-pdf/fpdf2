# Tutorial #

Pełna dokumentacja metod: [`fpdf.FPDF` API doc](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Tuto 1 - Minimalny Przykład ##

Zacznijmy od klasycznego przykładu:

```python
{% include "../tutorial/tuto1.py" %}
```

[Plik wynikowy PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto1.pdf)

Po dołączeniu pliku biblioteki tworzymy obiekt `FPDF`. Używany jest tutaj konstruktor [FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) z domyślnymi wartościami: 
strony są w formacie A4 w pionie, a jednostką miary jest milimetr.
Można było to określić jawnie za pomocą:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

Możliwe jest ustawienie formatu PDF w trybie poziomym (`L`) lub użycie innych formatów stron.
(takich jak `Letter` i `Legal`) oraz jednostek miary (`pt`, `cm`, `in`).

Na razie nie ma strony, więc musimy ją dodać za pomocą 
[add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). Początek znajduje się w lewym górnym rogu, a bieżąca pozycja domyślnie ustawiona jest na 1 cm od krawędzi; marginesy można zmienić za pomocą [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins).

Zanim będziemy mogli drukować tekst, konieczne jest wybranie czcionki za pomocą 
[set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), w przeciwnym razie dokument będzie nieprawidłowy. Wybieramy czcionkę Helvetica pogrubioną o rozmiarze 16:

```python
pdf.set_font('helvetica', 'B', 16)
```

Można było określić kursywę za pomocą `I`, podkreślenie za pomocą `U` lub zwykłą czcionkę za pomocą pustego łańcucha (lub dowolnej kombinacji). Należy pamiętać, że rozmiar czcionki jest podany w punktach, a nie w milimetrach (lub innej jednostce użytkownika); jest to jedyny wyjątek. Inne wbudowane czcionki to `Times`, `Courier`, `Symbol` i `ZapfDingbats`.

Teraz możemy wydrukować komórkę za pomocą [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). Komórka to prostokątny obszar, ewentualnie obramowany, zawierający tekst. Jest renderowany w bieżącej pozycji. Określamy jej wymiary, jej tekst (wyśrodkowany lub wyrównany), czy powinny być rysowane ramki i gdzie przesunie się bieżąca pozycja po niej (w prawo, poniżej lub na początek następnego wiersza). Aby dodać ramkę, postępujemy tak:

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

Aby dodać obok niego nową komórkę z wyśrodkowanym tekstem i przejść do następnego wiersza, wykonalibyśmy:

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**Uwaga**: łamanie wiersza można również wykonać za pomocą [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). Ta metoda pozwala dodatkowo określić wysokość przerwy.

Na koniec dokument jest zamykany i zapisywany pod podaną ścieżką pliku za pomocą 
[output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Bez podanego parametru `output()`
zwraca bufor PDF `bytearray`.

## Tuto 2 - Nagłówek, stopka, podział strony i obraz ##

Oto przykład dwustronicowy z nagłówkiem, stopką i logo:

```python
{% include "../tutorial/tuto2.py" %}
```

[Plik wynikowy PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto2.pdf)

Ten przykład wykorzystuje metody [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) i 
[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) do przetwarzania nagłówków i stopek stron. Są one wywoływane automatycznie. Istnieją już w klasie FPDF, ale nic nie robią, dlatego musimy rozszerzyć klasę i je nadpisać.

Logo jest drukowane za pomocą metody [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image), która określa jego górny lewy róg i szerokość. Wysokość jest automatycznie obliczana, aby zachować proporcje obrazu.

Aby wydrukować numer strony, jako szerokość komórki przekazywana jest wartość null. Oznacza to, że komórka powinna rozciągać się do prawego marginesu strony; jest to przydatne do centrowania tekstu. Bieżący numer strony zwracany jest przez metodę [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no); Całkowita liczba stron jest uzyskiwana za pomocą specjalnej wartości `{nb}`, która zostanie zastąpiona przy zamykaniu dokumentu (tę wartość specjalną można zmienić za pomocą metody  
[alias_nb_pages()](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)).
Należy zwrócić uwagę na użycie metody [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y), która pozwala ustawić pozycję w dowolnym miejscu na stronie, zaczynając od góry lub od dołu.

Kolejną interesującą funkcją stosowaną tutaj jest automatyczne łamanie strony. Gdy tylko komórka przekroczy limit strony (domyślnie 2 centymetry od dołu), następuje łamanie i przywrócenie czcionki. Chociaż nagłówek i stopka wybierają własną czcionkę (`helvetica`), treść dokumentu jest kontynuowana czcionką `Times`.
Ten mechanizm automatycznego przywracania dotyczy również kolorów i grubości linii. 
Limit wywołujący łamanie strony można ustawić za pomocą metody 
[set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).


## Tuto 3 - Łamanie wierszy i kolory ##

Kontynuujmy przykładem drukowania wyjustowanych akapitów.
Ilustruje on również zastosowanie kolorów.

```python
{% include "../tutorial/tuto3.py" %}
```

[Plik wynikowy PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne text](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

Metoda [get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) pozwala określić długość łańcucha znaków w bieżącej czcionce. Używana jest tutaj do obliczenia pozycji i szerokości ramki otaczającej tytuł. Następnie ustawiane są kolory (za pomocą metod [set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color),
[set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) i
[set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)) oraz grubość linii na 1 mm (domyślnie jest to 0,2 mm) za pomocą metody
[set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). Na koniec wyprowadzana jest komórka (ostatni parametr ustawiony na true oznacza, że tło musi być wypełnione).

Metodą używaną do drukowania akapitów jest [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell). Text is justified by default.
Domyślnie tekst jest wyjustowany. Za każdym razem, gdy linia osiąga prawy koniec komórki lub napotkany zostanie znak nowej linii (`\n`),
następuje łamanie wiersza i automatyczne utworzenie nowej komórki pod bieżącą.
Automatyczne łamanie wiersza następuje w miejscu najbliższej spacji lub miękkiego łącznika (`\u00ad`) przed prawą krawędzią.
Miękki łącznik zostanie zastąpiony zwykłym łącznikiem podczas łamania wiersza, a w przeciwnym razie zostanie zignorowany.

W dokumencie definiowane są dwie właściwości: tytuł
([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title))  i autor 
([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Właściwości można wyświetlić na dwa sposoby. Pierwszy to bezpośrednie otwarcie dokumentu w programie Acrobat Reader, przejście do menu Plik i wybranie opcji Właściwości dokumentu. Drugi sposób, również dostępny z wtyczki, polega na kliknięciu prawym przyciskiem myszy i wybraniu opcji Właściwości dokumentu.

## Tuto 4 - Wiele kolumn ##

Ten przykład jest wariantem poprzedniego, pokazującym jak rozłożyć tekst na wiele kolumn.

```python
{% include "../tutorial/tuto4.py" %}
```

[Plik wynikowy PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne text](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

Główna różnica w stosunku do poprzedniego tutoriala polega na użyciu metody 
[`text_columns`](fpdf/fpdf.html#fpdf.fpdf.FPDF.text_column). 
Gromadzi ona cały tekst, możliwie w częściach, i rozdziela go na żądaną liczbę kolumn, automatycznie wstawiając łamanie strony w razie potrzeby. Należy zauważyć, że dopóki instancja `TextColumns` jest aktywna jako menedżer kontekstu, style tekstu i inne właściwości czcionki można zmieniać. Zmiany te będą ograniczone do kontekstu. Po jego zamknięciu zostaną przywrócone poprzednie ustawienia.


## Tuto 5 - Tworzenie tabel ##

W tym tutorialu omówione zostanie tworzenie dwóch różnych tabel,
aby pokazać, co można osiągnąć za pomocą prostych modyfikacji.

```python
{% include "../tutorial/tuto5.py" %}
```

[Plik wynikowy PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Dane CSV z krajami](https://github.com/py-pdf/fpdf2/raw/master/tutorial/countries.txt)

Pierwszy przykład przedstawia najprostszy sposób przekazania danych do funkcji [`FPDF.table()`](https://py-pdf.github.io/fpdf2/Tables.html). Wynik jest podstawowy, ale bardzo szybki do uzyskania.

Druga tabela zawiera pewne ulepszenia: kolory, ograniczona szerokość tabeli, zmniejszona wysokość linii,
 wyśrodkowane tytuły, kolumny o niestandardowych szerokościach, wyrównane do prawej cyfry...
 Ponadto usunięto linie poziome.
 Zrealizowano to poprzez wybranie `borders_layout` spośród dostępnych wartości:
 [`TableBordersLayout`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TableBordersLayout).

## Tuto 6 - Tworzenie linków i mieszanie stylów tekstu ##

W tym samouczku omówione zostaną różne sposoby wstawiania łączy w dokumencie PDF,
 a także dodawania łączy do źródeł zewnętrznych.

Pokaże również kilka sposobów, w jakie możemy używać różnych stylów tekstu,
 (pogrubienie, kursywa, podkreślenie) w ramach tego samego tekstu.

```python
{% include "../tutorial/tuto6.py" %}
```

[Plik wynikowy PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://raw.githubusercontent.com/py-pdf/fpdf2/master/docs/fpdf2-logo.png)

Nowa metoda drukowania tekstu pokazana tutaj to
 [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
. Jest bardzo podobna do
 [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
 , przy czym główne różnice polegają na:

- Koniec linii znajduje się na prawym marginesie, a następny wiersz zaczyna się na lewym marginesie.
- TAktualna pozycja przesuwa się do końca tekstu.

Dlatego metoda pozwala nam napisać fragment tekstu, zmienić styl czcionki i kontynuować
dokładnie od miejsca, w którym skończyliśmy. Z drugiej strony, jej główną wadą jest to, że
nie możemy wyjustować tekstu tak jak robimy to za pomocą metody
 [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
.

W pierwszej stronie przykładu użyliśmy do tego celu metody
 [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
Początek zdania zapisany jest zwykłą czcionką, następnie za pomocą metody 
 [set_font()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
 przełączyliśmy się na podkreślenie i dokończyliśmy zdanie.

Aby dodać link wewnętrzny prowadzący do drugiej strony, użyliśmy metody 
 [add_link()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link)
, która tworzy klikalny obszar nazwany przez nas "link", który kieruje do innej strony w dokumencie.

Do utworzenia linku zewnętrznego za pomocą obrazu użyliśmy metody 
 [image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image)
. Metoda ta ma opcję przekazania linku jako jednego z argumentów. Link może być zarówno wewnętrzny, jak i zewnętrzny.

Alternatywnie, inną opcją zmiany stylu czcionki i dodawania linków jest użycie metody z `write_html()`. Jest to parser html, który pozwala na dodawanie tekstu, zmianę stylu czcionki i dodawanie linków za pomocą html.
