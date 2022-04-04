# Tutorial #

Documentation complète des méthodes : [`fpdf.FPDF` API doc](https://pyfpdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF)

[TOC]

## Tuto 1 - Exemple minimal ##

Commençons par un exemple classique :

```python
{% include "../tutorial/tuto1.py" %}
```

[PDF généré](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto1.pdf)

Après avoir inclu la librairie, on créé un objet `FPDF`. Le constructeur [FPDF](fpdf/fpdf.html#fpdf.fpdf.FPDF) est utilisé avec ses valeurs par défaut : 
les pages sont en format portrait A4 et l'unité de mesure est le millimètre.
Cela peut également être spéficié de cette manière :

```python
pdf = FPDF(orientation="P", unit="mm", format="A4")
```

Il est possible de créer un PDF en format paysage (`L`) ou encore d'utiliser d'autres formats (par exemple `Letter` et `Legal`) et unités de mesure (`pt`, `cm`, `in`).

Il n'y a pas encore de page, il faut donc en créer une avec [add_page](fpdf/fpdf.html#fpdf.fpdf.FPDF.add_page). Le coin en haut à gauche correspond à l'origine, et le curseur (c'est-à-dire la position actuelle où l'on va afficher un élément) est placé par défaut à 1 cm des bords; les marges peuvent être modifiées avec [set_margins](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_margins).

Avant de pouvoir afficher du texte, il faut obligatoirement choisir une police de caractères avec [set_font](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_font).
Choisissons Helvetica bold 16:

```python
pdf.set_font('helvetica', 'B', 16)
```

On aurait pu spécifier une police en italique avec `I`; soulignée avec `U` ou une police normale avec une chaine de caractères vide. Il est aussi possible de combiner les effets en combinant les caractères. Notez que la taille des caractères est à spécifier en points (pts), pas en millimètres (ou tout autre unité); c'est la seule exception.
Les autres polices fournies par défaut sont `Times`, `Courier`, `Symbol` et `ZapfDingbats`.

On peut maintenant afficher une cellule avec [cell](fpdf/fpdf.html#fpdf.fpdf.FPDF.cell). Une cellule est une zone rectangulaire, avec ou sans cadre, qui contient du texte. Elle est affichée à la position actuelle du curseur. On spécifie ses dimensions, le texte (centré ou aligné), si'l y a une bordure ou non, ainsi que la position du curseur après avoir affiché la cellule (s'il se déplace à droite, vers le bas ou au début de la ligne suivante). Pour ajouter un cadre, on utilise ceci :

```python
pdf.cell(40, 10, 'Hello World!', 1)
```

Pour ajouter une nouvelle cellule avec un texte centré, et déplacer le curseur à la ligne suivante on utilise cela :

```python
pdf.cell(60, 10, 'Powered by FPDF.', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
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

Pour centrer le numéro de page dans le bas de page, il faut passer la valeur nulle à la place de la largeur de la cellule. Cela fait prendre toute la largeur de la page à la cellule, ce qui permet de centrer le texte. Le numéro de page actuel est obtenu avec la méthode [page_no](fpdf/fpdf.html#fpdf.fpdf.FPDF.page_no); le nombre total de pages est obtenu avec la variable `{nb}` qui prend sa valeur quand le document est fermé (la méthode [alias_nb_pages](fpdf/fpdf.html#fpdf.fpdf.FPDF.alias_nb_pages) permet de définir un autre nom de variable pour cette valeur).
La méthode [set_y](fpdf/fpdf.html#fpdf.fpdf.FPDF.set_y) permet de spécifier une position dans la page relative au haut ou pas de page.

Une autre fonctionnalité intéressante est utilisée ici : les sauts de page automatiques. Si une cellule dépasse la limite du contenu de la page (par défaut à 2 centimètres du bas), un saut de page est inséré à la place et la police de caractères est restaurée. C'est-à-dire, bien que l'en-tête et le bas de page utilisent la police (`helvetica`), le corps du texte garde la police `Times`.
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
En cours de traduction.

## Tuto 5 - Créer des tables ##
En cours de traduction.

## Tuto 6 - Créer des liens et mélanger différents styles de textes ##
En cours de traduction.
