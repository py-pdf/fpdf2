from fpdf.graphics_state import GraphicsStateMixin

f = GraphicsStateMixin()
# Push initial state in stack: gs0
gs0 = f._push_local_stack()
# Step 1 - set some graphic styles: gs1
f.font_size_pt = 16
f.underline = True
gs1 = f._get_current_graphics_state()
# Step 2 - restore gs0
f._pop_local_stack()
print(f"{f.font_size_pt=} {f.underline=}")
# -> f.font_size_pt=0 f.underline=False
