import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
from PIL import ImageGrab
import math

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Grafika Komputer")
        self.root.geometry("1100x750")
        
        self.root.configure(bg="#1e1e1e")
        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
            
        self.style.configure("TFrame", background="#252526")
        self.style.configure("Dark.TFrame", background="#1e1e1e")
        
        self.style.configure("TButton", background="#3e3e42", foreground="#cccccc", borderwidth=0, padding=5, font=("Segoe UI", 9))
        self.style.map("TButton", background=[("active", "#505050"), ("pressed", "#007acc")])
        
        self.style.configure("Tool.TButton", background="#252526", foreground="#cccccc", borderwidth=0, padding=6)
        self.style.map("Tool.TButton", background=[("active", "#3e3e42"), ("pressed", "#007acc")])
        
        self.style.configure("TLabel", background="#252526", foreground="#cccccc", font=("Segoe UI", 9))
        self.style.configure("Title.TLabel", background="#252526", foreground="#ffffff", font=("Segoe UI", 10, "bold"))
        
        self.style.configure("TLabelframe", background="#252526", bordercolor="#3e3e42")
        self.style.configure("TLabelframe.Label", background="#252526", foreground="#007acc", font=("Segoe UI", 9, "bold"))
        self.style.configure("TSeparator", background="#3e3e42")


        self.stroke_color = "#000000"
        self.fill_color = "" 
        self.stroke_width = 3
        self.tool = "select"

        self.last_x, self.last_y = None, None
        self.temp_shape = None

        self.undo_stack = []
        self.redo_stack = []
        
        self.selected_object = None
        self.selection_visuals = [] 
        self.current_scales = {}

        self.setup_ui()

    def setup_ui(self):
        # 1. TOP BAR 
        self.top_bar = tk.Frame(self.root, bg="#333333", bd=0, height=45)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)
        self.top_bar.pack_propagate(False)
        
        action_frame = tk.Frame(self.top_bar, bg="#333333")
        action_frame.pack(side=tk.LEFT, padx=10, pady=7)
        
        ttk.Button(action_frame, text="💾 Save", command=self.save_canvas).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="↩ Undo", command=self.undo).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="↪ Redo", command=self.redo).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🗑 Clear Canvas", command=self.clear_canvas).pack(side=tk.LEFT, padx=5)

        # 2. MAIN WORKSPACE
        self.main_container = tk.Frame(self.root, bg="#1e1e1e")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Objek objek
        self.left_sidebar = tk.Frame(self.main_container, bg="#252526", width=65)
        self.left_sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        self.tools = ["select", "line", "persegi panjang", "kotak", "oval", "lingkaran", "segitiga"]
        self.tool_buttons = {}
        
        ttk.Label(self.left_sidebar, text="Objek", style="Title.TLabel").pack(pady=(15, 10))
        
        for tool in self.tools:
            btn = ttk.Button(self.left_sidebar, text=tool.capitalize(), style="Tool.TButton",
                             command=lambda t=tool: self.select_tool(t))
            btn.pack(side=tk.TOP, padx=5, pady=2, fill=tk.X)
            self.tool_buttons[tool] = btn

        # Canvas
        self.canvas_frame = tk.Frame(self.main_container, bg="#1e1e1e")
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=10)        
        self.canvas = tk.Canvas(self.canvas_frame, bg="#ffffff", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Properties
        self.right_panel = ttk.Frame(self.main_container)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=10)
        
        ttk.Label(self.right_panel, text="Menu", style="Title.TLabel").pack(pady=(5, 10))

        appearance_frame = ttk.LabelFrame(self.right_panel, text="Tampilan")
        appearance_frame.pack(fill=tk.X, pady=5, ipady=5, padx=5)
        
        color_frame = ttk.Frame(appearance_frame)
        color_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(color_frame, text="Stroke:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.stroke_color_btn = tk.Button(color_frame, bg=self.stroke_color, width=3, relief=tk.FLAT, cursor="hand2", command=self.choose_stroke_color)
        self.stroke_color_btn.grid(row=0, column=1, padx=5, sticky=tk.W)

        ttk.Label(color_frame, text="Fill:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.fill_color_btn = tk.Button(color_frame, bg="#252526", text="X", fg="#ff5555", width=3, relief=tk.FLAT, cursor="hand2", command=self.choose_fill_color)
        self.fill_color_btn.grid(row=1, column=1, padx=5, sticky=tk.W)
        ttk.Button(color_frame, text="Clear", width=5, command=self.clear_fill_color).grid(row=1, column=2, padx=5)

        ttk.Label(appearance_frame, text="Ketebalan Stroke:").pack(anchor=tk.W, padx=10, pady=(10,0))
        self.slider = ttk.Scale(appearance_frame, from_=1, to=20, orient=tk.HORIZONTAL, command=self.change_thickness_drag)
        self.slider.set(self.stroke_width)
        self.slider.pack(fill=tk.X, padx=10, pady=5)
        
        self.slider.bind("<ButtonPress-1>", self.on_slider_press)
        self.slider.bind("<ButtonRelease-1>", self.on_slider_release)

        # Transform Panel
        transform_frame = ttk.LabelFrame(self.right_panel, text="Transformasi")
        transform_frame.pack(fill=tk.X, pady=5, ipady=5, padx=5)

        # Translasi
        ttk.Label(transform_frame, text="Translasi (px):").pack(anchor=tk.W, padx=10)
        move_ctrl = ttk.Frame(transform_frame)
        move_ctrl.pack(pady=5)
        
        self.pixel_var = tk.StringVar(value="10")
        ttk.Entry(move_ctrl, textvariable=self.pixel_var, width=5).grid(row=1, column=3, padx=10)
        
        ttk.Button(move_ctrl, text="↖", width=2, command=lambda: self.move_object(-1, -1)).grid(row=0, column=0)
        ttk.Button(move_ctrl, text="↑", width=2, command=lambda: self.move_object(0, -1)).grid(row=0, column=1)
        ttk.Button(move_ctrl, text="↗", width=2, command=lambda: self.move_object(1, -1)).grid(row=0, column=2)
        ttk.Button(move_ctrl, text="←", width=2, command=lambda: self.move_object(-1, 0)).grid(row=1, column=0)
        ttk.Button(move_ctrl, text="●", width=2, command=self.deselect_object).grid(row=1, column=1)
        ttk.Button(move_ctrl, text="→", width=2, command=lambda: self.move_object(1, 0)).grid(row=1, column=2)
        ttk.Button(move_ctrl, text="↙", width=2, command=lambda: self.move_object(-1, 1)).grid(row=2, column=0)
        ttk.Button(move_ctrl, text="↓", width=2, command=lambda: self.move_object(0, 1)).grid(row=2, column=1)
        ttk.Button(move_ctrl, text="↘", width=2, command=lambda: self.move_object(1, 1)).grid(row=2, column=2)

        ttk.Separator(transform_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10, padx=10)

        # Rotasi & Skala
        rs_frame = ttk.Frame(transform_frame)
        rs_frame.pack(fill=tk.X, padx=10)
        
        ttk.Label(rs_frame, text="Rotasi (°):").grid(row=0, column=0, sticky=tk.W)
        self.rotate_var = tk.StringVar(value="45")
        r_entry = ttk.Entry(rs_frame, textvariable=self.rotate_var, width=6)
        r_entry.grid(row=0, column=1, padx=5)
        r_entry.bind('<Return>', lambda e: self.apply_rotation())
        ttk.Button(rs_frame, text="Apply", width=6, command=self.apply_rotation).grid(row=0, column=2)

        ttk.Label(rs_frame, text="Skala (%):").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.scale_var = tk.IntVar(value=100)
        s_entry = ttk.Spinbox(rs_frame, from_=10, to=500, increment=10, textvariable=self.scale_var, width=4)
        s_entry.grid(row=1, column=1, padx=5, pady=8)
        s_entry.bind('<Return>', lambda e: self.apply_absolute_scale())
        ttk.Button(rs_frame, text="Apply", width=6, command=self.apply_absolute_scale).grid(row=1, column=2, pady=8)

        ttk.Separator(transform_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10, padx=10)

        # Shear & Refleksi
        sh_frame = ttk.Frame(transform_frame)
        sh_frame.pack(fill=tk.X, padx=10)
        
        ttk.Label(sh_frame, text="Shear:").grid(row=0, column=0, sticky=tk.W)
        self.shear_var = tk.StringVar(value="0.5")
        ttk.Entry(sh_frame, textvariable=self.shear_var, width=5).grid(row=0, column=1, padx=(5,10))
        ttk.Button(sh_frame, text="X", width=2, command=lambda: self.apply_shear('x')).grid(row=0, column=2)
        ttk.Button(sh_frame, text="Y", width=2, command=lambda: self.apply_shear('y')).grid(row=0, column=3, padx=2)

        ttk.Label(sh_frame, text="Refleksi:").grid(row=1, column=0, sticky=tk.W, pady=(12,0))
        ttk.Button(sh_frame, text="X ↔", width=6, command=lambda: self.apply_reflection('x')).grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=(5,0), pady=(12,0))
        ttk.Button(sh_frame, text="Y ↕", width=6, command=lambda: self.apply_reflection('y')).grid(row=1, column=3, sticky=tk.W, padx=2, pady=(12,0))

        # Events
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.reset)
        
        self.select_tool("select")

    def add_action(self, action):
        self.undo_stack.append(action)
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack: return
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        
        if action['type'] == 'draw':
            self.canvas.itemconfig(action['item'], state='hidden')
            self.deselect_object()
            
        elif action['type'] == 'transform':
            self.canvas.coords(action['item'], *action['prev_coords'])
            if 'prev_scale' in action:
                self.current_scales[action['item']] = action['prev_scale']
                if self.selected_object == action['item']:
                    self.scale_var.set(int(action['prev_scale'] * 100))
            self.update_selection_box()
            
        elif action['type'] == 'recolor':
            item_type = self.canvas.type(action['item'])
            if item_type == "line":
                self.canvas.itemconfig(action['item'], fill=action['prev_outline'], width=action['prev_width'])
            else:
                self.canvas.itemconfig(action['item'], outline=action['prev_outline'], fill=action['prev_fill'], width=action['prev_width'])
            
            if self.selected_object == action['item']:
                self.update_ui_from_selection()
            self.update_selection_box()

    def redo(self):
        if not self.redo_stack: return
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        
        if action['type'] == 'draw':
            self.canvas.itemconfig(action['item'], state='normal')
            
        elif action['type'] == 'transform':
            self.canvas.coords(action['item'], *action['new_coords'])
            if 'new_scale' in action:
                self.current_scales[action['item']] = action['new_scale']
                if self.selected_object == action['item']:
                    self.scale_var.set(int(action['new_scale'] * 100))
            self.update_selection_box()
            
        elif action['type'] == 'recolor':
            item_type = self.canvas.type(action['item'])
            if item_type == "line":
                self.canvas.itemconfig(action['item'], fill=action['new_outline'], width=action['new_width'])
            else:
                self.canvas.itemconfig(action['item'], outline=action['new_outline'], fill=action['new_fill'], width=action['new_width'])
            
            if self.selected_object == action['item']:
                self.update_ui_from_selection()
            self.update_selection_box()

    def select_tool(self, tool):
        self.tool = tool
        self.deselect_object()
        for t, btn in self.tool_buttons.items():
            if t == tool: btn.state(['pressed'])
            else: btn.state(['!pressed'])

    def update_ui_from_selection(self):
        if not self.selected_object: return
        
        item_type = self.canvas.type(self.selected_object)
        width = float(self.canvas.itemcget(self.selected_object, 'width'))
        
        if item_type == "line":
            stroke = self.canvas.itemcget(self.selected_object, 'fill')
            fill = ""
        else:
            stroke = self.canvas.itemcget(self.selected_object, 'outline')
            fill = self.canvas.itemcget(self.selected_object, 'fill')
            
        self.stroke_color = stroke
        self.stroke_color_btn.config(bg=stroke if stroke else "#252526")
        
        self.fill_color = fill
        self.fill_color_btn.config(bg=fill if fill else "#252526", text="" if fill else "X")
        
        self.stroke_width = width
        self.slider.set(width)

    def choose_stroke_color(self):
        color = colorchooser.askcolor(initialcolor=self.stroke_color if self.stroke_color else "#cccccc")[1]
        if color:
            self._apply_stroke(color)

    def _apply_stroke(self, color):
        prev_stroke = self.stroke_color
        self.stroke_color = color
        self.stroke_color_btn.config(bg=color)
        
        if self.selected_object:
            item_type = self.canvas.type(self.selected_object)
            prev_width = float(self.canvas.itemcget(self.selected_object, 'width'))
            
            if item_type == "line":
                prev_outline = self.canvas.itemcget(self.selected_object, 'fill')
                self.canvas.itemconfig(self.selected_object, fill=color)
                prev_fill = ""
            else:
                prev_outline = self.canvas.itemcget(self.selected_object, 'outline')
                prev_fill = self.canvas.itemcget(self.selected_object, 'fill')
                self.canvas.itemconfig(self.selected_object, outline=color)
                
            self.add_action({
                'type': 'recolor', 'item': self.selected_object,
                'prev_outline': prev_outline, 'new_outline': color,
                'prev_fill': prev_fill, 'new_fill': prev_fill,
                'prev_width': prev_width, 'new_width': prev_width
            })

    def choose_fill_color(self):
        color = colorchooser.askcolor(initialcolor=self.fill_color if self.fill_color else "#ffffff")[1]
        if color:
            self._apply_fill(color)

    def clear_fill_color(self):
        self._apply_fill("")

    def _apply_fill(self, color):
        self.fill_color = color
        self.fill_color_btn.config(bg=color if color else "#252526", text="" if color else "X")
        
        if self.selected_object:
            item_type = self.canvas.type(self.selected_object)
            if item_type == "line": return # Lines don't have standard fills
            
            prev_outline = self.canvas.itemcget(self.selected_object, 'outline')
            prev_fill = self.canvas.itemcget(self.selected_object, 'fill')
            prev_width = float(self.canvas.itemcget(self.selected_object, 'width'))
            
            self.canvas.itemconfig(self.selected_object, fill=color)
            
            self.add_action({
                'type': 'recolor', 'item': self.selected_object,
                'prev_outline': prev_outline, 'new_outline': prev_outline,
                'prev_fill': prev_fill, 'new_fill': color,
                'prev_width': prev_width, 'new_width': prev_width
            })

    def change_thickness_drag(self, val):
        self.stroke_width = float(val)
        if self.selected_object:
            self.canvas.itemconfig(self.selected_object, width=self.stroke_width)
            self.update_selection_box()

    def on_slider_press(self, event):
        if self.selected_object:
            self.drag_start_width = float(self.canvas.itemcget(self.selected_object, 'width'))

    def on_slider_release(self, event):
        if self.selected_object and hasattr(self, 'drag_start_width'):
            new_w = float(self.canvas.itemcget(self.selected_object, 'width'))
            if self.drag_start_width != new_w:
                item_type = self.canvas.type(self.selected_object)
                outline = self.canvas.itemcget(self.selected_object, 'fill' if item_type == "line" else 'outline')
                fill = "" if item_type == "line" else self.canvas.itemcget(self.selected_object, 'fill')
                
                self.add_action({
                    'type': 'recolor', 'item': self.selected_object,
                    'prev_outline': outline, 'new_outline': outline,
                    'prev_fill': fill, 'new_fill': fill,
                    'prev_width': self.drag_start_width, 'new_width': new_w
                })

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.temp_shape = None
        if self.tool != "select":
            self.deselect_object()

    def draw(self, event):
        if self.tool in ["line", "rect", "oval", "square", "circle", "triangle"]:
            if self.temp_shape: self.canvas.delete(self.temp_shape)
                
            if self.tool == "line":
                self.temp_shape = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, fill=self.stroke_color, width=self.stroke_width)
            elif self.tool in ["rect", "square"]:
                x1, y1 = self.last_x, self.last_y
                if self.tool == "square":
                    size = max(abs(event.x - x1), abs(event.y - y1))
                    x2 = x1 + size if event.x > x1 else x1 - size
                    y2 = y1 + size if event.y > y1 else y1 - size
                else:
                    x2, y2 = event.x, event.y
                self.temp_shape = self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.stroke_color, width=self.stroke_width)
            elif self.tool in ["oval", "circle"]:
                x1, y1 = self.last_x, self.last_y
                if self.tool == "circle":
                    size = max(abs(event.x - x1), abs(event.y - y1))
                    x2 = x1 + size if event.x > x1 else x1 - size
                    y2 = y1 + size if event.y > y1 else y1 - size
                else:
                    x2, y2 = event.x, event.y
                self.temp_shape = self.canvas.create_oval(x1, y1, x2, y2, outline=self.stroke_color, width=self.stroke_width)
            elif self.tool == "triangle":
                size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                points = [self.last_x, self.last_y - size, self.last_x - size, self.last_y + size, self.last_x + size, self.last_y + size]
                self.temp_shape = self.canvas.create_polygon(*points, outline=self.stroke_color, fill="", width=self.stroke_width)

    def reset(self, event):
        if self.tool in ["line", "rect", "oval", "square", "circle", "triangle"] and self.temp_shape:
            coords = self.canvas.coords(self.temp_shape)
            self.canvas.delete(self.temp_shape)
            item = None
            
            if self.tool == "line":
                item = self.canvas.create_line(*coords, fill=self.stroke_color, width=self.stroke_width, capstyle=tk.ROUND)
            
            elif self.tool in ["rect", "square"]:
                x1, y1, x2, y2 = coords
                points = [x1, y1, x2, y1, x2, y2, x1, y2]
                item = self.canvas.create_polygon(*points, outline=self.stroke_color, fill=self.fill_color, width=self.stroke_width)
                
            elif self.tool in ["oval", "circle"]:
                x1, y1, x2, y2 = coords
                cx, cy = (x1+x2)/2, (y1+y2)/2
                rx, ry = abs(x2-x1)/2, abs(y2-y1)/2
                points = []
                for i in range(120):
                    a = math.radians(i * 3)
                    points.extend([cx + rx * math.cos(a), cy + ry * math.sin(a)])
                item = self.canvas.create_polygon(*points, outline=self.stroke_color, fill=self.fill_color, width=self.stroke_width, smooth=True)

            elif self.tool == "triangle":
                size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                points = [self.last_x, self.last_y - size, self.last_x - size, self.last_y + size, self.last_x + size, self.last_y + size]
                item = self.canvas.create_polygon(*points, outline=self.stroke_color, fill=self.fill_color, width=self.stroke_width, joinstyle=tk.ROUND)
            
            if item:
                self.add_action({'type': 'draw', 'item': item})
            self.temp_shape = None
                
        elif self.tool == "select":
            items_at_click = self.canvas.find_overlapping(event.x - 2, event.y - 2, event.x + 2, event.y + 2)
            valid_items = [i for i in items_at_click if i not in self.selection_visuals]
            
            if valid_items:
                self.selected_object = valid_items[-1]
                self.update_selection_box()
                self.scale_var.set(int(self.current_scales.get(self.selected_object, 1.0) * 100))
                self.update_ui_from_selection()
            else:
                self.deselect_object()

    def update_selection_box(self):
        self.clear_selection_visuals()
        if not self.selected_object: return
        
        bbox = self.canvas.bbox(self.selected_object)
        if not bbox: return
        
        pad = 4
        x1, y1, x2, y2 = bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad
        
        outline = self.canvas.create_rectangle(x1, y1, x2, y2, outline="#00aaff", width=1, dash=(4, 4))
        self.selection_visuals.append(outline)
        
        cx, cy = (x1+x2)/2, (y1+y2)/2
        handles = [(x1, y1), (cx, y1), (x2, y1), (x1, cy), (x2, cy), (x1, y2), (cx, y2), (x2, y2)]
        
        s = 3
        for hx, hy in handles:
            h = self.canvas.create_rectangle(hx-s, hy-s, hx+s, hy+s, fill="#1e1e1e", outline="#00aaff")
            self.selection_visuals.append(h)

    def clear_selection_visuals(self):
        for v in self.selection_visuals:
            self.canvas.delete(v)
        self.selection_visuals.clear()

    def deselect_object(self):
        self.clear_selection_visuals()
        self.selected_object = None
        self.scale_var.set(100)

    def move_object(self, dx, dy):
        if not self.selected_object: return
        try: pixels = int(self.pixel_var.get())
        except ValueError: pixels = 10
        
        prev_coords = self.canvas.coords(self.selected_object)
        self.canvas.move(self.selected_object, dx * pixels, dy * pixels)
        new_coords = self.canvas.coords(self.selected_object)
        
        self.add_action({'type': 'transform', 'item': self.selected_object, 'prev_coords': prev_coords, 'new_coords': new_coords})
        self.update_selection_box()

    def apply_shear(self, axis):
        if not self.selected_object: return
        try: factor = float(self.shear_var.get())
        except ValueError: return 

        if self.canvas.type(self.selected_object) in ["polygon", "line"]:
            prev_coords = self.canvas.coords(self.selected_object)
            if not prev_coords: return
            bbox = self.canvas.bbox(self.selected_object)
            cx, cy = (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0

            new_coords = []
            for i in range(0, len(prev_coords), 2):
                x, y = prev_coords[i] - cx, prev_coords[i+1] - cy
                nx = x + (factor * y) if axis == 'x' else x
                ny = y + (factor * x) if axis == 'y' else y
                new_coords.extend([nx + cx, ny + cy])
                
            self.canvas.coords(self.selected_object, *new_coords)
            self.add_action({'type': 'transform', 'item': self.selected_object, 'prev_coords': prev_coords, 'new_coords': new_coords})
            self.update_selection_box()

    def apply_reflection(self, axis):
        if not self.selected_object: return
        
        if self.canvas.type(self.selected_object) in ["polygon", "line"]:
            prev_coords = self.canvas.coords(self.selected_object)
            if not prev_coords: return
            bbox = self.canvas.bbox(self.selected_object)
            cx, cy = (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0

            new_coords = []
            for i in range(0, len(prev_coords), 2):
                x, y = prev_coords[i], prev_coords[i+1]
                nx = 2 * cx - x if axis == 'x' else x
                ny = 2 * cy - y if axis == 'y' else y
                new_coords.extend([nx, ny])
                
            self.canvas.coords(self.selected_object, *new_coords)
            self.add_action({'type': 'transform', 'item': self.selected_object, 'prev_coords': prev_coords, 'new_coords': new_coords})
            self.update_selection_box()

    def apply_rotation(self):
        if not self.selected_object: return
        try: angle_deg = float(self.rotate_var.get())
        except ValueError: return

        if self.canvas.type(self.selected_object) in ["polygon", "line"]:
            prev_coords = self.canvas.coords(self.selected_object)
            if not prev_coords: return
            bbox = self.canvas.bbox(self.selected_object)
            cx, cy = (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0

            angle_rad = math.radians(angle_deg)
            cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

            new_coords = []
            for i in range(0, len(prev_coords), 2):
                x, y = prev_coords[i] - cx, prev_coords[i+1] - cy
                nx = x * cos_a - y * sin_a
                ny = x * sin_a + y * cos_a
                new_coords.extend([nx + cx, ny + cy])
                
            self.canvas.coords(self.selected_object, *new_coords)
            self.add_action({'type': 'transform', 'item': self.selected_object, 'prev_coords': prev_coords, 'new_coords': new_coords})
            self.update_selection_box()

    def apply_absolute_scale(self):
        if not self.selected_object: return
        try: target_scale = float(self.scale_var.get()) / 100.0
        except ValueError: return
        
        current_scale = self.current_scales.get(self.selected_object, 1.0)
        if target_scale == current_scale: return
            
        relative_factor = target_scale / current_scale
        prev_coords = self.canvas.coords(self.selected_object)
        if not prev_coords: return
        
        x_coords, y_coords = prev_coords[0::2], prev_coords[1::2]
        center_x, center_y = sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords)
        
        self.canvas.scale(self.selected_object, center_x, center_y, relative_factor, relative_factor)
        new_coords = self.canvas.coords(self.selected_object)
        
        self.current_scales[self.selected_object] = target_scale
        
        self.add_action({
            'type': 'transform', 'item': self.selected_object,
            'prev_coords': prev_coords, 'new_coords': new_coords,
            'prev_scale': current_scale, 'new_scale': target_scale
        })
        self.update_selection_box()

    def clear_canvas(self):
        self.canvas.delete("all")
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_scales.clear()
        self.deselect_object()

    def save_canvas(self):
        self.deselect_object()
        self.root.update()
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if filepath:
            ImageGrab.grab().crop((x, y, x1, y1)).save(filepath)

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()