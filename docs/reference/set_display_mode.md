## set_display_mode ##

```python
fpdf.set_display_mode(zoom, layout: str)
```
### Description ###

Defines the way the document is to be displayed by the viewer. The zoom level can be set: pages can be displayed entirely on screen, occupy the full width of the window, use the real size, be scaled by a specific zooming factor or use the viewer default (configured in the Preferences menu of Adobe Reader). The page layout can be specified too: single page at a time, continuous display, two columns or viewer default.

If this method is not called, the zoom mode is set to _fullwidth_ and the layout is set to _continuous_ by default.

### Parameters ###

zoom:
> The zoom to use. It can be one of the following string values:
>>  * `fullpage`: displays the entire page on the screen
>>  * `fullwidth`: uses the maximum width of the window
>>  * `real`: uses the real size (equivalent to 100% zoom)
>>  * `default`: uses the viewer default mode
> 
> or a number indicating the zooming factor to use, as a percentage.

layout:
> The page layout. Possible values are:
>>  * `single`: displays one page at a time
>>  * `continuous`: displays pages continuously
>>  * `two`: displays two pages in two columns
>>  * `default`: uses the viewer default mode
> 
> The default value is `continuous`.



