विभिन्न उदाहरण जल्दी से दिखाते हैं कि fpdf2 का उपयोग कैसे करें। आपको सभी मुख्य विशेषताओं की व्याख्या मिल जाएगी।

Methods full documentation / तरीके पूर्ण प्रलेखन: [`fpdf.FPDF` API doc](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Tuto 1 - मूल उदाहरण ##

आइए क्लासिक उदाहरण से शुरू करें:

```python
{% include "../tutorial/tuto1.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

लाइब्रेरी फ़ाइल को शामिल करने के बाद, हम एक `FPDF` ऑब्जेक्ट बनाते हैं।
[FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) कंस्ट्रक्टर का उपयोग यहां डिफ़ॉल्ट मानों के साथ किया जाता है:

पृष्ठ A4 पोर्ट्रेट में हैं और माप इकाई मिलीमीटर है।
इसके साथ स्पष्ट रूप से निम्नलिखित निर्दिष्ट किये जा सकते है:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

पीडीएफ को लैंडस्केप मोड में सेट करना संभव है (`L`) या अन्य पेज प्रारूपों का उपयोग करने के लिए
(जैसे कि `Letter` तथा `Legal`) और इकाइयों को मापें (`pt`, `cm`, `in`)।

फिलहाल कोई पेज नहीं है, इसलिए हमें इसमें एक [add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page) जोड़ना होगा ।

मूल ऊपरी-बाएँ कोने में है और वर्तमान स्थिति डिफ़ॉल्ट रूप से सीमाओं से 1 cm पर रखी जाती है; मार्जिन को [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins)
के साथ बदला जा सकता है ।

इससे पहले कि हम टेक्स्ट प्रिंट कर सकें, इसके साथ एक फॉन्ट का चयन [set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) से करना अनिवार्य है, अन्यथा दस्तावेज़ (Document) अमान्य होगा।
हम Helvetica bold 16 चुनते हैं:

```python
pdf.set_font('helvetica', 'B', 16)
```

हम `I` के साथ इटैलिक (Italic) निर्दिष्ट कर सकते हैं, `U` के साथ रेखांकित (Underlined) निर्दिष्ट कर सकते हैं या एक नियमित फ़ॉन्ट
एक खाली स्ट्रिंग के साथ (या कोई संयोजन) निर्दिष्ट कर सकते हैं। ध्यान दें कि फ़ॉन्ट का आकार अंकों में दिया गया है, मिलीमीटर में नहीं (या अन्य उपयोगकर्ता इकाई); यह एकमात्र अपवाद है।
अन्य बिल्ट-इन फॉन्ट `Times`, `Courier`, `Symbol` और `ZapfDingbats` हैं।

अब हम [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) के साथ cell print कर सकते हैं। 
एक सेल (cell) एक आयताकार क्षेत्र है, संभवतः तैयार किया गया है, जिसमें कुछ पाठ है। यह वर्तमान स्थिति में प्रदान किया जाता है।
हम इसके आयाम, इसके पाठ (केंद्रित या संरेखित) निर्दिष्ट करते हैं, अगर सीमाएं
खींचा जाना चाहिए,और जहां वर्तमान स्थिति इसके बाद चलती है (दाईं ओर,
नीचे या अगली पंक्ति की शुरुआत में)।

एक फ्रेम जोड़ने के लिए, हम यह करेंगे:

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

केन्द्रित पाठ (centered text) के साथ इसके आगे एक नया सेल (cell) जोड़ने के लिए और अगली पंक्ति पर जाने के लिए, हम
करेंगे:

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**टिप्पणी**: लाइन ब्रेक [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln) के साथ भी किया जा सकता हैं। इस
विधि ब्रेक की ऊंचाई के अतिरिक्त निर्दिष्ट करने की अनुमति देती है।

अंत में, दस्तावेज़ को बंद कर दिया गया है और प्रदान किए गए फ़ाइल पथ के तहत सहेजा गया है
[output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output).बिना किसी पैरामीटर के, `output()`
PDF `bytearray` बफ़र लौटाता है।

## Tuto 2 - शीर्षलेख (Header), पाद लेख (Footer), पृष्ठ विराम (Page Break) और छवि (Image) ##

यहाँ शीर्ष लेख (Header), पादलेख (Footer) और लोगो (Logo) के साथ दो पृष्ठ का उदाहरण दिया गया है:

```python
{% include "../tutorial/tuto2.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)

यह उदाहरण [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) और [footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) को संसाधित करने के लिए header और footer लेख विधियों का उपयोग करता है।
उन्हें स्वचालित रूप से (automatically) बुलाया जाता है। वे पहले से ही FPDF वर्ग में मौजूद हैं लेकिन कुछ नहीं करते हैं,
इसलिए हमें class का विस्तार करना होगा और उन्हें override करना होगा।

Logo को निर्दिष्ट करके [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) विधि से इसका ऊपरी-बाएँ कोना और इसकी चौड़ाई निर्दिष्ट करके मुद्रित किया जाता है। 
छवि अनुपात का सम्मान करने के लिए ऊंचाई की गणना स्वचालित रूप से की जाती है।

पृष्ठ संख्या (Page number) मुद्रित (print) करने के लिए, सेल चौड़ाई (cell width) के रूप में एक शून्य मान(null value) पास किया जाता है। 

इसका मतलब है कि सेल को पेज के दाहिने हाशिये (right margin) तक बढ़ाया जाना चाहिए; यह पाठ को केंद्र(center) में रखने के लिए आसान है। 

वर्तमान पृष्ठ संख्या [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) विधि द्वारा वापस की जाती है; पृष्ठों की कुल संख्या के लिए, यह विशेष मूल्य `{nb}` के माध्यम से प्राप्त किया जाता है जिसे दस्तावेज़
बंद होने पर प्रतिस्थापित किया जाएगा कहा जाता है)।

[set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) पद्धति के उपयोग पर ध्यान दें जो पृष्ठ में एक पूर्ण स्थान पर स्थिति सेट करने की अनुमति देता है, ऊपर या नीचे से शुरू होता है।

यहाँ एक और दिलचस्प विशेषता का उपयोग किया गया है: the automatic page breaking. 
जैसे ही कोई सेल पृष्ठ में एक सीमा को पार करेगा (डिफ़ॉल्ट रूप से नीचे से 2 सेंटीमीटर पर), एक ब्रेक किया जाता है और फ़ॉन्ट को पुनर्स्थापित किया जाता है। 

हालांकि शीर्ष लेख (Header) और पाद लेख (Footer) अपने स्वयं के फ़ॉन्ट (`Helvetica`) का चयन करते हैं, body `Times` के साथ जारी रहता है।
स्वचालित बहाली का यह तंत्र रंगों और रेखा की चौड़ाई पर भी लागू होता है।
पृष्ठ विराम को ट्रिगर करने वाली सीमा को [set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break) के साथ सेट किया जा सकता है।


## Tuto 3 - लाइन ब्रेक और रंग ##

आइए एक उदाहरण के साथ जारी रखें जो Justified अनुच्छेदों को प्रिंट करता है। यह रंगों के उपयोग को भी दर्शाता है।

```python
{% include "../tutorial/tuto3.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

[get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) विधि वर्तमान फ़ॉन्ट में एक स्ट्रिंग की लंबाई निर्धारित करने की अनुमति देती है, 
जिसका उपयोग शीर्षक के आसपास के फ्रेम की स्थिति और चौड़ाई की गणना करने के लिए यहां किया जाता है।

फिर रंग सेट किए जाते हैं ([set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), सेट फिल कलर और सेट टेक्स्ट कलर के माध्यम से) और लाइन की मोटाई सेटलाइन चौड़ाई के साथ 1 मिमी (डिफ़ॉल्ट रूप से 0.2 के खिलाफ) पर सेट की जाती है।

फिर रंग सेट किए जाते हैं ([set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), [set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) और [set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color) के माध्यम से) और लाइन की मोटाई [set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width) के साथ 1 मिमी (डिफ़ॉल्ट रूप से 0.2 के विरुद्ध) पर सेट की जाती है। 
अंत में, हम सेल को आउटपुट करते हैं (अंतिम पैरामीटर के `true` होने से हमे पता चलता है कि पृष्ठभूमि को भरा जाना चाहिए)।

पैराग्राफ को प्रिंट करने के लिए इस्तेमाल की जाने वाली विधि [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) है।
हर बार जब कोई लाइन cell के दाहिने छोर तक पहुँचती है या carriage return कैरेक्टर मिलता है, तो एक लाइन ब्रेक जारी किया जाता है और current cell के तहत एक नया सेल स्वचालित रूप से बनाया जाता है। Text डिफ़ॉल्ट रूप से Justified है।

दो दस्तावेज़ गुण परिभाषित हैं: शीर्षक
([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) और लेखक 
([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). गुणों को दो तरीकों से देखा जा सकता है।
सबसे पहले दस्तावेज़ को सीधे एक्रोबेट रीडर के साथ खोलना है, फ़ाइल मेनू पर जाएँ
और दस्तावेज़ गुण विकल्प चुनें। दूसरा, प्लग-इन से भी उपलब्ध है, राइट-क्लिक करना और दस्तावेज़ गुण चुनना है।

## Tuto 4 - मल्टी कॉलम ##

 यह उदाहरण पिछले एक का एक प्रकार है, जिसमें दिखाया गया है कि टेक्स्ट को कई कॉलम में कैसे रखा जाए।
 
```python
{% include "../tutorial/tuto4.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

पिछले ट्यूटोरियल से मुख्य अंतर [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) और set_col विधियों का उपयोग है।

[accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) विधि का उपयोग करते हुए, एक बार जब सेल पृष्ठ की निचली सीमा को पार कर जाता है, तो यह वर्तमान कॉलम संख्या की जांच करेगा।
यदि यह 2 से कम है (हमने पृष्ठ को तीन स्तंभों में विभाजित करना चुना है) तो यह set_col विधि को कॉल करेगा,
कॉलम संख्या बढ़ाना और अगले कॉलम की स्थिति बदलना ताकि टेक्स्ट वहां जारी रह सके।
एक बार तीसरे कॉलम की निचली सीमा तक पहुँच जाने पर, [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) विधि रीसेट हो जाएगी और पहले कॉलम पर वापस जाएगी और एक पेज ब्रेक को ट्रिगर करेगी।


## Tuto 5 - टेबल बनाना ##

```python
{% include "../tutorial/tuto5.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Countries text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/countries.txt)

_⚠️ This section has changed a lot and requires a new translation: <https://github.com/PyFPDF/fpdf2/issues/267>_

English versions:

* [Tuto 5 - Creating Tables](https://pyfpdf.github.io/fpdf2/Tutorial.html#tuto-5-creating-tables)
* [Documentation on tables](https://pyfpdf.github.io/fpdf2/Tables.html)

## Tuto 6 - लिंक बनाना और टेक्स्ट शैलियों को मिलाना ##

यह ट्यूटोरियल पीडीएफ दस्तावेज़ के अंदर लिंक डालने के साथ-साथ बाहरी स्रोतों के लिंक जोड़ने के कई तरीकों की व्याख्या करेगा।
 यह कई तरीके भी दिखाएगा जिससे हम एक ही टेक्स्ट के भीतर विभिन्न टेक्स्ट शैलियों, (बोल्ड, इटैलिक, अंडरलाइन) का उपयोग कर सकते हैं।
 
```python
{% include "../tutorial/tuto6.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://raw.githubusercontent.com/PyFPDF/fpdf2/master/docs/fpdf2-logo.png)

टेक्स्ट प्रिंट करने के लिए यहां दिखाया गया नया तरीका [write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write) है। यह बहुत हद तक [multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) के समान है, मुख्य अंतर यह है:
- पंक्ति का अंत दाएं हाशिये पर है और अगली पंक्ति बाएं हाशिये पर शुरू होती है।
- वर्तमान स्थिति पाठ के अंत में चली जाती है।

इसलिए विधि हमें पाठ का एक हिस्सा लिखने, फ़ॉन्ट शैली को बदलने और ठीक उसी स्थान से जारी रखने की अनुमति देती है जहां से हमने छोड़ा था।
दूसरी ओर, इसका मुख्य दोष यह है कि हम टेक्स्ट को जस्टिफाई नहीं कर सकते जैसे हम [multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) मेथड के साथ करते हैं।

उदाहरण के पहले पृष्ठ में, हमने इस उद्देश्य के लिए [write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write) का उपयोग किया। वाक्य की शुरुआत नियमित शैली के पाठ में लिखी जाती है, फिर [set_font()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) विधि का उपयोग करके, हमने रेखांकित करने के लिए स्विच किया और वाक्य को समाप्त किया।

दूसरे पृष्ठ की ओर इशारा करते हुए एक आंतरिक लिंक जोड़ने के लिए, हमने  [add_link()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link) विधि का उपयोग किया, जो एक क्लिक करने योग्य क्षेत्र बनाता है जिसे हमने "Link" नाम दिया है जो दस्तावेज़ के भीतर किसी अन्य स्थान पर निर्देशित करता है।

Image का उपयोग करके बाहरी लिंक बनाने के लिए, हमने  [image()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image) का उपयोग किया। विधि में एक लिंक को इसके तर्कों में से एक के रूप में पारित करने का विकल्प होता है। लिंक आंतरिक या बाहरी दोनों हो सकता है।

एक विकल्प के रूप में, फ़ॉन्ट शैली बदलने और लिंक जोड़ने का दूसरा विकल्प `write_html()` पद्धति का उपयोग करना है। यह एक HTML पार्सर है, जो टेक्स्ट जोड़ने, फ़ॉन्ट शैली बदलने और html का उपयोग करके लिंक जोड़ने की अनुमति देता है।
