# チュートリアル #

Methods full documentation: [`fpdf.FPDF` API doc](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Tuto 1 - 簡単な使用例 ##

まずは、単純な使用例から始めましょう。

```python
{% include "../tutorial/tuto1.py" %}
```

[生成されるPDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto1.pdf)

ライブラリをインポートした後、`FPDF` オブジェクトを作成します。
上の例では、[FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) コンストラクタはデフォルト値を利用します(A4サイズ縦向きのページとミリメーター単位)。
次のようにして、明示的に指定することも可能です。

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

PDFを横向き(`L`)に設定したり、他のページサイズ(`Letter`, `Legal` など)や
単位(`pt`, `cm`, `in`)を設定することも可能です。

（訳注） 縦向き（portrait）、横向き（landscape）の頭文字で向きを指定します。

この時点ではPDFファイルにページが存在しないため、[add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page)でページを追加します。
原点は左上隅で、現在の位置はデフォルトでページ端から1cmの場所になります。
余白は[set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins) で変更可能です。

テキストを表示する前に、[set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) で
フォントを選択する必要があります。今回はHelvetica bold 16 を選択します。

```python
pdf.set_font('helvetica', 'B', 16)
```

`I`で斜体、`U`で下線、空文字列で通常のフォント（または任意の組み合わせ）を指定することができます。
フォントサイズはミリメートル（または他のユーザー単位）ではなくポイントで指定することに注意してください。他の内蔵フォントは`Times`、`Courier`、`Symbol`、`ZapfDingbats`です。

これでセルを [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) で表示できるようになりました。
セルとは、テキストを含む長方形の領域で、現在の位置に描画されます。
寸法、テキスト（配置）、ボーダーの有無、そして現在の位置が次に移動する先（右、下、次の行頭）を指定します。
ボーダー付きで描画するには次のようにします。

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

その隣に新しいセルを中央揃えのテキストで追加し、次の行に進むには、次のようにします。

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**備考**: 改行は [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln) でも可能です。`ln` メソッドは、改行時の高さを指定することができます。

最後に、[output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output) で、指定した場所にPDFを保存します。引数なしの `output()`は PDFの `bytearray`を返します。

## Tuto 2 - ヘッダー、フッターと改ページ、画像 ##

ヘッダー、フッター、ロゴのある2ページのPDFを生成するサンプルです。

```python
{% include "../tutorial/tuto2.py" %}
```

[生成されるPDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto2.pdf)

この例では、[header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) と
[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer)メソッドを使用して、ページのヘッダーとフッターを処理しています。
これらのメソッドは自動的に呼び出されます。
FPDFクラスはこれらのメソッドを持っていますが、何もしません。
そのため、クラスを継承してメソッドをオーバーライドする必要があります。

ロゴは、左上隅の位置と幅を指定して、[image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image)メソッドによって表示されます。
高さは画像の縦横比から自動的に計算されます。

ページ番号を表示するには、セルの幅にnull valueを渡します。
これによって、セルがページの右の余白まで広がります。これはテキストを中央寄せする場合に便利です。
現在のページ番号は [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) メソッドで取得できます。
総ページ数はドキュメント終了時に置換される特殊な値 `{nb}` によって取得できます（この特殊な値は[alias_nb_pages()](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages) によって変更できます）。
[set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) メソッドを使うことで、ページの上部もしくは下部からの絶対位置を指定できます。

ここで使用されているもう一つの興味深い機能は、自動改ページ機能です。
セルがページの限界（デフォルトでは下から2cm）を超えると改行され、フォントが元に戻ります。
ヘッダーとフッターは独自のフォント（`helvetica`）を使用しますが、本文は`Times` を使用し続けます。
この自動復帰の仕組みは、色と行幅にも適用されます。
この改ページのトリガーとなるページの限界は [set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break) で設定できます。


## Tuto 3 - 改行と色 ##

続いて、複数の段落を文字揃えして表示する例を見てみましょう。同時に、色の使い方についても学びます。

```python
{% include "../tutorial/tuto3.py" %}
```

[生成されるPDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto3.pdf)

[PDF中の本文（Jules Verne text）](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

[get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) メソッドは現在のフォントでの文字列の幅を求めることができ、ここではタイトルを囲む枠の位置と幅を計算するために使われています。
次に、色を指定し（[set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color)、 [set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color)、 
[set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color) を利用）、 
線の太さをset_line_widthで1mmに設定します（デフォルトでは0.2）。
最後に、セルを出力します（最後のパラメータをtrueにして、背景の塗りつぶしを有効にします。）。

段落を表示するためには [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) メソッドを利用します。
テキストはデフォルトで両端揃えされます。
行がセルの右端に届くか、改行文字（`\n`）のたびに改行され、現在のセルの下に新しいセルが自動的に作成されます。
自動改行は、右端に最も近いスペースかソフトハイフン（`\u00ad`）の位置で行われます。
ソフトハイフンは改行をトリガーする場合は通常のハイフンに置き換えられ、そうでない場合は無視されます。

この文書には、タイトル（[set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)）と著者（[set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)）の2つの文書プロパティがセットされています。
プロパティは2つの方法で見ることができます。
1つ目は、Acrobat Readerで直接文書を開き、「ファイル」メニューから「プロパティ」オプションを選択する方法です。
もう1つは、プラグインからも利用できますが、右クリックして「ドキュメントのプロパティ」を選択する方法です。

## Tuto 4 - 段組み ##

この例では、前の例の派生版として、複数列に渡ってテキストを配置する（段組み）方法を紹介します。

```python
{% include "../tutorial/tuto4.py" %}
```

[生成されるPDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto4.pdf)

[PDF中の本文（Jules Verne text）](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

前回のチュートリアルとの大きな違いは、[accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) メソッドと set_col メソッドの 使用です。

[accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) メソッドは、セルがページの下端に到達した際に、現在の列番号をチェックします。
列番号が2より小さい場合（今回はページを3分割にする）、set_col メソッドを呼び出し、列番号のインクリメントと次の列の位置への変更を行います。

3列目の下端に到達すると、[accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) メソッドはリセットされて1列目に戻り、改ページが実行されます。

## Tuto 5 - 表の作成 ##

このチュートリアルでは、簡単な調整で何ができるのかを示すために、
2種類のテーブルの作成方法について解説します。

```python
{% include "../tutorial/tuto5.py" %}
```

[生成されるPDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto5.pdf) -
[国別CSVデータ](https://github.com/py-pdf/fpdf2/raw/master/tutorial/countries.txt)

1つ目の例は最も基本的な方法で、[`FPDF.table()`](https://py-pdf.github.io/fpdf2/Tables.html) にデータを与えています。
結果は単純なものですが、非常に短時間で作成できます。

2つ目の例ではいくつかの改善を加えています。色、テーブルの幅の制限、行の高さの縮小、中央寄せされたタイトル、列幅の指定、右寄せの数値などに加え、行を区切る横線を削除しています。
これは、[`TableBordersLayout`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TableBordersLayout) の `borders_layout` を指定することで行うことができます。

## Tuto 6 - リンクの作成と、テキストスタイルの組み合わせ ##

このチュートリアルでは、PDF文書内にリンクを埋め込むいくつかの方法を紹介します。
同様の方法で、外部リンクも作成可能です。

また、1つのテキスト内で複数のスタイリング（太字、斜体、下線）を使用する方法についても解説します。

```python
{% include "../tutorial/tuto6.py" %}
```

[生成されるPDF](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://raw.githubusercontent.com/py-pdf/fpdf2/master/docs/fpdf2-logo.png)

ここではテキストを表示するための新しい方法として、 [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write) を使っています。
このメソッドは [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) と非常によく似ており、重要な違いとしては次があります。

- 行末は右の余白、行頭は左の余白から始まる
- 現在の位置はテキストの終わりに移動する

したがって、このメソッドを用いてテキストのまとまりを書き込み、フォントスタイルを変更し、
さらにその続きからテキストを書き込むことができます。
一方でこの方法の欠点は、 [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) メソッドで行ったようなテキストの字揃えが行えないことです。

この例の1ページ目では、[write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write) をフォントスタイルの変更に使用しています。文章の始めには通常のスタイルのテキストですが、 [set_font()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font) メソッドを用いて下線を追加しています。

2ページ目への内部リンクを作成するには、
 [add_link()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link)
 メソッドを使用します。
 このメソッドは「link」と名付けられたクリック可能なエリアを作成し、
 文書内の別のページに移動させます。

画像を利用した外部リンクを作成するために、ここでは
 [image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image)
 メソッドを使っています。
このメソッドは引数の1つとしてリンクを受け取ります。このリンクは内部リンクでも外部リンクでも問題ありません。

別の方法として、`write_html()` メソッドを使用してフォントスタイルの変更やリンクの作成を行うことも出来ます。
このメソッドはHTMLパーサーであり、テキストの追加、フォントスタイルの変更、リンクの作成をHTMLを用いて行なえます。
