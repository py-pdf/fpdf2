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

אחרי שכללנו את קובץ הספריה, יצרנו אובייקט `FPDF`.
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

דוגמא זו מסבירה איך ליצור טבלאות בקלות.

הקוד ייצור שלוש טבלאות שונות על מנת להראות מה ניתן להשיג עם שינוים קלים.

```python
{% include "../tutorial/tuto5.py" %}
```

[תוצר](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Countries text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/countries.txt)

מאחר וטבלה היא בסה"כ אוסף של תאים, טבעי שכך נבנה טבלאות.

הדוגמא הראשונה נוצרת באופן הבסיסי ביותר שאפשר: תאים בגדלים שווים עם מסגרות ומיושרים לשמאל.התוצאה היא בסיסית אבל קלה מאוד להשגה.

הטבלה השניה מציגה כמה שיפורים: לכל עמודה יש רוחב משלה, כותרות ממורכזות ותמונות מיושרות לימין. הוסרו קווים אופקיים. זה נעשה על ידי תכונות הגבול של המתודה ()Cell, שמציינת איזה גבולות של התא להדפיס. כאן אנחנו רוצים את הגבול השמאלי (L) והימני (R). כעת נותרה הבעיה של הקווים האופקיים. ישנן שתי אפשרויות לפתור בעיה זו: לבדוק את הקו האחרון בלולאה, במקרה זה נשתמש בLRB עבור פרמטר הגבול; או לחלופין, כמו שעשינו כאן, להוסיף את הקו בסוף הלולאה.

הטבלה השלישית דומה לשניה אבל עושה שימוש בצבעים. צבעי המילוי, טקסט והקווים מצויינים במפורש. שינוי הצבעים נעשה על ידי שימוש בתאים שקופים ומלאים לסירוגין.

## 6 - יצירת קישורים וערבוב סגנונות טקסט ##

דוגמא זו מציגה מספר דרכים להוסיף קישורים למסמך וקישורים חיצוניים. בנוסף הדוגמא ממחישה שימוש בסגנונות שונים של עיצוב טקסט (מודגש, נטוי, קו תחתון) באותו טקסט.
This tutorial will explain several ways to insert links inside a pdf 

```python
{% include "../tutorial/tuto6.py" %}
```

[תוצר](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://raw.githubusercontent.com/PyFPDF/fpdf2/master/docs/fpdf2-logo.png)

המתודה החדשה שמשומשת כאן כדי להדפיס טקסט היא  [write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write). דומה מאוד ל[multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell), כאשר ההבדלים העיקריים הם:

- סוף השורה הוא בגבול הימני והשורה הבאה מתחילה בגבול השמאלי
- הפוזיציה הנוכחית זזה לסוף שורת הטקסט

לפיכך המתודה מאפשרת לנו לכתוב קטע טקסט, לשנות את סגנון הגופן, ולהמשיך מאותו מקום שעצרנו. מצד שני, החסרון העיקרי הוא שלא ניתן ליישר את הטקסט כמו ב[multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell).

בעמוד הראשון של הדוגמא השתמשנו [write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write) למטרה זו. תחילת המשפט נכתב בסגנון טקסט רגיל ואז על ידי שימוש במתודה [set_font()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) החלפנו לטקסט עם קו תחתון לסיום המשפט.

כדי להוסיף קישור פנימי שמוביל לעמוד השני השתמשנו במתודה [add_link()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link) שוצרת איזור ניתן להקלקה שנתנו לו את השם "קישור" שמוביל לאיזור אחר באותו המסמך. בעמוד השני השתמשנו ב[set_link()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_link) על מנת להגדיר את האיזור אליו הקישור שיצרנו מוביל.

על מנת ליצור קישור חיצני באמצעות תמונה, השתמשנו במתודה [image()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image). למתודה יש אופציה לקבל קישור כאחד הפרמטרים שלה. הקישור יכול להיות פנימי או חיצוני.

To create the external link using an image, we used
 [image()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image)

ניתן גם להשתמש במתודה `write_html()` כדי לשנות סגנונות גופן ולהוסיף קישורים. זהו פרסר של html, שמאפשר להוסיף טקסט, לשנות את הסגנון ולהוסיף קישורים באמצעות html.

</div>