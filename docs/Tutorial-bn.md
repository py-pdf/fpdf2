# Tutorial #

Method গুলোর সম্পূর্ণ ডকুমেন্টেশন: [`fpdf.FPDF` API doc](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[ TOC ]

## টিউটোরিয়াল ১ - সংক্ষিপ্ত উদাহরণ ##

একটি ক্লাসিক উদাহরণ দিয়ে শুরু করা যাক:

```python
{% include "../tutorial/tuto1.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto1.pdf)

প্রয়োজনীয় লাইব্রেরীগুলো যুক্ত করার পর, আমরা একটা `FPDF` অব্জেক্ট তৈরি করবো. 
[FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) কনস্ট্রাক্টরটি এখানে ডিফল্ট ভ্যালুগুলো ব্যবহার করছে: 
পৃষ্ঠাগুলো A4 পোর্ট্রেট সাইজের এবং পরিমাপক একক হচ্ছে মিলিমিটার.
এটাকে বাহ্যিকভাবে উল্লেখ করা যায় নিচের স্নিপেট এর মত করে -

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

পিডিএফ কে ল্যান্ডস্কেপ মোড (`L`) অথবা অন্যান্য ফরম্যাট এও পৃষ্ঠা বিন্যাস করা যায় (যেমন `Letter` এবং `Legal`) 
এবং পরিমাপক একক (`pt`, `cm`, `in`)।


এই মুহুর্তে এখানে কোন পৃষ্ঠা নেই, তাই আমাদের একটা পৃষ্ঠা যুক্ত করতে হবে
[add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page)। শুরুটা উপর-নাম কোণায় এবং বর্তমান অবস্থানটি
সীমান্ত থেকে গতানুগতিকভাবে ১ সেন্টিমিটার নিচের দিকে অবস্থান করে; মার্জিন পরিবর্তন করা যাবে 
[set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins)।

লিখা প্রিন্ট করার পূর্বেই ফন্ট সিলেক্ট করে নিতে হয় [set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), 
নতুবা ডকুমেন্ট টা অকার্যকর হয়ে যাবে। আমরা Helvetica bold 16 পছন্দ করলামঃ 

```python
pdf.set_font('helvetica', 'B', 16)
```

ইটালিক সেট করতে চাইলে `I`, আন্ডারলাইন করতে চাইলে `U` অথবা একটি সাধারণ ফন্টে একটি খালি স্ট্রিং 
(অথবা যেকোন কম্বিনেশন)। উল্লেখ্য ফন্ট সাইজ পয়েন্টে দেয়া আছে, মিলিমিটারে নয় (অন্য কোন এককেও নয়);
এটাই একমাত্র ব্যাতিক্রম। অন্যান্য মৌলিক ফন্টগুলো হলো, `Times`, `Courier`, `Symbol` এবং `ZapfDingbats`

এখন আমরা একটি cell প্রিন্ট করতে পারি [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell)। cell হলো একটি আয়তাকৃতি
ক্ষেত্র, হয়তো ফ্রেম করা, যেখানে কিছু টেক্সট থাকবে। এটা রেন্ডার হয় বর্তমান অবস্থানে। আমরা ডাইমেনশন, 
টেক্সট (মাঝামাঝি কিংবা সাজানো) নির্দিষ্ট করতে পারি, যদি বর্ডার আকানো হয়, এবং বর্তমান অবস্থান বর্ডারের পরে এগিয়ে যাবে
(ডানে, নিচে অথবা পরবর্তী লাইনের শুরুতে)। ফ্রেম যুক্ত করার আমরা নিচের মত করতে পারিঃ

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

এর পর কেন্দ্র বরাবর একটি নতুন cell যুক্ত করে এবং পরের লাইনে এগোনোর জন্য আমরা নিচের মত করতে পারিঃ

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**মন্তব্য**: পরবর্তী লাইনে আমরা এভাবেও যেতে পারি [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln)। এই মেথডের 
মাধ্যমে লাইন ব্রেক এর উচ্চতাও যুক্ত করা যায়।

সবশেষে, ডকুমেন্টটি বন্ধ করা হয় এবং [output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output) এই ফাইল পাথ 
এ সেভ করা হলো। কোন প্যারামিটার ছাড়া `output()` পিডিএফ এর একটি `bytearray` রিটার্ন করে। 

## টিউটোরিয়াল ২ - হেডার, ফুটার, পেজ ব্রেক এবং ইমেজ ##

হেডার, ফুটার এবং লোগো সহ একটা দুই পৃষ্ঠার উদাহরণ দেয়া হলোঃ

```python
{% include "../tutorial/tuto2.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto2.pdf)

এই উদাহরণটি headers এবং footers প্রসেস করার জন্য [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) এবং 
[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) মেথডকে ব্যবহারকে দেখায়। এরা স্বয়ংক্রিয়ভাবেই চালিত হয়। 
এরা FPDF ক্লাসেই থাকে কিন্তু কোন আলাদা প্রসেস করে না, তাই এই ক্লাসগুলোকে এক্সটেন্ড করতে হবে এবং 
ওভাররাইড করতে হবে।

অবস্থান উপরের কোণা এবং চওড়ার পরিমান নির্দ্দিষ্ট করে লোগোটি প্রিন্ট করা হয় 
[image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) মেথডকে কল করলে। ছবির অনুপাতকে ঠিক রাখার জন্য
 উচ্চতাটা স্বয়ংক্রিয়ভাবেই নিরূপিত হয়। 

পৃষ্ঠা নম্বর প্রিন্ট করার জন্য, একটি শূণ্য মান cell width হিসেবে পাঠানো হয়। এর মানে cell টি 
পৃষ্ঠার ডান মার্জিন পর্যন্ত প্রসারিত হওয়া উচিত; যেটা লিখা গুলোকে কেন্দ্র বরাবর সারিবদ্ধ করা হলো। 
[page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) মেথড বর্তমান পৃষ্ঠা নাম্বারটি রিটার্ন করে; 
মোট পৃষ্ঠা নাম্বারটা একটি বিশেষ ভ্যালু `{nb}` এর মাধ্যমে পাওয়া যায় যেটা ডকুমেন্ট ক্লোজারের এর 
সময় প্রতিস্থাপিত হয়। (এই বিশেষ ভ্যালু পরিবর্তন করা যায়  
[alias_nb_pages()](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages) এর মাধ্যমে)। উল্লেখ্য, 
  উপর কিংবা নিচ থেকে শুরু করে পৃষ্ঠার অবস্থান [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) 
  মেথডের ব্যবহার করে সেট করা যায়। 

এখানে আরেকটি মজার বৈশিষ্ট্য ব্যবহার করা হয়েছেঃ অটোমেটিক পেজ ব্রেকিং। যখনই একটা cell একটা 
পেজ লিমিট ক্রস করে যায় ( নিচ থেকে ২ সেন্টিমিটার ), পেজ ব্রেক এ্যাপ্লাই হয় এবং ফন্ট রিস্টোর হয়। 
যদিও হেডার এবং ফুটার নিজ নিজ ফন্ট (`helvetica`) সিলেক্ট করে, পেজ বডি `Times` হিসেবেই 
এগোতে থাকে। অটোমেটিক রিস্টোর এর ব্যাপার টা কালার এবং লাইন উইডথ এর ব্যাপারেও প্রযোজ্য হয়। 
পেজ ব্রেক এর লিমিট টি [set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break) 
মেথডের মাধ্যমেও সেট করা যায়।

## টিউটোরিয়াল ৩ - লাইন ব্রেক এবং কালারস ##

জাস্টিফাইড প্যারাগ্রাফে প্রিন্ট করা একটি উদাহরণ এর সাথে এগোনো যাক। যা একইসাথে colors নিয়েও ধারণা দেবে। 

```python
{% include "../tutorial/tuto3.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne text](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

[get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) মেথড বর্তমান ফন্টে একটি স্ট্রিং এর 
দৈর্ঘ্য নির্ণয় করে দেয়, যা এখানে অবস্থা এবং টাইটেল সমেত ফ্রেম ও এর আশপাশসহ উইদথ মাপজোকের জন্য ব্যবহার 
করা যায়। colors সেট করা যায় ([set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), 
[set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) এবং
[set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color) মাধ্যমে) এবং লাইনের পুরুত্ব বা থিকনেস সেট 
করা হলো 1 mm ( 0.2 এর বিপরীতে বাই ডিফল্ট) [set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width) 
এর মাধ্যমে। অবশেষে, আমরা cell টা আউটপুট দিলাম (সর্বশেষ প্যারামিটার টা true যার মানে ব্যাকগ্রাউন্ড আবশ্যিকভাবে 
পরিপূর্ণ থাকতে হবে)। 

প্যারাগ্রাফ প্রিন্ট করার জন্য [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) মেথড ব্যবহার করা হয়েছে। লিখাগুলো জাস্টিফাইড এলাইনমেন্টে 
এ থাকে গতানুগতিকভাবে। প্রত্যেক লাইন যখন cell এর শেষ এ পৌছায় অথবা একটি carriage return ক্যারেক্টার (`\n`) পাওয়া যায়, একটি লাইন ব্রেক 
এ্যাপ্লাই করা হয় এবং একটি নতুন cell অটোমেটিক্যালি বর্তমানটির নিচে তৈরি হয়।
সঠিক লিমিটের পূর্বেই কাছাকাছি স্পেস কিংবা সফট হাইফেন (`\u00ad`) ক্যারেক্টার এর জায়গায় একটা অটোমেটিক ব্রেক তৈরি হয়। 
যখন একটি লাইন ব্রেক এ্যাপ্লাই করা হয় তখন একটা সফট-হাইফেন একটি নরমাল হাইফেন এর দ্বারা প্রতিস্থাপিত হয় নতুবা ইগ্নোর হয়। 

ডকুমেন্ট দুটো প্রপার্টি সংঙ্গায়িত করা হয়ঃ title ([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) মেথড এবং 
author ([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)) মেথড। প্রপার্টি দুই উপায়ে দেখা যায়।
প্রথমটি হলো ডকুমেন্টকে ডিরেক্টলি Acrobat Reader দিয়ে ওপেন করা হয়, File মেন্যূ তে গিয়ে Document Properties 
অপশনটি চুজ করা হয়। পরেরটি হলো, প্লাগিন থেকে রাইট ক্লিক করে ডকুমেন্ট প্রপার্টি সিলেক্ট করে। 

## টিউটোরিয়াল ৪ - মাল্টি কলাম ##

এই উদাহরণটি পূর্বের উদাহরণ এর অন্যরকম সংস্করণ, যা আসলে কিভাবে কয়েকটি কলাম এর মধ্যে টেক্সট রাখতে হয় 
সেটা দেখানো হয়েছে। 

```python
{% include "../tutorial/tuto4.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne text](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

_⚠️ This section has changed a lot and requires a new translation: <https://github.com/py-pdf/fpdf2/issues/267>_

English versions:

* [Tuto 4 - Multi Columns](https://py-pdf.github.io/fpdf2/Tutorial.html#tuto-4-multi-columns)
* [Documentation on TextColumns](https://py-pdf.github.io/fpdf2/TextColumns.html


## টিউটোরিয়াল ৫ - টেবিল তৈরি করা ##

এই টিউটোরিয়ালটি কিভাবে হালকা কিছু পরিবর্তন করেই সহজেই ভিন্ন দুইটি টেবিল তৈরি করা যায় সেটা ব্যাখ্যা করবে। 
না না কাঠের না! সারি-কলাম এর টেবিল।

```python
{% include "../tutorial/tuto5.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Countries CSV data](https://github.com/py-pdf/fpdf2/raw/master/tutorial/countries.txt)

প্রথম উদাহরণটি [`FPDF.table()`](https://py-pdf.github.io/fpdf2/Tables.html) এর ভেতরে ডেটা সরবরাহের মাধ্যমে 
খুবই সাধারণভাবেই তৈরি করা যায়।  ফলাফল খুবই সাধারণ কিন্তু খুব সহজেই তৈরি করা যায় এমন।

পরবর্তী টেবিলে কিছু পরিবর্তন আনা হয়েছেঃ কালার, টেবিলের নিয়ন্ত্রিত বিস্তার, হ্রাসকৃত লাইনের উচ্চতা, মাঝ বরাবর এলাইন করা শিরোনাম,
 ডান দিকে এলাইন করা ছবি ... এসবের মাধ্যমে। 
 তাছাড়া, আনুভূমিক লাইনগুলোও সরানো হয়েছে। এটা করা হয়েছে এভেইলেবল ভ্যালু গুলো থেকে `borders_layout` এর একটি ভ্যালু 
 নেবার মাধ্যমে [`TableBordersLayout`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TableBordersLayout).


## টিউটোরিয়াল ৬ - লিংক এবং মিশ্র টেক্সট স্টাইল তৈরি করা ##

এই টিউটোরিয়ালটি PDF এর মধ্যে লিংক প্রবেশ করানো সহ বিভিন্ন বাহ্যিক উৎসের লিংক যুক্ত করার বিষয়ে বর্ণনা করবে। 
একইসাথে লিখার বিভিন্ন রকম স্টাইল (bold, italic, underline) এর ব্যাপারেও আলোকপাত করবে।

```python
{% include "../tutorial/tuto6.py" %}
```

[Resulting PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://raw.githubusercontent.com/py-pdf/fpdf2/master/docs/fpdf2-logo.png)

লিখার প্রিন্ট করার নতুন মেথড এখানে দেখানো হলো - 
 [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
। যা 
 [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
 এর খুব কাছাকাছি, মূল পার্থক্য হলো:

- লাইনের শেষ হয় ডানপ্রান্ত থেকে এবং পরের লাইনের শুরু হয় বামপ্রান্ত থেকে।
- বর্তমান অবস্থান লিখার একদম শেষে গিয়ে পৌছায়।

এই মেথডের মাধ্যমে কিছু টেক্সট একসাথে লিখা যায়, ফন্ট স্টাইল পরিবর্তন করা যায়, এবং যেই স্থান হতে লিখা 
 বন্ধ করা হয়েছে পুনরায় সেখান থেকেই শুরু করা যায়।
অন্যদিকে এই মেথডের মূল প্রতিবন্ধকতা হচ্ছে, টেক্সটগুলোকে জাস্টিফাই করা যায় না যেমনটা আমরা 
 [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) মেথডের 
 মাধ্যমে করতে পারি।

উদাহরণের প্রথম পৃষ্ঠায়, আমরা এই উদ্দেশ্যে 
 [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write) মেথড ব্যবহার করেছিলাম। 
 বাক্যের শুরুটা সাধারণ টেক্সট স্টাইলেই লিখা হয়েছে, এরপরে 
 [set_font()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) মেথড ব্যবহার করে, 
 আমরা আন্ডারলাইন করে বাক্যটি শেষ করলাম।

পরবর্তী পৃষ্ঠার একটি আন্তর্বর্তী লিংক যুক্ত করার জন্য, আমরা 
 [add_link()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link) মেথডটি ব্যবহার করেছি, 
 যা ক্লিক করার মত একটি এলাকা তৈরি করে দিলো যেটাকে আমরা "লিংক" বলছি যা ডকুমেন্ট এর ভেতরেরই অন্য একটি 
 পৃষ্ঠায় নিয়ে যায়।

ছবির মাধ্যমে একটি বাহ্যিক লিংক তৈরি করার জন্য, আমরা 
 [image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image) মেথডটি ব্যবহার করেছি। 
 এই মেথডের মাধ্যমে আর্গুমেন্ট হিসেবে লিংক পাস করার মত সুবিধা আছে। এই লিংক ডকুমেন্ট এর ভেতরকার বা বাইরের যেকোন 
 লিংকই হতে পারে।

বিকল্প হিসেবে ফন্ট স্টাইল এবং লিংক যুক্ত করার অন্য আরেকটি মাধ্যম আছে, সেটি হলো `write_html()` 
 মেথড ব্যবহার করা। এটা একটা html পারসার, যার মাধ্যমে html ব্যবহার করে টেক্সট যুক্ত করার, ফন্ট 
 স্টাইল পরিবর্তন করা এবং লিংক যুক্ত করা যায়।
