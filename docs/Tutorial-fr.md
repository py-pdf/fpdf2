# Tutorial #

Documentation complète des méthodes : [`fpdf.FPDF` API doc](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Tuto 1 - Exemple minimal ##

Commençons par un exemple classique :

```python
{% include "../tutorial/tuto1.py" %}
```

[PDF généré](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

Après avoir inclus la librairie, on crée un objet `FPDF`. Le constructeur [FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) est utilisé avec ses valeurs par défaut : 
les pages sont en format portrait A4 et l'unité de mesure est le millimètre.
Cela peut également être spéficié de cette manière :

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

Il est possible de créer un PDF en format paysage (`L`) ou encore d'utiliser d'autres formats (par exemple `Letter` et `Legal`) et unités de mesure (`pt`, `cm`, `in`).

Il n'y a pas encore de page, il faut donc en créer une avec [add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). Le coin en haut à gauche correspond à l'origine, et le curseur (c'est-à-dire la position actuelle où l'on va afficher un élément) est placé par défaut à 1 cm des bords. Les marges peuvent être modifiées avec [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins).

Avant de pouvoir afficher du texte, il faut obligatoirement choisir une police de caractères avec [set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font).
Choisissons Helvetica bold 16 :

```python
pdf.set_font('helvetica', 'B', 16)
```

On aurait pu spécifier une police en italique avec `I`, soulignée avec `U` ou une police normale avec une chaine de caractères vide. Il est aussi possible de combiner les effets en combinant les caractères. Notez que la taille des caractères est à spécifier en points (pts), pas en millimètres (ou tout autre unité). C'est la seule exception.
Les autres polices fournies par défaut sont `Times`, `Courier`, `Symbol` et `ZapfDingbats`.

On peut maintenant afficher une cellule avec [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). Une cellule est une zone rectangulaire, avec ou sans cadre, qui contient du texte. Elle est affichée à la position actuelle du curseur. On spécifie ses dimensions, le texte (centré ou aligné), s'il y a une bordure ou non, ainsi que la position du curseur après avoir affiché la cellule (s'il se déplace à droite, vers le bas ou au début de la ligne suivante). Pour ajouter un cadre, on utilise ceci :

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

Pour ajouter une nouvelle cellule avec un texte centré et déplacer le curseur à la ligne suivante, on utilise cela :

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x="LMARGIN", new_y="NEXT", align='C')
```

**Remarque** : le saut de ligne peut aussi être fait avec [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). Cette méthode permet de spécifier la hauteur du saut.

Enfin, le document est sauvegardé à l'endroit spécifié en utilisant [output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Sans aucun paramètre, `output()` retourne le buffer `bytearray` du PDF.

## Tuto 2 - En-tête, bas de page, saut de page et image ##

Voici un exemple contenant deux pages avec un en-tête, un bas de page et un logo :

```python
{% include "../tutorial/tuto2.py" %}
```

[PDF généré](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)

Cet exemple utilise les méthodes [header](fpdf/fpdf.html#fpdf.fpdf.FPDF.header) et [footer](fpdf/fpdf.html#fpdf.fpdf.FPDF.footer) pour générer des en-têtes et des bas de page. Elles sont appelées automatiquement. Elles existent déjà dans la classe FPDF mais elles ne font rien, il faut donc les redéfinir dans une classe fille.

Le logo est affiché avec la méthode [image](fpdf/fpdf.html#fpdf.fpdf.FPDF.image) en spécifiant la position du coin supérieur gauche et la largeur de l'image. La hauteur est calculée automatiquement pour garder les proportions de l'image.

Pour centrer le numéro de page dans le bas de page, il faut passer la valeur nulle à la place de la largeur de la cellule. Cela fait prendre toute la largeur de la page à la cellule, ce qui permet de centrer le texte. Le numéro de page actuel est obtenu avec la méthode [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no). Le nombre total de pages est obtenu avec la variable `{nb}` qui prend sa valeur quand le document est fermé (la méthode [alias_nb_pages](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages) permet de définir un autre nom de variable pour cette valeur).
La méthode [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) permet de spécifier une position dans la page relative au haut ou bas de page.

Une autre fonctionnalité intéressante est utilisée ici : les sauts de page automatiques. Si une cellule dépasse la limite du contenu de la page (par défaut à 2 centimètres du bas), un saut de page est inséré à la place et la police de caractères est restaurée. C'est-à-dire, bien que l'en-tête et le bas de page utilisent la police `helvetica`, le corps du texte garde la police `Times`.
Ce mécanisme de restauration automatique s'applique également à la couleur et l'épaisseur des lignes.
La limite du contenu qui déclenche le saut de page peut être spécifiée avec [set_auto_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_auto_page_break).


## Tuto 3 - Saut de ligne et couleur ##
Continuons avec un exemple qui affiche des paragraphes avec du texte justifié. Cet exemple montre également l'utilisation de couleurs.

```python
{% include "../tutorial/tuto3.py" %}
```

[PDF généré](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto3.pdf)

[Texte de Jules Verne](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

La méthode [get_string_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.get_string_width) permet de déterminer la largeur d'un texte utilisant la police actuelle, ce qui permet de calculer la position et la largeur du cadre autour du titre. Ensuite les couleurs sont spécifiées (avec [set_draw_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_draw_color), [set_fill_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_fill_color) et [set_text_color](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_text_color)) et on spécifie l'épaisseur de la bordure du cadre à 1 mm (contre 0.2 par défaut) avec [set_line_width](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_line_width). Enfin, on affiche la cellule (le dernier paramètre "true" indique que le fond doit être rempli).

La méthode [multi_cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell) est utilisée pour afficher les paragraphes.
Chaque fois qu'une ligne atteint le bord d'une cellule ou qu'un caractère de retour à la ligne est présent, un saut de ligne est inséré et une nouvelle cellule est créée automatiquement sous la cellule actuelle. Le texte est justifié par défaut.

Deux propriétés sont définies pour le document : le titre ([set_title](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_title)) et l'auteur ([set_author](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_author)). Les propriétés peuvent être trouvées en ouvrant le document PDF avec Acrobat Reader. Elles sont alors visibles dans le menu Fichier -> Propriétés du document.

## Tuto 4 - Colonnes multiples ##
Cet exemple est une variante du précédent qui montre comment répartir le texte sur plusieurs colonnes.

```python
{% include "../tutorial/tuto4.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto4.pdf)

[Jules Verne text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/20k_c1.txt)

La principale différence avec le tutoriel précédent est l'utilisation des méthodes [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) et `set_col()`.

En utilisant la méthode [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break), une fois que la cellule franchit la limite inférieure de la page, elle vérifie le numéro de la colonne actuelle. Si celui-ci est inférieur à 2 (nous avons choisi de diviser la page en trois colonnes), il appelle la méthode `set_col()`, en augmentant le numéro de la colonne et en modifiant la position de la colonne suivante pour que le texte puisse s'y poursuivre.

Une fois que la limite inférieure de la troisième colonne est atteinte, la méthode [accept_page_break](fpdf/fpdf.html#fpdf.fpdf.FPDF.accept_page_break) sera réinitialisée et retournera à la première colonne. Cela déclenchera un saut de page.

## Tuto 5 - Créer des tables ##
Ce tutoriel explique comment créer facilement des tableaux.

Le code créera trois tableaux différents pour expliquer ce qui peut être réalisé avec quelques modifications.

```python
{% include "../tutorial/tuto5.py" %}
```

[Resulting PDF](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto5.pdf) -
[Countries text](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/countries.txt)

Comme un tableau n'est qu'une collection de cellules, il est naturel d'en construire un à partir de celles-ci.

Le premier exemple est réalisé de la manière la plus basique qui soit : de simples cellules encadrées, toutes de même taille et alignées à gauche. Le résultat est rudimentaire mais très rapide à obtenir.

Le deuxième tableau apporte quelques améliorations : chaque colonne possède sa propre largeur, les titres sont centrés et les chiffres alignés à droite. De plus, les lignes horizontales ont été supprimées. C'est fait grâce au paramètre `border` de la méthode [`.cell()`](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell) qui spécifie quels côtés de la cellule doivent être dessinés. Ici, nous voulons les côtés gauche (`L`) et droit (`R`). Il ne reste plus que le problème de la ligne horizontale pour terminer le tableau. Il y a deux possibilités pour le résoudre : vérifier la dernière ligne dans la boucle (dans ce cas nous utilisons `LRB` pour le paramètre de bordure) ou, comme fait ici, ajouter la ligne une fois la boucle terminée.

Le troisième tableau est similaire au deuxième mais utilise des couleurs. Les couleurs de remplissage, de texte et de ligne sont simplement spécifiées. Une coloration alternative pour les lignes est obtenue en utilisant des cellules alternativement transparentes et remplies.

## Tuto 6 - Créer des liens et mélanger différents styles de textes ##
Ce tutoriel explique plusieurs façons d'insérer des liens à l'intérieur d'un document pdf, ainsi que l'ajout de liens vers des sources externes.

Il montrera également plusieurs façons d'utiliser différents styles de texte (gras, italique, souligné) dans un même texte.

```python
{% include "../tutorial/tuto6.py" %}
```

[PDF créé dans ce tutoriel](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto6.pdf) -
[fpdf2-logo](https://raw.githubusercontent.com/PyFPDF/fpdf2/master/docs/fpdf2-logo.png)

La nouvelle méthode présentée ici pour imprimer du texte est [write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write). Elle est très similaire à [multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell). Les principales différences sont les suivantes :

- La fin de la ligne se trouve dans la marge de droite et la ligne suivante commence dans la marge de gauche.
- La position actuelle se déplace à la fin du texte.

Cette méthode nous permet donc d'écrire un morceau de texte, de modifier le style de police et de reprendre exactement là où nous nous sommes arrêtés.
En revanche, son principal inconvénient est que nous ne pouvons pas justifier le texte comme nous le faisons avec la méthode [multi_cell()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.multi_cell).

Dans la première page de l'exemple, nous avons utilisé [write()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.write) à cette fin. Le début de la phrase est écrit en style normal, puis en utilisant la méthode [set_font()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font), nous sommes passés au soulignement et avons terminé la phrase.

Pour ajouter un lien interne pointant vers la deuxième page, nous avons utilisé la méthode [add_link()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.add_link), qui crée une zone cliquable que nous avons nommée `link` et qui dirige vers un autre endroit du document. Sur la deuxième page, nous avons utilisé [set_link()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.set_link) pour définir la zone de destination du lien que nous venons de créer.

Pour créer le lien externe à l'aide d'une image, nous avons utilisé [image()](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image). Cette méthode a la possibilité de transmettre un lien comme l'un de ses arguments. Le lien peut être interne ou externe.

Comme alternative, une autre option pour changer le style de police et ajouter des liens est d'utiliser la méthode `write_html()`. Il s'agit d'un analyseur html qui permet d'ajouter du texte, de changer le style de police et d'ajouter des liens en utilisant le html.
