# Руководство #

Полная документация по методам класса **FPDF**: [`fpdf.FPDF` API doc](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

## Руководство 1 - Минимальный пример ##

Начнём с классического примера:

```python
{% include "../tutorial/tuto1.py" %}
```

[Итоговый PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto1.pdf)

После подключения библиотеки мы создаем объект `FPDF`. Здесь используется конструктор [FPDF](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF) со значениями по умолчанию: страницы формата A4 портретные, единица измерения - миллиметр.

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

Можно установить PDF в альбомном режиме (`L`) или использовать другой формат страниц (например, `Letter` или `Legal`) и единицы измерения (`pt`, `cm`, `in`).

На данный момент страницы нет, поэтому мы должны добавить ее с помощью команды [add_page](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). Начало страницы находится в левом верхнем углу, а текущая позиция по умолчанию располагается на расстоянии 1 см от границ; поля можно изменить с помощью команды [set_margins](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins).

Прежде чем мы сможем напечатать текст, обязательно нужно выбрать шрифт с помощью [set_font](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), иначе документ будет недействительным. Мы выбираем Helvetica bold 16:

```python
pdf.set_font('Helvetica', style='B', size=16)
```

Мы можем указать курсив с помощью `I`, подчеркнутый шрифт с помощью `U` или обычный шрифт с помощью пустой строки (или использовать любую комбинацию). Обратите внимание, что размер шрифта задается в пунктах, а не в миллиметрах (или другой единице измерений); это единственное исключение. Другие встроенные шрифты: `Times`, `Courier`, `Symbol` и `ZapfDingbats`.

Теперь мы можем распечатать ячейку с помощью [cell](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). Ячейка - это прямоугольная область, возможно, обрамленная рамкой, которая содержит некоторый текст. Она отображается в текущей позиции. Мы указываем ее размеры, текст (центрированный или выровненный), должны ли быть нарисованы рамки, и куда текущая позиция перемещается после нее (вправо, вниз или в начало следующей строки). Чтобы добавить рамку, мы сделаем следующее:

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

Чтобы добавить новую ячейку с центрированным текстом и перейти к следующей строке, мы сделаем следующее:

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**Примечание**: разрыв строки также можно сделать с помощью [ln](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). Этот метод позволяет дополнительно указать высоту разрыва.

Наконец, документ закрывается и сохраняется по указанному пути к файлу с помощью функции [output](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Без указания параметров `output()` возвращает буфер PDF `bytearray`.

## Руководство 2 - Верхний колонтитул, нижний колонтитул, разрыв страницы и картинка ##

Пример двух страниц с верхним и нижним колонтитулами и логотипом:

```python
{% include "../tutorial/tuto2.py" %}
```

[Итоговый PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto2.pdf)

В этом примере используются методы [header](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.header) и [footer](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) для обработки заголовков и колонтитулов страницы. Они вызываются автоматически. Они уже существуют в классе FPDF, но ничего не делают, поэтому мы должны расширить класс и переопределить их.

Логотип печатается методом [image](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image) с указанием его левого верхнего угла и ширины. Высота вычисляется автоматически, чтобы соблюсти пропорции изображения.

Для печати номера страницы в качестве ширины ячейки передается нулевое значение. Это означает, что ячейка должна простираться до правого поля страницы; это удобно для центрирования текста. Номер текущей страницы возвращается методом [page_no](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no); что касается общего количества страниц, то оно получается с помощью специального значения `{nb}`, которое будет подставлено при закрытии документа.
Обратите внимание на использование метода [set_y](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y), который позволяет установить позицию в абсолютном месте страницы, начиная сверху или снизу.

Здесь используется еще одна интересная функция: автоматический разрыв страницы. Как только ячейка пересекает границу страницы (по умолчанию 2 сантиметра от низа), происходит разрыв и шрифт восстанавливается. Хотя верхний и нижний колонтитулы выбирают свой собственный шрифт (`helvetica`), основная часть продолжает использовать `Times`. Этот механизм автоматического восстановления также применяется к цветам и ширине линий. Предел, который вызывает разрыв страницы, можно установить с помощью [set_auto_page_break](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).

## Руководство 3 - Переносы строк и цвета ##

Продолжим с примера, который печатает выровненные абзацы. Он также иллюстрирует использование цветов.

```python
{% include "../tutorial/tuto3.py" %}
```

[Итоговый PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto3.pdf)

[Текст Жюля Верна](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

Метод [get_string_width](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) позволяет определить длину строки в текущем шрифте, которая используется здесь для расчета положения и ширины рамки, окружающей заголовок. Затем устанавливаются цвета (через [set_draw_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), [set_fill_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) и [set_text_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)), а толщина линии устанавливается в 1 мм (против 0,2 по умолчанию) с помощью [set_line_width](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). Наконец, мы выводим ячейку (последний параметр True указывает на то, что фон должен быть заполнен).

Для печати абзацев используется метод [multi_cell](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell). Каждый раз, когда строка достигает правого края ячейки или встречается символ возврата каретки, выдается разрыв строки и автоматически создается новая ячейка под текущей. По умолчанию текст выравнивается по ширине.

Определены два свойства документа: заголовок ([set_title](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) и автор ([set_author](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Свойства можно просматривать двумя способами. Первый - открыть документ непосредственно с помощью Acrobat Reader, перейти в меню Файл и выбрать пункт Свойства документа. Второй, также доступный из плагина, - щелкнуть правой кнопкой мыши и выбрать пункт Свойства документа.

## Руководство 4 - Несколько колонок ##

 Этот пример является вариантом предыдущего и показывает, как расположить текст в нескольких колонках.

```python
{% include "../tutorial/tuto4.py" %}
```

[Итоговый PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto4.pdf)

[Текст Жюля Верна](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

_⚠️ This section has changed a lot and requires a new translation: <https://github.com/py-pdf/fpdf2/issues/267>_

English versions:

* [Tuto 4 - Multi Columns](https://py-pdf.github.io/fpdf2/Tutorial.html#tuto-4-multi-columns)
* [Documentation on TextColumns](https://py-pdf.github.io/fpdf2/TextColumns.html


## Руковдство 5 - Создание таблиц ##

```python
{% include "../tutorial/tuto5.py" %}
```

[Итоговый PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto5.pdf) - 
[Список стран](https://github.com/py-pdf/fpdf2/raw/master/tutorial/countries.txt)

_⚠️ This section has changed a lot and requires a new translation: <https://github.com/py-pdf/fpdf2/issues/267>_

English versions:

* [Tuto 5 - Creating Tables](https://py-pdf.github.io/fpdf2/Tutorial.html#tuto-5-creating-tables)
* [Documentation on tables](https://py-pdf.github.io/fpdf2/Tables.html)

## Руководство 6 - Создание ссылок и смешивание стилей текста ##

В этом уроке будет рассказано о нескольких способах вставки ссылок внутри pdf документа, а также о добавлении ссылок на внешние источники.

Также будет показано несколько способов использования различных стилей текста (жирный, курсив, подчеркивание) в одном и том же тексте.

```python
{% include "../tutorial/tuto6.py" %}
```

[Итоговый PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://py-pdf.github.io/fpdf2/fpdf2-logo.png)

Новый метод, показанный здесь для печати текста - это [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write). Он очень похож на [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell), основные отличия заключаются в следующем:

- Конец строки находится на правом поле, а следующая строка начинается на левом поле.
- Текущая позиция перемещается в конец текста.

Таким образом, этот метод позволяет нам написать фрагмент текста, изменить стиль шрифта и продолжить с того самого места, на котором мы остановились. С другой стороны, его главный недостаток заключается в том, что мы не можем выровнять текст, как это делается при использовании метода [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell).

На первой странице примера мы использовали для этой цели [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write). Начало предложения написано текстом обычного стиля, затем, используя метод [set_font()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), мы переключились на подчеркивание и закончили предложение.

Для добавления внутренней ссылки, указывающей на вторую страницу, мы использовали метод [add_link()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link), который создает кликабельную область, названную нами "link", которая ведет в другое место внутри документа.

Чтобы создать внешнюю ссылку с помощью изображения, мы использовали метод [image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image). Этот метод имеет возможность передать ссылку в качестве одного из аргументов. Ссылка может быть как внутренней, так и внешней.

В качестве альтернативы для изменения стиля шрифта и добавления ссылок можно использовать метод `write_html()`. Это парсер html, который позволяет добавлять текст, изменять стиль шрифта и добавлять ссылки с помощью html.
