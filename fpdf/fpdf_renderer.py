"""
Based on https://github.com/matplotlib/matplotlib/blob/v3.7.1/lib/matplotlib/backends/backend_template.py

Just need to tell MatPlotLib to use this renderer and then do fig.savefig.
"""

from contextlib import nullcontext
import logging
from matplotlib.backend_bases import (
    FigureCanvasBase,
    FigureManagerBase,
    GraphicsContextBase,
    RendererBase,
)
from matplotlib.transforms import Affine2D
import matplotlib as mpl

from fpdf.drawing import PaintedPath
from fpdf.enums import PathPaintRule

PT_TO_MM = 0.3527777778  # 1 point = 0.3527777778 mm


LOGGER = logging.getLogger(__name__)


class RendererTemplate(RendererBase):
    """Removed draw_markers, draw_path_collection and draw_quad_mesh - all optional, we can add later"""

    def __init__(self, figure, dpi, fpdf, scale, transform, fig_width, fig_height):
        del fig_height  # unused for now
        super().__init__()
        self.figure = figure
        # print (f'FPDF: dpi: {dpi}')
        self.dpi = dpi

        self._fpdf = fpdf
        self._trans = transform
        self._scale = scale

        # calc font scaling factor to get matplotlib font sizes to match FPDF sizes if width is scaled
        fig_w_mm = fig_width * scale
        fig_w_inch = fig_width / dpi

        shrink_ratio_w = (fig_w_mm / 25.4) / fig_w_inch
        if fpdf:
            self._font_scaling = shrink_ratio_w
            # print(f"Font scaling factor: {self._font_scaling}")

    def draw_gouraud_triangles(self, gc, triangles_array, colors_array, transform):
        raise NotImplementedError("draw_gouraud_triangles not implemented yet")

    def draw_path(self, gc, path, transform, rgbFace=None):

        if len(path) == 0:
            logging.debug("draw_path: empty path - skipping")
            return

        tran = transform + self._trans
        clip_rect = None
        clip_x0, clip_y0, clip_x1, clip_y1 = None, None, None, None
        if gc.get_clip_rectangle():
            clip_rect = gc.get_clip_rectangle().extents
            clip_x0, clip_y0 = self._trans.transform(clip_rect[0:2])
            clip_x1, clip_y1 = self._trans.transform(clip_rect[2:4])

        # else:
        # print(f"clip-path: {gc.get_clip_path()}\n")
        c, v = zip(*[(c, v.tolist()) for v, c in path.iter_segments(transform=tran)])

        p = self._fpdf
        fill_opacity = None
        stroke_opacity = None
        if rgbFace is not None and len(rgbFace) >= 3:
            p.set_fill_color(rgbFace[0] * 255, rgbFace[1] * 255, rgbFace[2] * 255)

            if len(rgbFace) == 4:
                # print(f"fill_opacity: { rgbFace[3]}")
                fill_opacity = rgbFace[3]

        rgb = gc.get_rgb()
        p.set_draw_color(rgb[0] * 255, rgb[1] * 255, rgb[2] * 255)
        stroke_opacity = None
        if len(rgb) == 4:
            # print(f"stroke_opacity: { rgb[3]}")
            stroke_opacity = rgb[3]

        _, dash_array = gc.get_dashes()

        line_width = gc.get_linewidth()
        line_width_px = line_width * self.dpi / 72.0  # points to pixels
        mm_line_width = line_width_px * self._scale
        with (
            p.rect_clip(clip_x0, clip_y0, clip_x1 - clip_x0, clip_y1 - clip_y0)
            if clip_rect is not None
            else nullcontext()
        ):

            with p.local_context(
                stroke_opacity=stroke_opacity,
                fill_opacity=fill_opacity,
                line_width=mm_line_width,
            ):
                # p.set_draw_color(rgb[0]*255, rgb[1]*255, rgb[2]*255)
                # print(f"draw_path: color rgb: {rgb}, line_width: {line_width} pt -> mm_line_width: {mm_line_width:.2f} mm")
                # print(f"line_width: {line_width} pt -> mm_line_width: {mm_line_width:.2f} mm")
                if dash_array and len(dash_array) >= 2:
                    # Scale dash array from points to mm
                    mm_dash_array = [(d * PT_TO_MM) for d in dash_array]

                    if len(mm_dash_array) > 2:
                        # make sure we have even number of elements
                        LOGGER.warning(
                            "Warning: dash array has more than two elements - ignoring extra ones"
                        )
                    dash = mm_dash_array[0] - mm_line_width
                    gap = mm_dash_array[1] + mm_line_width
                    p.set_dash_pattern(dash=dash, gap=gap)
                # print(f'Path commands: {c}: {v}')

                match c:
                    # Simple line
                    case [path.MOVETO, path.LINETO]:
                        # print(f"simpleline: {v}")
                        p.polyline(v)

                    # Polyline - move then a set of lines
                    case [path.MOVETO, *mid, path.LINETO] if all(
                        e == path.LINETO for e in mid
                    ):
                        # print(f"polyline2: {v}")
                        p.polyline(v)

                    # Path combinations: Starts with MOVETO, and can end with CLOSEPOLY
                    case [path.MOVETO, *_]:
                        # print(f"polygon: \n{c}\n{v}\n")

                        pth = None
                        length = len(c)
                        with p.drawing_context() as ctxt:
                            for i, vtx in enumerate(v):
                                # print(f"  cmd: {c[i]}, vtx: {vtx}")
                                if pth is None:
                                    pth = PaintedPath()
                                    pth.style.auto_close = False
                                if c[i] == path.MOVETO:
                                    pth.move_to(*vtx)
                                elif c[i] == path.LINETO:
                                    pth.line_to(*vtx)
                                elif c[i] == path.CURVE3:
                                    pth.quadratic_curve_to(*vtx)
                                elif c[i] == path.CURVE4:
                                    pth.curve_to(*vtx)
                                elif c[i] == path.CLOSEPOLY:
                                    # print(f"Closing polygon path. idx: {i}")

                                    if i == length - 1:
                                        pth.close()  # close the path and add to context without copying
                                        ctxt.add_item(pth, _copy=False)
                                        pth = None
                                    else:
                                        pth.paint_rule = PathPaintRule.FILL_EVENODD
                                        pth.move_to(*v[i])  # start a new sub-path

                                else:
                                    LOGGER.warning(
                                        "Unhandled path command in polygon: %d at vertex %s",
                                        c[i],
                                        vtx,
                                    )
                            if pth is not None:
                                # print(f"path was not closed - adding to context")
                                # add to context without copying
                                ctxt.add_item(pth, _copy=False)
                                pth = None

                    case _:
                        LOGGER.warning("draw_path: Unmatched %d", c)

    def draw_image(self, gc, x, y, im, transform=None):
        LOGGER.warning("draw_image at %d,%d size %s", x, y, im.get_size())
        raise NotImplementedError("draw_image not implemented yet")

    def draw_text(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):

        # print (f'RendererTemplate.draw_text - {s} at {x:.0f},{y:.0f} at angle {angle:.1f} with prop {prop} - {mtext}')
        # print (f'RendererTemplate.draw_text - {s} at {x:.0f},{y:.0f} - {mtext}')
        th = (
            self._fpdf.font_size_pt * PT_TO_MM * self._font_scaling
        )  # Default text height in mm

        if isinstance(prop, str):
            raise ValueError(
                f"draw_text.prop is a string ({prop}) - add code to add font"
            )

        # We're expecting a FontProperties instance
        if isinstance(prop, mpl.font_manager.FontProperties):
            # print(f"font prop size: {prop.get_size()} name: {prop.get_name()}, self._font_scaling: {self._font_scaling}")
            self._fpdf.set_font(
                prop.get_name(), size=prop.get_size() * self._font_scaling
            )

            tw, th, _ = self.get_text_width_height_descent(s, prop, ismath)
            tw *= self._font_scaling * PT_TO_MM / self.dpi * 72.0
            th *= self._font_scaling * PT_TO_MM / self.dpi * 72.0
            # tw_prerotate = tw
            # th_prerotate = th

            # print(f'Text width/height before rotation: {tw_prerotate:.1f}/{th_prerotate:.1f} mm')
            # print(f'scale x: {self.figure.bbox.width}, y: {self.figure.bbox.height}')
            # Calc text width and height
            rotated_bbox = (
                Affine2D()
                .rotate_deg(angle)
                .transform(((0, 0), (tw, 0), (tw, th), (0, th)))
            )

            min_x = min(rotated_bbox[:, 0])
            max_x = max(rotated_bbox[:, 0])
            min_y = min(rotated_bbox[:, 1])
            max_y = max(rotated_bbox[:, 1])
            tw = max_x - min_x
            th = max_y - min_y
        else:
            LOGGER.warning("Unknown prop type: %s", type(prop))
            tw = None
            th = None

        # Transform our data point
        # print(f"Before transform: x={x}, y={y}. s:'{s}'")

        trans = self._trans  # + Affine2D().translate(-tw/3.5, 0)
        x, y = trans.transform((x, y))

        # print(f'- [{x:.1f},{y:.1f}] {s}')
        # print(f'Text \'{s}\' ha: {ha}, angle: {angle}')
        color = gc.get_rgb()
        self._fpdf.set_text_color(
            int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
        )
        # print("Color:", color)
        # Get text width to sort positioning - MPL centers on co-ordinate
        # print (f'Text width rotated: {tw:.1f}, height: {th:.1f}')
        match angle:
            case 0:
                self._fpdf.text(x, y, s)

            case _:
                # print (f'Rotate to "{angle}" {type(angle)}')
                rotpt_x = 0
                rotpt_y = 0
                with self._fpdf.rotation(angle=angle, x=x - rotpt_x, y=y + rotpt_y):
                    self._fpdf.text(x, y, s)

    def flipy(self):
        return False

    def get_canvas_width_height(self):
        return 100, 100

    def new_gc(self):
        return GraphicsContextTemplate()

    def points_to_pixels(self, points):
        return points / 72.0 * self.dpi
        # return points


class GraphicsContextTemplate(GraphicsContextBase):
    """
    The graphics context provides the color, line styles, etc.  See the cairo
    and postscript backends for examples of mapping the graphics context
    attributes (cap styles, join styles, line widths, colors) to a particular
    backend.  In cairo this is done by wrapping a cairo.Context object and
    forwarding the appropriate calls to it using a dictionary mapping styles
    to gdk constants.  In Postscript, all the work is done by the renderer,
    mapping line styles to postscript calls.

    If it's more appropriate to do the mapping at the renderer level (as in
    the postscript backend), you don't need to override any of the GC methods.
    If it's more appropriate to wrap an instance (as in the cairo backend) and
    do the mapping here, you'll need to override several of the setter
    methods.

    The base GraphicsContext stores colors as an RGB tuple on the unit
    interval, e.g., (0.5, 0.0, 1.0). You may need to map this to colors
    appropriate for your backend.
    """


########################################################################
#
# The following functions and classes are for pyplot and implement
# window/figure managers, etc.
#
########################################################################


class FigureManagerTemplate(FigureManagerBase):
    """
    Helper class for pyplot mode, wraps everything up into a neat bundle.

    For non-interactive backends, the base class is sufficient.  For
    interactive backends, see the documentation of the `.FigureManagerBase`
    class for the list of methods that can/should be overridden.
    """


class FigureCanvasTemplate(FigureCanvasBase):
    """
    The canvas the figure renders into.  Calls the draw and print fig
    methods, creates the renderers, etc.

    Note: GUI templates will want to connect events for button presses,
    mouse movements and key presses to functions that call the base
    class methods button_press_event, button_release_event,
    motion_notify_event, key_press_event, and key_release_event.  See the
    implementations of the interactive backends for examples.

    Attributes
    ----------
    figure : `matplotlib.figure.Figure`
        A high-level Figure instance
    """

    # The instantiated manager class.  For further customization,
    # ``FigureManager.create_with_canvas`` can also be overridden; see the
    # wx-based backends for an example.
    manager_class = FigureManagerTemplate

    def draw(self, *args, **kwargs):
        """
        Draw the figure using the renderer.

        It is important that this method actually walk the artist tree
        even if not output is produced because this will trigger
        deferred work (like computing limits auto-limits and tick
        values) that users may want access to before saving to disk.
        """
        if args or kwargs:
            LOGGER.warning(
                "draw() got arguments that will not be used for now: %s, %s",
                args,
                kwargs,
            )

        # print (f'Draw: {self._fpdf}')
        width = self.figure.bbox.width
        height = self.figure.bbox.height
        renderer = RendererTemplate(
            self.figure,
            self.figure.dpi,
            self._fpdf,
            self._scale,
            self._trans,
            width,
            height,
        )
        self.figure.draw(renderer)

        # You should provide a print_xxx function for every file format
        # you can write.

    # If the file type is not in the base set of filetypes,
    # you should add it to the class-scope filetypes dictionary as follows:
    filetypes = {**FigureCanvasBase.filetypes, "fpdf": "My magic FPDF format"}

    def print_fpdf(self, filename, **kwargs):
        del filename  # filename is not used for now

        self._fpdf = self._trans = origin = scale = None
        self._scale = 1.0
        self._facecolor = self._edgecolor = None
        # if not isinstance(self.figure, Figure):
        # 	if self.figure is None: manager = Gcf.get_active()
        # 	else: manager = Gcf.get_fig_manager(figure)
        # 	if manager is None: raise ValueError(f"No figure {self.figure}")
        # 	figure = manager.canvas.figure

        # Fpdf uses top left origin, matplotlib bottom left so... fix Y axis
        # We pass scale, origin and a handle to the fpdpf instance through here
        for k, v in kwargs.items():
            match (k):
                case "fpdf":
                    self._fpdf = v
                case "origin":
                    origin = v
                    # print(f"print_fpdf: origin={origin}")
                case "scale":
                    scale = v
                    # print(f"print_fpdf: scale={scale}")
                    self._scale = scale
                case "facecolor":
                    if not v:
                        self._facecolor = (1, 0, 1)
                case "edgecolor":
                    if not v:
                        self._edgecolor = (0, 1, 1)
                case "orientation":
                    pass  # ignore for now
                case "bbox_inches_restore":
                    pass  # ignore for now
                case _:
                    LOGGER.warning("Unrecognised keyword %s -> %s", k, v)

        # fig_width = self.figure.bbox.width
        # fig_height = self.figure.bbox.height

        # Build our transformation do scale and offset for whole figure
        if origin and scale:
            # fig_height_mm = fig_height * scale
            # print(f"print_fpdf: fig_width={fig_width}, fig_height={fig_height}, fig_height_mm={fig_height_mm}")
            self._trans = Affine2D().scale(self._scale).scale(1, -1).translate(*origin)

        self.draw()

    @classmethod
    def get_default_filetype(cls):
        return "fpdf"


########################################################################
#
# Now just provide the standard names that backend.__init__ is expecting
#
########################################################################

FigureCanvas = FigureCanvasTemplate
FigureManager = FigureManagerTemplate
