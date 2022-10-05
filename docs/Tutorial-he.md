<div dir="rtl">
# מדריך #

תיעוד מלא: [`fpdf.FPDF` API doc](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## 1 - דוגמא מינימלית ##

נתחיל בדוגמא קלאסית:

```python
{% include "../tutorial/tuto1.py" %}
```

[תוצר](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

אחרי שכללנו את קובץ הספריה, יצרנו אובייקט `FPDF`
הבנאי של [FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF)  משתמש כאן בערכים דיפולטיביים:
דפים בפורמט A4 לאורך והמידות במילימטרים. ניתן לציין זאת במפורש באמצעות:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```
ניתן להגדיר את הPDF לרוחב (`L`) או להשתמש בתבניות שונות (כמו `Letter` או `Legal`) ומידות שונות (כמו `pt`, `cm`, `in`).

כרגע אין עמודים, נצטרך להוסיף אחד בעזרת [add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page).
המקור הוא בפינה השמאלית עליונה והפוזיציה הנוכחית בברירת המחדל היא סנטימטר אחד מהגבולות; ניתן לשנות את השוליים על ידי [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins).

לפני שנוכל להדפיס טקסט, חובה לבחור גופן בעזרת [set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), אחרת המסמך לא יהיה תקין. אנחנו בוחרים בגופן helvetica מודגש בגודל 16:

```python
pdf.set_font('helvetica', 'B', 16)
```

יכולנו לבחור הטייה עם `I`, קו תחתון עם `U`, או גופן רגיל עם מחרוזת ריקה (או כל שילוב של הנ"ל). שימו לב שגודל הגופן הוא בנקודות ולא מילימטרים או כל יחידת מידה אחרת. זה יוצא הדופן היחיד. הגופנים המובנים האחרים הם `Times`, `Courier`, `Symbol` וּ `ZapfDingbats`.

כעת נוכל להדפיס תא עם [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). תא הוא איזור מלבני, אולי ממוסגר, שמכיל טקסט. נוצר בפוזיציה הנוכחית. אנחנו מציינים את המידות שלו, טקסט (ממורכז או מיושר), האם לצייר גבולות, ולאן תזוז הפוזיציה הנוכחית לאחר התא (מימין, למטה או בתחילת השורה הבאה). כדי להוסיף מסגרת, נריץ:


```python
pdf.cell(40, 10, 'Hello World!', 1)
```

כדי להוסיף ליד התא הקודם תא עם טקסט ממורכז ואז ללכת לשורה הבאה, נריץ:

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**הערה**: אפשר ליצור שורה רווח גם בעזרת [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). השיטה הזו מאפשרת גם לציין את גובה הרווח

לבסוף, הקובץ נסגר ונשמר תחת הכתובת שסופקה באמצעות [output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output).
ללא פרמטרים נוספים, `output()` מחזיר את הבאפר `bytearray` של הPDF.

## 2 - כותרת, כותרת תחתונה, מעבר עמוד ותמונות ##

דוגמא בעלת שני עמודים עם כותרת, כותרת תחתונה ולוגו:

```python
{% include "../tutorial/tuto2.py" %}
```

[תוצר](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)

הדוגמא משתמשת במתודות ה[header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) ו[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer).

הלוגו מודפס עם מתודת ה[image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) ע"י ציון הנקודה השמאלית-עליונה ואת הרוחב. הגובה מחושב אוטומטית לפי מידות התמונה.

על מנת להדפיס את מספר העמוד, ניתן להעביר ערך null כרוחב התא. כך התא יתרחב עד השול הימני של העמוד; זה שימושי כאשר צריך למרכז את הטקסט. מספר העמוד הנוכחי חוזר ממתודת ה[page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no); לגבי מספר העמודים הכולל, ניתן להשיג נתון זה מהערך המיוחד `{nb}` שיוחלף בסגירת המסמך (ניתן לשנות ערך זה ע"י שימוש ב[alias_nb_pages()](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)).
שימו לב למתודה [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) שמאפשרת להגדיר פוזיציה אבסולוטית בדף, מראש או תחתית העמוד.

נעשה גם שימוש  בפיצ'ק נוסף כאן: מעבר עמוד אוטומטי. ברגע שתא יחרוד מגבולות הדף (בברירת מחדל 2 סנטימטר מהסוף), מתתבצע מעבר עמוד והגופן חוזר להיות מה שהוגדר עבור גוף העמוד. למרות שהכותרת והכותרת תחתותנה משתמשות בגופן (`helvetica`), גוף העמוד ממשיך עם `Times`. המנגנון הזה תקף גם לגבי צבע ורוחב שורה. הגבול שמפעיל את מעבר העמוד האוטומטי ניתן לשינוי באמצעות [set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).


## 3 - שורות רווח וצבעים ##

נמשיך עם דוגמא שמדפיסה פסקאות ומדגימה שימוש בצבעים.

```python
{% include "../tutorial/tuto3.py" %}
```

[תוצר](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

מתודת ה[get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) מאפשרת לקבוע אורך מחרוזת בגופן הנוכחי, שבדוגמא זו משמש כדי לחשב את הפוזיציה והרוחב של המסגרת המקיפה את הכותרת. לאחר מכן מוגדרים צבעים
(באמצעות [set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), [set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) ו [set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)) and   ועובי השורה מוגזר למילימטר (בניגוד ל0.2 מילימטר כברירת מחדל) באמצעות [set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). לבסוף אנחנו מדפיסים את התא (הפרמטר האחרון true מעיד שהרקע צריך להיות מלא).


המתודה בה משתמשים להדפסת הפסקא היא [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell). טקסט נחתך אוטומטית בסוף השורה בברירת מחדל. בכל פעם ששורה מגיעה לקצה הימני של התא או שנמצא התו (`n\`), נוצרת שורה חדשה בתא חדש מתחת לנוכחי. הפסקת שורה אוטומטית נוצרת במיקום של הרווח הקרוב או תו בלתי-נראה (`u00ad\`) לפני סוף השורה. התו יוחלף במקף אם הופעלה הפסקת שורה.

שני תכונות מסמך הוגדרו: שם המסמך ([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) ויוצר ([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). ניתן לצפות בתכונות בשני אופנים. אופציה ראשונה היא לפתוח את המסמך בAdobe Reader ישירות, ואז ב'תפריט' לבחור 'תכונות מסמך'. אופציה שניה, זמינה גם באמצעות תוסף, זה לחצן ימני ואז לבחור תכונות מסמך.

## 4 - עמודות מרובות ##

הדוגמא הזו דומה לקודמת ומראה איך לפרוס טקסט על פני מספר עמודות.

```python
{% include "../tutorial/tuto4.py" %}
```

[תוצר](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

ההבדל העיקרי בין דוגמא זו לקודמת הוא השימוש במתודות [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) וset_col

ע"י שימוש במתודה [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break), ברגע שתא חורג מהגבול התחתון של הדף, המתודה בודקת את מספר העמודה הנוכחי. אם הוא קטן מ2 (בחרנו לחלק את הדף ל3 עמודות) תיקרא המתודה set_col, שמגדילה את מספר העמודה ומשנה את הפוזיציה של העמודה הבאה כך שהטקסט ימשיך בה.

ברגע שהגענו לגבול התחתון של העמודה השלישית, המתודה [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) תאותחל, תחזור לעמודה הראשונה ותיצור מעבר עמוד.

## 5 - יצירת טבלאות ##

This tutorial will explain how to create tables easily.

The code will create three different tables to explain what
 can be achieved with some simple adjustments.

```python
{% include "../tutorial/tuto5.py" %}
```

[תוצר](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto5.pdf) -
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

## 6 - יצירת קישורים וערבוב סגנונות טקסט ##

This tutorial will explain several ways to insert links inside a pdf document,
 as well as adding links to external sources.

 It will also show several ways we can use different text styles,
 (bold, italic, underline) within the same text.

```python
{% include "../tutorial/tuto6.py" %}
```

[תוצר](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto6.pdf) -
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
 method, which creates a clickable area which we named "link" that directs to
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
