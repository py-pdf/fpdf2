# Text Flow Regions #

**Notice:** As of fpdf2 release 2.5.8, this is an experimental feature. Both the API and the functionality may change before it is finalized, without prior notice.

Text regions are a hierarchy of classes that enable to flow text within a given outline. In the simplest case, it is just the running text column of a page. But it can also be a sequence of outlines, such as several parallel columns or the cells of a table. Other outlines may be combined by addition or subtraction to create more complex shapes.

There are two general categories of regions. One defines boundaries for running text that will just continue in the same manner one the next page. Those include columns and tables. The second category are distinct shapes. Examples would be a circle, a rectangle, a polygon of individual shape or even an image. They may be used individually, in combination, or to modify the outline of a multipage column. Shape regions will typically not cause a page break when they are full. In the future, a possibility to chain them may be implemented, so that a new shape will continue with the text that didn't fit into the previous one.

## General Operation ##

Using the different region types and combination always follows the same pattern. The main difference to the normal `FPDF.write()` method is that all added text will first be buffered, and you need to explicitly trigger its rendering on the page. This is necessary so that text can be aligned within the given boundaries even if its font, style, or size are arbitrarily varied along the way.

* Create the region instance
* If desired, add or subtract other shapes from it
* Use the `.write()` method to feed text into its buffer
* You can use the region instance as a context manager for filling, but you don't have to
  * When used as a context manager, you can change all text styling parameters within that context, and they will be used by the added text, but won't leak to the surroundings
  * For adding text with the already existing settings, just use the region instance as is.
* Once all the desired text is collected to fill a shape or a set of columns, you can call its `.render()` method to actually do so. 


### Text Start Position ###

When rendering, the vertical start position of the text will be either at the lowest point out of the current y position, the top of the region (if it has a defined top), or the top margin of the page. The horizontal start position will either at the current x position or at the left edge of the region, whichever is further to the right. In both horizontal and vertical positioning, regions with multiple columns may follow additional rules and restrictions.


### Interaction between Regions ###

Several region instances can exist at the same time. But only one of them can act as context manager at any given time. It is not currently possible to operate them recursively.
But it is possible to use them intermittingly. This will probably most often make sense between a columnar region and a table. You may have some running text ending at a given height, then insert a table with data, and finally continue the running text at the new height below the table within the existing column.


