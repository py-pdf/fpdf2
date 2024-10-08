# Öğretici

Metodların tam dökümantasyonu: [`fpdf.FPDF` API dökümanı](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Öğretici 1 - Minimal Örnek

Hadi klasik bir örnekle başlayalım:

```python
{% include "../tutorial/tuto1.py" %}
```

[Sonuç PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto1.pdf)

Kütüphaneyi dahil ettikten sonra, `FPDF` objesi oluşturuyoruz. 
[FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) oluşturucusu buradaki varsayılan değerleri kullanır: 
sayfalar dikey A4 formatında ve milimetre cinsinden ölçülüdür.
Ayrıca bu şekilde açıkça da belirtilebilir:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

Diğer sayfa formatları (`Letter` ve `Legal` gibi) ve ölçü birimleri (`pt`, `cm`, `in`) de 
kullanılabilir.

Şu an için bir sayfamız yok, bu yüzden bir tane eklememiz gerekiyor 
[add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). Başlangıç noktası sol üst köşededir ve
geçerli konum varsayılan olarak sınırlardan 1 cm uzağa yerleştirilir; kenar boşlukları
[set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins) ile değiştirilebilir.

Metni yazdırmadan önce, aşağıdaki özelliklere sahip bir yazı tipi seçmek zorunludur 
[set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), aksi takdirde belge geçersiz olur.
Helvetica bold 16'yı seçiyoruz:

```python
pdf.set_font('helvetica', 'B', 16)
```

Yazı tipi stilleriyle oynayabiliriz. Örneğin, italikleri `I` ile, altı çizgili `U` ile 
veya düz bir yazı tipiyle boş bir dizeyle (veya herhangi bir kombinasyonla) belirtebiliriz. 
Yazı tipi boyutu puan cinsinden belirtilir, milimetre (veya başka bir kullanıcı birimi) 
değil; bu tek istisnadır. Diğer yerleşik yazı tipleri `Times`, `Courier`, `Symbol` ve `ZapfDingbats`'tir.

Artık bir hücreyi [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) ile yazdırabiliriz. Hücre,
muhtemelen çerçeveli, metin içeren bir dikdörtgen alanıdır. Hücre geçerli konumda
oluşturulur. Boyutlarını, metnini (merkezlenmiş veya hizalanmış), çerçevelerinin çizilip
çizilmeyeceğini ve sonrasında nereye gidileceğini (sağa, aşağıya veya bir sonraki satırın başına) belirtiriz. 
Bir çerçeve eklemek için şunu yapabiliriz:

```python
pdf.cell(40, 10, 'Merhaba Dünya!', 1)
```

Yanına merkezlenmiş metin eklemek ve bir sonraki satıra gitmek için, şunu yapabiliriz:

```python
pdf.cell(60, 10, 'FPDF tarafından oluşturuldu.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**Not**: Satır sonu ayrıca [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln) ile de yapılabilir. Bu
metot ayrıca, satır aralığını belirtmeye de olanak tanır.

Son olarak, belge kapatılır ve verilen dosya yoluna kaydedilir.
[output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Herhangi bir parametre sağlanmadığında, `output()`
PDF `bytearray` buffer değerini döndürür.

## Öğretici 2 - Başlık, altbilgi, sayfa sonu ve resim

Şimdi bir başlık, altbilgi ve logo içeren iki sayfalık bir örnek yapalım:

```python
{% include "../tutorial/tuto2.py" %}
```

[Sonuç PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto2.pdf)

Bu örnek, sayfa başlıklarını ve altbilgilerini işlemek için [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) ve
[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) metodlarını kullanır. Bunlar otomatik olarak çağrılır.
Bu özellikler FPDF sınıfında zaten mevcuttur ancak varsayılan olduklarından boşturlar, bu yüzden sınıfı 
genişletmeli ve içeriklerini doldurarak onları özelleştirmeliyiz.

Logo, [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) metoduyla üst sol köşesini ve genişliğini belirterek yazdırılır.
Yükseklik otomatik olarak hesaplanır ve resmin oranlarını korumak için kullanılır.

Sayfa numarasını yazdırmak için, hücre genişliği olarak null bir değer geçilir. 
Bu, metnin sağ kenarına kadar uzanması gerektiği anlamına gelir; metni ortalamak için kullanışlıdır. 
Geçerli sayfa numarası [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) metodu ile alınır; 
toplam sayfa sayısı ise belge kapatıldığında `{nb}` ile değiştirilecek özel bir değerle alınır 
(bu özel değer [alias_nb_pages()](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages) ile değiştirilebilir). 
Not olarak, [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) metodu, sayfanın üstünden veya altından 
başlayarak mutlak bir konum belirlemeye izin verir.

Burada kullanılan başka ilginç bir özellik de otomatik sayfa sınırlandırmalarıdır. Bir hücre sayfanın bir sınırını
geçeceği anda (varsayılan olarak alttan 2 cm uzakta) bir kesme gerçekleştirilir ve yazı tipi geri yüklenir.
Başlık ve altbilgi kendi yazı tipini (`helvetica`) seçerken, gövde `Times` ile devam eder.
Bu otomatik geri yükleme mekanizması, renkler ve çizgi kalınlığı için de geçerlidir.
Sayfa kesimlerini tetikleyen sınır,
[set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break) ile ayarlanabilir.

## Öğretici 3 - Satır sonları ve renkler

Şimdi, paragrafları hizalayarak yazdıran bir örneğe devam edelim. Ayrıca renklerin nasıl kullanılacağını gösterir.

```python
{% include "../tutorial/tuto3.py" %}
```

[Sonuç PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto3.pdf)

[Jules Verne metni](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

[get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) metodu, 
kullanılan yazı tipindeki bir dizenin uzunluğunu belirlemeye olanak tanır. Bu, başlığı çevreleyen kısmın
konumunu ve genişliğini hesaplamak için kullanılır. Ardından renkler ayarlanır
([set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color),
[set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) ve
[set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)) ve çizgi kalınlığı
varsayılan 0.2 mm'ye karşı 1 mm'ye ayarlanır
[set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). Son olarak, hücre çıktısı yapılır
(arka planın doldurulması gerektiğini belirten son parametre true'dur).

Paragrafları yazdırmak için kullanılan yöntem [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) metotudur.
Metin varsayılan olarak hizalanır. Her bir satır sağ sınırı hücrenin sağ kenarına ulaştığında veya 
bir satır sonu karakteri (`\n`) karşılaşıldığında, bir satır sonu verilir ve yeni bir hücre 
otomatik olarak mevcut hücrenin altına oluşturulur. Otomatik bir kesme, en yakın boşluğa veya 
yumuşak kısa çizgi karakterine (`\u00ad`) sağ sınıra ulaşıldığında gerçekleştirilir. 
Bir satır sonu tetiklendiğinde, bir yumuşak kısa çizgi normal bir kısa çizgiyle değiştirilir 
ve aksi takdirde yoksayılır.

İki belge özelliği tanımlanmıştır: başlık 
([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) ve yazar 
([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Özellikler iki şekilde görülebilir.
İlk olarak, belgeyi doğrudan Acrobat Reader ile açarak, Dosya menüsüne gidin ve Belge Özellikleri seçeneğini seçin.
İkincisi, eklentiden de mevcut olan, belge özelliklerini sağ tıklayarak seçmek.

## Öğretici 4 - Çoklu Sütunlar

 Bu örnek, metni birden fazla sütuna yayarak, metni birden fazla sütuna yayarak nasıl yapılacağını gösterir.
 This example is a variant of the previous one, showing how to lay the text across multiple columns.

```python
{% include "../tutorial/tuto4.py" %}
```

[Sonuç PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne metni](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

Önceki öğreticiyle ana fark, 
[`text_columns`](fpdf/fpdf.html#fpdf.fpdf.FPDF.text_column) metodunun kullanılmasıdır.
Metni toplar ve istenen sütun sayısına dağıtır, gerekirse otomatik olarak sayfa kesmeleri ekler.
`TextColumns` örneği bir bağlam yöneticisi olarak etkin olduğunda, metin stilleri ve diğer yazı tipi özellikleri değiştirilebilir.
Bu değişiklikler bağlamla sınırlı olacaktır. Kapatıldığında önceki ayarlar yeniden yüklenecektir.

## Öğretici 5 - Tablolar Oluşturma

Bu öğretici, iki farklı tablo oluşturmayı açıklar, basit ayarlamalarla nelerin elde edilebileceğini göstermek için.

```python
{% include "../tutorial/tuto5.py" %}
```

[Sonuç PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Ülkelerin CSV verisi](https://github.com/py-pdf/fpdf2/raw/master/tutorial/countries.txt)

İlk örnek mümkün olan en basit yöntem ile elde edilebilir, verileri [`FPDF.table()`](https://py-pdf.github.io/fpdf2/Tables.html) metoduna vererek.
Sonuç basit olsa da çok hızlı bir şekilde elde edilir.

İkinci tablo bazı iyileştirmeler getirir: renkler, sınırlı tablo genişliği, azaltılmış satır yüksekliği,
 başlıkların ortalanması, özel genişliklere sahip sütunlar, rakamların sağa hizalanması...
 Ayrıca yatay çizgiler kaldırılmıştır.
 Bu, mevcut değerler arasından bir `borders_layout` seçilerek yapılmıştır:
 [`TableBordersLayout`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TableBordersLayout).

## Öğretici 6 - Bağlantılar Oluşturma ve Metin Stillerini Harmanlayarak Kullanma

Bu öğretici, bir pdf belgesi içine bağlantılar eklemenin birkaç yolunu açıklar,
 ayrıca dış kaynaklara bağlantı eklemeyi gösterir.

 Ayrıca, aynı metin içinde farklı metin stillerini (kalın, italik, altı çizili) nasıl kullanabileceğimizi gösterecektir.

```python
{% include "../tutorial/tuto6.py" %}
```

[Sonuç PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://raw.githubusercontent.com/py-pdf/fpdf2/master/docs/fpdf2-logo.png)

Bu öğreticide, metin yazdırmak için gösterilen yeni yöntem
 [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
. Burada gösterilen yeni yöntem, metni yazdırmak için kullanılan
 [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
 metoduna oldukça benzer, temel farklar şunlardır:

- Satır sonu sağ kenarda ve bir sonraki satır sol kenarda başlar.
- işaretçi konum metnin sonuna taşınır.

Bu yöntem, bir metin parçası yazmamıza, yazı tipi stilini değiştirmemize ve kaldığımız yerden devam etmemize olanak tanır.
Öte yandan, metni
 [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
 metoduyla olduğu gibi düzgün hizalayamayız.

İlk sayfada, bu amaçla
 [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
 kullanıldı. Cümlenin başlangıcı düz yazı tipinde yazıldı, ardından
 [set_font()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
 metoduyla altı çizili haline getirildi ve cümle tamamlandı.

İkinci sayfaya yönlendiren bir iç bağlantı eklemek için, ikinci sayfayı ekledik ve
 [add_link()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link)
 metoduyla ikinci sayfaya yönlendiren bir bağlantı linki oluşturduk.

Dış bağlantı oluşturmak için bir resim kullanarak dış bağlantı oluşturduk
    [image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image)
. Metodun bir bağlantıyı bir argüman olarak geçme seçeneği vardır. Bağlantı hem iç hem de dış bağlantı olabilir.

Alternatif olarak, yazı tipi stilini değiştirmek ve bağlantılar eklemek için başka bir seçenek de
 `write_html()` yöntemini kullanın. Metin eklemeyi sağlayan bir html ayrıştırıcıdır,
 yazı tipi stilini değiştirme ve html kullanarak bağlantı ekleme özelliklerine sahiptir.
