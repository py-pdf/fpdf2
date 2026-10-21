# Tutorial #

Documentação completa dos métodos: [`fpdf.FPDF` API doc](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

## Tuto 1 - Exemplo Mínimo ##

Vamos começar com um exemplo clássico:

```python
{% include "../tutorial/tuto1.py" %}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto1.pdf)

Após incluirmos o ficheiro da biblioteca, criamos um objeto `FPDF`. O construtor
[FPDF](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF) é usado aqui com os valores por omissão:
as páginas ficam em A4 vertical e a unidade de medida é o milímetro.
Isso poderia ter sido especificado explicitamente com:

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

É possível colocar o PDF em modo horizontal (`L`) ou em outros formatos de página
(como `Letter` e `Legal`) e em outras unidades de medida (`pt`, `cm`, `in`).

Neste momento, não há nenhuma página, então temos que adicionar uma com
[add_page](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). A origem está no canto superior esquerdo e a posição atual é, por padrão, colocada a 1 cm das bordas; as margens podem ser alteradas com [set_margins](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins).

Antes de imprimirmos o texto, é obrigatório selecionar uma fonte com
[set_font](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), caso contrário, o documento será inválido.
Nós escolhemos Helvetica bold 16:

```python
pdf.set_font('Helvetica', style='B', size=16)
```
Podemos formatar em itálico com `I`, sublinhar com `U` ou uma fonte normal
com uma string vazia (ou qualquer combinação). Observe que o tamanho da fonte é fornecido em pontos, não milímetros (ou outra unidade do utilizador); esta é a única exceção.
As outras fontes integradas são `Times`, `Courier`, `Symbol` e `ZapfDingbats`.

Agora podemos imprimir uma célula com [cell](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). Uma célula é uma área retangular, possivelmente emoldurada, que contém algum texto. É renderizada na posição atual. Nós especificamos as suas dimensões, o seu texto (centrado ou alinhado), se as bordas devem ser desenhadas, e para onde a posição atual se deve mover depois dela (para a direita, abaixo ou no início da próxima linha). Para adicionar uma moldura, temos de fazer o seguinte:

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

Para adicionar uma nova célula ao lado desta, com texto centralizado e ir para a próxima linha, teríamos de fazer:

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**Nota**: a quebra de linha também pode ser feita com [ln](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). Esse método permite especificar, adicionalmente, a altura da quebra.

Finalmente, o documento é fechado e guardado no caminho do arquivo fornecido utilizando
[output](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Sem termos qualquer parâmetro fornecido, `output()` retorna o buffer PDF `bytearray`.

## Tuto 2 - Cabeçalho, rodapé, quebra de página e imagem ##

Aqui temos um exemplo de duas páginas com cabeçalho, rodapé e logótipo:

```python
{% include "../tutorial/tuto2.py" %}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto2.pdf)

Este exemplo usa os métodos [header](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.header) e [footer](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) para processar cabeçalhos e rodapés de página. Estes são chamados automaticamente. Eles já existem na classe FPDF, mas não fazem nada, portanto temos de estender a classe e sobrescrevê-los.

O logótipo é impresso utilizando o método [image](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image), especificando o seu canto superior esquerdo e sua largura. A altura é calculada automaticamente para respeitar as proporções da imagem.

Para imprimir o número da página, um valor nulo é passado como a largura da célula. Isso significa que a célula deve se estender até a margem direita da página; é útil para centralizar texto. O número da página atual é retornado pelo método [page_no](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no); quanto ao número total de páginas, é obtido por meio do valor especial `{nb}` que será substituído quando se fecha o documento (este valor especial pode ser alterado com
[alias_nb_pages()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages)).
Observe que o uso do método [set_y](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) permite definir a posição em um local absoluto da página, começando do início ou do fim.

Outro recurso interessante que se usa aqui é a quebra de página automática. Desde o momento em que uma célula cruza o limite da página (a 2 centímetros da parte inferior por
padrão), uma quebra é feita e a fonte restaurada. Embora o cabeçalho e o rodapé selecionem a sua própria fonte (`helvetica`), o corpo continua com `Times`.
Este mecanismo de restauração automática também se aplica a cores e largura de linha.
O limite que dispara quebras de página pode ser definido com
[set_auto_page_break](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).

## Tuto 3 - Quebras de linha e cores ##

Vamos continuar com um exemplo que imprime parágrafos justificados e o uso de cores.

```python
{% include "../tutorial/tuto3.py" %}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto3.pdf)

[Texto de Júlio Verne](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

O método [get_string_width](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) permite determinar o comprimento de uma string na fonte atual, o que é usado aqui para calcular a posição e a largura do quadro ao redor do título. Em seguida, as cores são definidas (via [set_draw_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), [set_fill_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) e [set_text_color](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)) e a espessura da linha é definida como 1 mm (contra 0,2 por padrão) com [set_line_width](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). Finalmente, produzimos a célula (se o último parâmetro for verdadeiro, indica que o plano de fundo deve ser preenchido).

O método usado para imprimir os parágrafos é [multi_cell](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell). O texto é justificado por padrão.
Cada vez que uma linha atinge a extremidade direita da célula ou um caractere de fim de linha (`\n`) é encontrado,
uma quebra de linha é emitida e uma nova célula é criada automaticamente sob a atual.
A quebra automática é feita no espaço ou hífen suave (`\u00ad`) mais próximo antes do limite direito.
Um hífen suave é substituído por um hífen normal quando provoca uma quebra de linha e é ignorado nos outros casos.

Duas propriedades do documento são definidas: o título
([set_title](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) e o autor
([set_author](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). As propriedades podem ser visualizadas de duas maneiras:
A primeira é abrir o documento diretamente no Acrobat Reader, ir ao menu Arquivo
e escolher a opção Propriedades do documento.
A segunda, também disponível no plug-in, é clicar com o botão direito e selecionar Propriedades do documento.

## Tuto 4 - Multi Colunas ##

Este exemplo é uma variante do anterior, mostrando como distribuir o texto em várias colunas.

```python
{% include "../tutorial/tuto4.py"%}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto4.pdf)

[Texto de Júlio Verne](https://github.com/py-pdf/fpdf2/raw/master/tutorial/20k_c1.txt)

A principal diferença em relação ao tutorial anterior é o uso do método
[`text_columns`](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.text_columns).
Ele reúne todo o texto, possivelmente em partes, e o distribui pelo número de colunas pedido, inserindo quebras de página automaticamente quando necessário. Observe que, enquanto a instância de `TextColumns` estiver ativa como gerenciador de contexto, os estilos de texto e as outras propriedades da fonte podem ser alterados. Essas alterações ficam restritas ao contexto. Quando ele é fechado, as configurações anteriores são restabelecidas.


## Tuto 5 - Criar Tabelas ##

Este tutorial explica como criar duas tabelas diferentes,
para mostrar o que se consegue com alguns ajustes simples.

```python
{% include "../tutorial/tuto5.py"%}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Texto dos países](https://github.com/py-pdf/fpdf2/raw/master/tutorial/countries.txt)

O primeiro exemplo é feito da forma mais básica possível, passando os dados para [`FPDF.table()`](https://py-pdf.github.io/fpdf2/Tables.html). O resultado é rudimentar, mas muito rápido de obter.

A segunda tabela traz algumas melhorias: cores, largura da tabela limitada, altura de linha reduzida,
títulos centralizados, colunas com larguras personalizadas, números alinhados à direita...
Além disso, as linhas horizontais foram removidas.
Isso foi feito escolhendo um `borders_layout` entre os valores disponíveis:
[`TableBordersLayout`](https://py-pdf.github.io/fpdf2/fpdf/enums.html#fpdf.enums.TableBordersLayout).

## Tuto 6 - Criar links e misturar estilos de texto ##

Este tutorial irá explicar várias maneiras de inserir links dentro de um documento PDF, bem como adicionar links para fontes externas.

Também mostrará várias maneiras de usar diferentes estilos de texto (negrito, itálico, sublinhado) no mesmo texto.

```python
{% include "../tutorial/tuto6.py"%}
```

[PDF resultante](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://py-pdf.github.io/fpdf2/fpdf2-logo.png)



O novo método mostrado aqui para imprimir texto é [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write). É muito parecido com [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell), sendo as principais diferenças:

- O fim da linha está na margem direita e a próxima linha começa na 
  margem esquerda.
- A posição atual move-se para o final do texto.

O método, portanto, nos permite escrever um pedaço de texto, alterar o estilo da fonte, e continuar do ponto exato em que paramos.
Por outro lado, a sua principal desvantagem é que não podemos justificar o texto como nós fazemos com o método [multi_cell()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell).

Na primeira página do exemplo, usámos [write()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write)
para este propósito. O início da frase está escrito no estilo de texto normal, depois, usando o método [set_font()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), trocamos para sublinhado e acabámos a frase.

Para adicionar o link interno a apontar para a segunda página, nós usámos o método [add_link()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link), que cria uma área clicável à qual demos o nome de “link” que direciona para outra parte do documento.

Para criar o link externo usando uma imagem, usámos [image()](https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image). O método tem a opção de passar um link como um dos seus argumentos. O link pode ser interno ou externo.

Como alternativa, outra opção para mudar o estilo da fonte e adicionar links é usar o método `write_html()`. É um “parser” que permite adicionar texto, mudar o estilo da fonte e adicionar links usando html.

## Tuto 7 - Criar documentos PDF/A ##

_Novo na versão [:octicons-tag-24: 2.8.3](https://github.com/py-pdf/fpdf2/blob/master/CHANGELOG.md)_

### Padrões PDF/A ###

<b>PDF/A-1</b> usa a versão 1.4 do PDF. Todos os recursos (imagens, gráficos, fontes) precisam estar incorporados ao documento. O gerenciamento de cores precisa ser preciso e especificado de forma independente da plataforma, com perfis ICC, e os metadados do documento precisam ser fornecidos como metadados XMP.

<b>PDF/A-2</b> usa a versão 1.7 do PDF. Permite compressão com JPEG2000, elementos transparentes, fontes OpenType e assinaturas digitais.

A única novidade do <b>PDF/A-3</b> é a possibilidade de incorporar qualquer tipo de arquivo.

### Níveis de conformidade ###

O nível A (acessível) abrange todos os requisitos do padrão, incluindo o mapeamento da estrutura do conteúdo e a ordem de leitura correta do documento. O texto precisa poder ser extraído, e a estrutura precisa refletir a sequência natural de leitura.

O nível B (básico) garante uma reprodução visual fiel do conteúdo. Costuma ser mais fácil de gerar do que o nível A, mas não garante que todo o texto possa ser extraído ou pesquisado, e a reutilização do conteúdo nem sempre é simples.

Para isso, aqui está um pequeno exemplo:

```python
{% include "../tutorial/tuto7.py" %}
```

[PDF resultante: tuto7.pdf](https://github.com/py-pdf/fpdf2/raw/master/tutorial/tuto7.pdf)

Ferramentas como o [VeraPDF](https://verapdf.org/) verificam se os documentos PDF produzidos estão em conformidade:

    verapdf --format text -v tutorial/tuto7.pdf

Resultado:

    PASS fpdf2/tutorial/tuto7.pdf 3b
