# 使用教程 #

完整说明文件：
[`fpdf.FPDF` API 文档](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## 教程一 - 简单的示例 ##

一个经典的示例：

```python
{% include "../tutorial/tuto1.py" %}
```

[生成的 PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

引入库文件后，创建`FPDF`对象。
[FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF)
构造函数在此使用默认值：页面 A4 纵向；单位毫米。
当然，这可以被明确定义：

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

同时，也可以将 PDF 设置为横向模式 (`L`) 或使用其他页面格式
（如 `Letter` 和 `Legal`）和度量单位（`pt`、`cm`、`in`）。

到此，文件暂无页面。调用
[add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page)
添加页面，原点位于页面左上角，当前位置默认为距边界 1 厘米处。
边距也可以调用
[set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins) 更改。

在加入文本之前，必须选定字体
[set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
，否则文件无效。
选择字体 Helvetica，粗体，16号：

```python
pdf.set_font('helvetica', 'B', 16)
```

使用 `I` 指定斜体，`U` 加下划线或空字符串指定常规字体。
请注意，字号单位是点数，而非毫米（或其他指定的单位）。
这是单位设置的唯一例外。其他内置字体有
`Times`、`Courier`、`Symbol` 与 `ZapfDingbats`。

调用 [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) 
创建一个单元格。单元格是一个矩形区域，可能带有外框，
其中包含一些文本，且置于当前位置。
单元格的尺寸，排版（居中或对齐），是否有边框
，以及所放置的位置（向右，向下或换行）可配置的。
添加一个框架：

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

添加一个文本居中的新单元格并换行，如下：

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**备注**：换行也可调用
[ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln)
实现。此方法允许指定换行行距。

最终，关闭文件并保存于给定路径
[output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output)。
无参数时，`output()`返回 PDF `bytearray` 缓冲区。

## 教程二 - 页眉、页脚、分页符与图像 ##

此教程使用了下述包含页眉、页脚和徽标的示例：

```python
{% include "../tutorial/tuto2.py" %}
```

[生成的 PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)

此示例使用 
[header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) 与
[footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) 
处理页眉和页脚。
虽然二者属于 FPDF 类，被自动调用，但默认是空置的，
因此需要扩展类从而覆盖缺省值。

调用 [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) 
依照指定的起始坐标（左上角）与宽度添加图标。
高度将依照图像比例自动计算。

可将空值作为单元格宽度以打印页码。这使单元格延伸到页面的右边缘，
便于文本居中。当前页码由
[page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no) 
返回。至于总页数，可以通过值`{nb}`获得。
`{nb}`将在文档关闭时被替换（此值调用
[alias_nb_pages()](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)
更改)。注意，调用 
[set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) 
能够从顶部或底部起，设置在页面中的绝对位置。

示例中使用了另一个有趣的特性：自动分页。
一旦单元格会越过页面中的限制（默认距离底部 2 厘米处），
将执行中断并恢复字体设置。
虽然标题和页脚仍然使用自身的字体（`helvetica`），但正文将继续使用 `Times` 字体。
这种自动恢复机制同样适用于字体颜色与行距。
触发分页符的机制可以通过
[set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break) 配置。


## 教程三 - 换行符和颜色 ##

让我们继续上述对齐段落的示例。此教程也将演示颜色的配置方法。

```python
{% include "../tutorial/tuto3.py" %}
```

[生成的 PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto3.pdf)

[儒勒·凡尔纳的原文](https://github.com/PyFPDF/fpdf2/raw/mast呃/教程/20k_c1.txt）

调用 [get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) 
函数设定当前字体下字符串的长度，
从而计算当前位置标题外框的宽度。
通过 [set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color)、
[set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color)和
[set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)
设置颜色。行距由 
[set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width) 
设定为 1 mm（默认为 0.2）。
最终，输出单元格（末位参数 true 表示必须填充背景）。

调用[multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
函数打印段落（文本默认对齐）。
每当到达单元格的右端或遇到回车符 (`\n`) 时，
换行并在当前单元格下自动创建一个新的单元格。
自动换行在右起最近的空格或软连字符 (`\u00ad`) 触发。
当触发换行符时，软连字符将被普通连字符替换，否则将被忽略。

示例中设定了两个文档属性：标题
([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) 
与作者
([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author))。
文档的属性可以直接用 Acrobat 阅读器 打开，
在文件菜单中选择文档属性查看；
也可以使用插件，右击并选择 文档属性 查看。

## 教程四 - 多栏目 ##

此示例是上一个示例的变体，展示了如何将文本放置在多个栏目中。

```python
{% include "../tutorial/tuto4.py" %}
```

[生成的 PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto4.pdf)

[儒勒·凡尔纳的原文](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

与上一个教程的主要区别在于使用了
[accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) 
与 set_col 方法。

在 [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) 
函数中，一当单元格越过页面的底部，
若当前列号小于2（页面分为三列），则调用 set_col，
递增列号并移动到下一列的位置，继续打印文本。

一旦达到第三列的底部，
[accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) 
将分页并回到第一列。

## 教程五 - 创建表 ##

```python
{% include "../tutorial/tuto5.py" %}
```

[生成的 PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto5.pdf) -
[源文本](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/countries.txt)

_⚠️ This section has changed a lot and requires a new translation: <https://github.com/PyFPDF/fpdf2/issues/267>_

English versions:

* [Tuto 5 - Creating Tables](https://pyfpdf.github.io/fpdf2/Tutorial.html#tuto-5-creating-tables)
* [Documentation on tables](https://pyfpdf.github.io/fpdf2/Tables.html)

## 教程六 - 创建链接和混合文本样式 ##

本教程将演示几种在 pdf 文档中插入内部链接，或指向外部资源
的超链接的方法，以及几种在同一文本中使用不同文本样式
（粗体、斜体、下划线）的方法。

```python
{% include "../tutorial/tuto6.py" %}
```

[生成的 PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2 图标](https://raw.githubusercontent.com/PyFPDF/fpdf2/master/docs/fpdf2-logo.png)

此处显示的打印文本的新方法是
[write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
，类似于
[multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
。二者主要区别在于：

- 行尾在右边缘，下一行在左边缘开始
- 当前位置移动到文本末尾。

因此，该方法允许在一段文本中更改字体样式，并从初始位置继续。
反之，它的缺点在于其不能如同
[multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell)
对齐文本。

因为上述原因，在示例的第一页中，调用了
[write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
打印常规字体，然后使用
[set_font()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font)
方法，切换到下划线样式并继续打印。

为添加指向第二页的内部链接，调用了
[add_link()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link)
。这将创建一个可点击区域，命名为“链接”，指向
文档中的另一页。

使用图像创建外部链接，则调用
[image()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image)
。该函数可将链接作为其参数之一。链接也可以指向内部或外部。

作为替代方案，更改字体样式和添加链接的另一种选择是
使用 `write_html()` 方法。这是一个 html 解析器，
允许添加文本，更改字体样式并添加链接。

