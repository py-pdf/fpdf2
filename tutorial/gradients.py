from FPDF.Gradients import *

pdf = Gradients()

# first page
pdf.AddPage()
pdf.SetFont("Arial", "", 14)
pdf.Cell(0, 5, "Page 1", 0, 1, "C")
pdf.Ln()

# set colors for gradients (r,g,b) or (grey 0-255)
red = [255, 0, 0]
blue = [0, 0, 200]
yellow = [255, 255, 0]
green = [0, 255, 0]
white = [255]
black = [0]

# set the coordinates x1,y1,x2,y2 of the gradient (see linear_gradient_coords.jpg)
coords = [0.0, 0.0, 1.0, 0.0]

# paint a linear gradient
pdf.LinearGradient(20, 25, 80, 80, red, blue, coords)

# set the coordinates fx,fy,cx,cy,r of the gradient (see radial_gradient_coords.jpg)
coords = [0.5, 0.5, 1.0, 1.0, 1.2]

# paint a radial gradient
pdf.RadialGradient(110, 25, 80, 80, white, black, coords)

# paint a coons patch mesh with default coordinates
pdf.CoonsPatchMesh(20, 115, 80, 80, yellow, blue, green, red)

# set the coordinates for the cubic Bezier points x1,y1 ... x12, y12 of the patch (see coons_patch_mesh_coords.jpg)
coords = [
    0.00,
    0.00,
    0.33,
    0.20,  # lower left
    0.67,
    0.00,
    1.00,
    0.00,
    0.80,
    0.33,  # lower right
    0.80,
    0.67,
    1.00,
    1.00,
    0.67,
    0.80,  # upper right
    0.33,
    1.00,
    0.00,
    1.00,
    0.20,
    0.67,  # upper left
    0.00,
    0.33,
]  # lower left
coords_min = 0.0  # minimum value of the coordinates
coords_max = 1.0  # maximum value of the coordinates

# paint a coons patch gradient with the above coordinates
pdf.CoonsPatchMesh(
    110, 115, 80, 80, yellow, blue, green, red, coords, coords_min, coords_max
)

# second page
pdf.AddPage()
pdf.Cell(0, 5, "Page 2", 0, 1, "C")
pdf.Ln()

# first patch: f = 0
patch_array = {0: {}, 1: {}, 2: {}, 3: {}}
patch_array[0]["f"] = 0
patch_array[0]["points"] = [
    0.00,
    0.00,
    0.33,
    0.00,
    0.67,
    0.00,
    1.00,
    0.00,
    1.00,
    0.33,
    0.8,
    0.67,
    1.00,
    1.00,
    0.67,
    0.8,
    0.33,
    1.80,
    0.00,
    1.00,
    0.00,
    0.67,
    0.00,
    0.33,
]
patch_array[0]["colors"] = {}
patch_array[0]["colors"][0] = {"r": 255.0, "g": 255.0, "b": 0.0}
patch_array[0]["colors"][1] = {"r": 0.0, "g": 0.0, "b": 255.0}
patch_array[0]["colors"][2] = {"r": 0.0, "g": 255.0, "b": 0.0}
patch_array[0]["colors"][3] = {"r": 255.0, "g": 0.0, "b": 0.0}

# second patch - above the other: f = 2
patch_array[1]["f"] = 2
patch_array[1]["points"] = [
    0.00,
    1.33,
    0.00,
    1.67,
    0.00,
    2.00,
    0.33,
    2.00,
    0.67,
    2.00,
    1.00,
    2.00,
    1.00,
    1.67,
    1.5,
    1.33,
]
patch_array[1]["colors"] = {}
patch_array[1]["colors"][0] = {"r": 0.0, "g": 0.0, "b": 0.0}
patch_array[1]["colors"][1] = {"r": 255.0, "g": 0.0, "b": 255.0}

# third patch - right of the above: f = 3
patch_array[2]["f"] = 3
patch_array[2]["points"] = [
    1.33,
    0.80,
    1.67,
    1.50,
    2.00,
    1.00,
    2.00,
    1.33,
    2.00,
    1.67,
    2.00,
    2.00,
    1.67,
    2.00,
    1.33,
    2.00,
]
patch_array[2]["colors"] = {}
patch_array[2]["colors"][0] = {"r": 0.0, "g": 255.0, "b": 255.0}
patch_array[2]["colors"][1] = {"r": 0.0, "g": 0.0, "b": 0.0}

# fourth patch - below the above, which means left(?) of the above: f = 1
patch_array[3]["f"] = 1
patch_array[3]["points"] = [
    2.00,
    0.67,
    2.00,
    0.33,
    2.00,
    0.00,
    1.67,
    0.00,
    1.33,
    0.00,
    1.00,
    0.00,
    1.00,
    0.33,
    0.8,
    0.67,
]
patch_array[3]["colors"] = {}
patch_array[3]["colors"][0] = {"r": 0.0, "g": 0.0, "b": 0.0}
patch_array[3]["colors"][1] = {"r": 0.0, "g": 0.0, "b": 255.0}

coords_min = 0
coords_max = 2

pdf.CoonsPatchMesh(
    10, 25, 190, 200, "", "", "", "", patch_array, coords_min, coords_max
)

pdf.Output("gradients.pdf", "F")
