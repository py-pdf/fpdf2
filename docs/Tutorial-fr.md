# Tutorial #

Versión en español: [Tutorial-es](Tutorial-es.md)

हिंदी संस्करण: [Tutorial-हिंदी](Tutorial-हिंदी.md)

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
pdf.cell(60, 10, 'Powered by FPDF.', ln=1, align='C')
```

**Remarque** : le saut de ligne peut aussi être fait avec [ln](fpdf/fpdf.html#fpdf.fpdf.FPDF.ln). Cette méthode permet de spécifier la hauteur du saut.

Enfin, le document est sauvegardé à l'endroit spécifié en utilisant [output](fpdf/fpdf.html#fpdf.fpdf.FPDF.output). Sans aucun paramètre, `output()` retourne le buffer `bytearray` du PDF.

## Tuto 2 - En-tête, bas de page, saut de page et image ##

Voici un exemple contenant deux pages avec un en-tête, un bas de page et un logo :

```python
{% include "../tutorial/tuto2.py" %}
```

[PDF généré](https://github.com/PyFPDF/fpdf2/raw/master/tutorial/tuto2.pdf)
En cours de traduction.

## Tuto 3 - Sauts de ligne et couleurs ##
En cours de traduction.

## Tuto 4 - Colonnes multiples ##
En cours de traduction.

## Tuto 5 - Créer des tables ##
En cours de traduction.

## Tuto 6 - Créer des liens et mélanger différents styles de textes ##
En cours de traduction.