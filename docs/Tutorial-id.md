# Panduan

Dokumentasi secara lengkap: [`fpdf.FPDF` API doc](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Panduan 1 - Contoh Sederhana

Mari kita mulai dengan contoh sederhana:

```python
{% include "../tutorial/tuto1.py" %}
```

[Hasil PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto1.pdf)

Setelah menyertakan file library tersebut, kita buat objek `FPDF`. 
Konstruktor [FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) yang digunakan ini mempunyai nilai bawaan: 
halaman dalam format kertas A4 portrait dan satuan pengukuran dalam milimeter.
Ini juga dapat ditentukan secara eksplisit dengan:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

Kita juga dapat mengatur PDF dalam mode _landscape_ (`L`) atau menggunakan format halaman lainnya
(seperti `Letter` dan `Legal`) dan satuan ukuran (`pt`, `cm`, `in`).

Karena saat ini tidak ada halaman, kita harus menambahkannya dengan 
[add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). Titik awal kursor berada di pojok kiri atas dan
posisi yang sekarang ditempatkan 1 cm dari margin secara default; margin dapat
diubah dengan [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins).

Sebelum kita dapat mencetak teks, penting untuk memilih font dengan
[set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), jika tidak, dokumen akan menjadi tidak valid.
Kita pilih font Helvetica dengan ketebalan 16:

```python
pdf.set_font('helvetica', 'B', 16)
```

Kita dapat menentukan font _italic_ dengan `I`, bergaris bawah dengan `U`, atau jenis font reguler 
dengan _string_ kosong (atau kombinasi lain). Perlu dicatat bahwa ukuran font diberikan dalam 
satuan poin, bukan milimeter (atau satuan lainnya); ini adalah satu-satunya pengecualian. 
Font bawaan lainnya adalah `Times`, `Courier`, `Symbol`, dan `ZapfDingbats`.

Sekarang kita dapat mencetak _cell_ dengan [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). Sebuah _cell_ adalah area berbentuk persegi panjang 
yang berisi beberapa teks. _Cell_ tersebut dirender pada posisi kursor saat ini. 
Kita tentukan dimensinya, teksnya (di tengah atau rata kiri/kanan), apakah garis batas 
akan digambar, dan di mana posisi kursor bergerak setelahnya (ke kanan, 
ke bawah, atau ke awal baris berikutnya). Untuk menambahkan _frame_, kita dapat melakukannya seperti ini:

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

Untuk menambahkan _cell_ baru tepat disampingnya dengan teks rata tengah dan langsung ke baris selanjutnya,
kita bisa:

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**_Komentar_**: _line break_ atau menambah baris baru sekarang bisa dilakukan dengan [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln).
_Method_ ini dapat menentukan tinggi dari baris baru tersebut.

Terakhir, dokumen di atas ditutup dan disimpan dalam _file path_ yang ditentukan menggunakan
[output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Tanpa adanya _parameter_, `output()`
akan menghasilkan PDF `bytearray` buffer.

## Panduan 2 - Header, footer, page break dan gambar

Berikut adalah contoh dua halaman dengan header, footer dan logo:

```python
{% include "../tutorial/tuto2.py" %}
```

[Hasil PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto2.pdf)

Contoh di atas menggunakan _method_ [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) dan 
[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) untuk memproses header dan footer halaman. Keduanya
dipanggil secara otomatis. Keduanya sebenarnya sudah ada dalam _class_ FPDF namun tidak melakukan apapun,
sehingga kita harus meng-_extend_ _class_ tersebut dan menimpanya dengan preferensi kita.

Logo halaman dicetak dengan _method_ [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) dan dengan menentukan 
sudut kiri atas dan lebarnya. Tinggi gambar akan dihitung secara otomatis untuk
menjaga proporsi gambarnya.

Untuk mencetak nomor halaman, nilai kosong atau _null_ akan di-_passing_ sebagai lebar _cell_. Yang artinya, 
_cell_ harus memanjang hingga margin kanan halaman; hal ini berguna agar teks rata tengah.
Nomor halaman yang ada sekarang, dihasilkan oleh 
_method_ [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no); sedangkan untuk 
jumlah total halaman, dapat diperoleh dengan nilai khusus yaitu `{nb}`
yang akan diganti saat dokumen ditutup (nilai khusus tersebut dapat diubah dengan 
[alias_nb_pages()](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)).
Perhatikan penggunaan _method_ [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) yang dapat mengatur 
posisi dengan lokasi yang absolut dalam halaman, mulai dari atas atau
bawah.

Fitur menarik lain yang digunakan disini adalah _page break_ otomatis.
Begitu _cell_ sudah melewati batas di halaman (jarak 2cm dari bawah secara _default_),
_page break_ dilakukan dan font dikembalikan. Meskipun header dan 
footer memilih _font_ mereka sendiri (`helvetica`), _body_ halaman tetap menggunakan `Times`.
Mekanisme pemulihan otomatis ini juga berlaku untuk warna dan lebar garis.
Batas yang memicu _page break_ dapat diatur dengan
[set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).


## Panduan 3 - Line breaks dan warna

Mari kita lanjutkan dengan mencetak paragraf yang rata kiri dan kanan.
Contoh ini juga akan mengilustrasikan penggunaan warna.

```python
{% include "../tutorial/tuto3.py" %}
```

[Hasil PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto3.pdf)

[Contoh teks Jules Verne](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

_Method_ [get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) dapat menentukan 
panjang _string_ dalam sebuah font, yang digunakan untuk menghitung 
posisi dan lebar frame yang mengelilingi judul. Kemudian, warna dapat ditetapkan 
(melalui [set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color),
[set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) dan 
[set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)) dan ketebalan garis dapat ditetapkan
ke 1 mm (dibandingkan 0,2 secara default) dengan
[set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). Terakhir, kita output _cell_ 
(parameter terakhir bernilai _True_ menunjukkan bahwa background harus diisi).

_Method_ yang digunakan untuk mencetak paragraf adalah [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell). Teks akan rata kiri dan kanan secara default.
Setiap kali baris mencapai ujung kanan _cell_ atau terdapat karakter _carriage return_ (`\n`),
akan dimunculkan _line break_ dan _cell_ baru akan otomatis dibuat di bawah _cell_ tersebut.
Pembatasan otomatis dilakukan di lokasi spasi terdekat atau karakter _soft-hyphen_ (`\u00ad`) sebelum batas kanan halaman.
_Soft-hyphen_ akan diganti dengan tanda hubung biasa saat ada _line break_, dan diabaikan jika tidak.

Dua properti dokumen ditetapkan: judul
([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) dan penulis 
([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Properti tersebut dapat dilihat dengan dua cara.
Pertama adalah dengan membuka dokumen secara langsung dengan Acrobat Reader, masuk ke menu File 
dan pilih opsi Document Properties. Yang kedua, juga tersedia dari 
plug-in, adalah klik kanan dan pilih Document Properties.

## Panduan 4 - Multi Kolom

Contoh berikut adalah varian dari contoh sebelumnya, yang menunjukkan cara meletakkan teks di beberapa kolom.

```python
{% include "../tutorial/tuto4.py" %}
```

[Hasil PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto4.pdf)

[Contoh teks Jules Verne](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

Perbedaan utama dari tutorial sebelumnya adalah penggunaan 
_method_ [`text_columns`](fpdf/fpdf.html#fpdf.fpdf.FPDF.text_column).
_Method_ tersebut mengumpulkan semua teks secara bertahap dan mendistribusikan ke sejumlah kolom yang diminta, secara otomatis memasukkan _page break_ jika diperlukan. Perlu diperhatikan bahwa saat _instance_ `TextColumns` aktif sebagai _context manager_, gaya teks dan properti font lainnya dapat diubah. Perubahan tersebut akan dibatasi sesuai pada _context_ dalam _context manager_. Setelah ditutup, pengaturan sebelumnya akan dikembalikan.


## Panduan 5 - Membuat tabel

Panduan ini akan menjelaskan tentang cara membuat dua tabel berbeda 
dengan beberapa penyesuaian sederhana.

```python
{% include "../tutorial/tuto5.py" %}
```

[Hasil PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Data CSV Negara-negara](https://github.com/py-pdf/fpdf2/raw/master/tutorial/countries.txt)

Contoh pertama dapat dicapai dengan cara yang mudah, yaitu memasukkan data ke [`FPDF.table()`](https://py-pdf.github.io/fpdf2/Tables.html). Hasil yang didapatkan memang sangat simpel, tetapi sangat cepat untuk dibuat.

Tabel kedua menghadirkan beberapa perbaikan: warna, lebar tabel yang dibatasi, tinggi baris yang berkurang,
judul dengan rata tengah, kolom dengan lebar custom, gambar yang rata kanan...
Selain itu, garis horizontal telah dihapus.
Hal ini dilakukan dengan memilih `border_layout` di antara nilai yang tersedia: 
[`TableBordersLayout`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TableBordersLayout).

## Panduan 6 - Membuat tautan dan mencampur gaya teks

Dalam panduan ini akan dijelaskan beberapa cara untuk menyisipkan tautan di dalam dokumen PDF,
serta menambahkan tautan ke sumber eksternal.

Panduan ini juga akan menunjukkan beberapa cara untuk menggunakan gaya teks yang berbeda, 
(tebal, miring, garis bawah) dalam teks yang sama.

```python
{% include "../tutorial/tuto6.py" %}
```

[Hasil PDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto6.pdf) -
[Logo fpdf2](https://raw.githubusercontent.com/py-pdf/fpdf2/master/docs/fpdf2-logo.png)

_Method_ baru yang ditunjukkan disini untuk mencetak teks adalah 
[write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
. Ini sangat mirip dengan 
[multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
, perbedaan utamanya adalah:

- Akhir baris berada di margin kanan dan baris berikutnya dimulai di 
margin kiri.
- Posisi kursor berpindah ke akhir teks.

Oleh karena itu, _method_ ini dapat digunakan untuk menulis sepotong teks, mengubah gaya font, 
dan melanjutkan dari tempat yang sama persis dengan tempat terakhir kursor berhenti.
Di sisi lain, kelemahan utamanya adalah kita tidak bisa membuat teks rata kiri dan kanan seperti 
saat menggunakan 
_method_ 
[multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell).

Pada halaman pertama contoh, kita menggunakan 
[write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write).
Awal kalimat ditulis dalam gaya teks biasa,
kemudian menggunakan
_method_ [set_font()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font),
kita ganti menggunakan garis bawah dan mengakhiri kalimatnya.

Untuk menambahkan tautan internal yang mengarah ke halaman kedua, kita dapat menggunakan 
_method_ [add_link()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link),
yang membuat area yang dapat diklik yang biasa disebut "link" yang mengarah ke 
halaman lain dalam dokumen.

Untuk membuat tautan eksternal menggunakan gambar, kita dapat menggunakan 
[image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image).
_Method_ ini 
mempunyai opsi untuk _passing_ tautan sebagai salah satu argumennya. Tautan tersebut dapat berupa tautan internal 
atau eksternal.

Sebagai alternatif, opsi lain untuk mengubah gaya font dan menambahkan tautan adalah dengan 
menggunakan _method_ `write_html()`. _Method_ tersebut merupakan parser HTML yang dapat menambahkan teks, 
mengubah gaya font, dan menambahkan tautan menggunakan HTML.
