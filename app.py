import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, simpledialog
from PIL import ImageTk, Image, ImageGrab
import os
import time
import math

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Grafika Komputer - Professional Vector Editor")
        self.root.geometry("1100x750")
        
        # Apply modern theme
        self.style = ttk.Style()
        if 'clam' in self.style.theme_names():
            self.style.theme_use('clam')
            
        self.style.configure("TFrame", background="#e0e0e0")
        self.style.configure("Tool.TButton", padding=5)
        self.style.configure("Panel.TLabelframe", background="#e0e0e0", font=("Segoe UI", 9, "bold"))
        self.style.configure("Panel.TLabelframe.Label", background="#e0e0e0")

        self.root.configure(bg="#e0e0e0")

        # Tool states
        self.brush_color = "#000000"
        self.brush_size = 3
        self.tool = "select"

        self.last_x, self.last_y = None, None
        self.temp_shape = None
        self.start_time = 0

        self.undo_stack = []
        self.redo_stack = []
        self.selected_object = None
        self.selection_visuals = [] # To hold the Photoshop-like bounding box handles
        self.current_scales = {}

        self.setup_ui()

    def setup_ui(self):
        # 1. TOP BAR (File/Edit Actions)
        self.top_bar = tk.Frame(self.root, bg="#d0d0d0", bd=0, height=40)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(self.top_bar, text="💾 Save", command=self.save_canvas).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(self.top_bar, text="↩ Undo", command=self.undo).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(self.top_bar, text="↪ Redo", command=self.redo).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(self.top_bar, text="🗑 Clear Canvas", command=self.clear_canvas).pack(side=tk.LEFT, padx=5, pady=5)

        # Main Container
        self.main_container = tk.Frame(self.root, bg="#e0e0e0")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # 2. LEFT SIDEBAR (Tools)
        self.left_sidebar = tk.Frame(self.main_container, bg="#eeeeee", width=60, bd=1, relief=tk.SUNKEN)
        self.left_sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        self.tools = ["select", "line", "rect", "square", "oval", "circle", "triangle", "text"]
        self.tool_buttons = {}
        
        ttk.Label(self.left_sidebar, text="TOOLS", font=("Segoe UI", 8, "bold"), background="#eeeeee").pack(pady=(10, 5))
        
        for tool in self.tools:
            btn = ttk.Button(self.left_sidebar, text=tool.capitalize(), style="Tool.TButton",
                             command=lambda t=tool: self.select_tool(t))
            btn.pack(side=tk.TOP, padx=5, pady=2, fill=tk.X)
            self.tool_buttons[tool] = btn

        # 3. CENTER (Canvas area)
        self.canvas_frame = tk.Frame(self.main_container, bg="#cccccc", bd=2, relief=tk.SUNKEN)
        self.canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 4. RIGHT SIDEBAR (Inspector / Properties)
        self.right_panel = tk.Frame(self.main_container, bg="#e0e0e0", width=250)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=10)
        
        ttk.Label(self.right_panel, text="PROPERTIES", font=("Segoe UI", 10, "bold"), background="#e0e0e0").pack(pady=(0, 10))

        # Appearance Panel
        appearance_frame = ttk.LabelFrame(self.right_panel, text="Appearance", style="Panel.TLabelframe")
        appearance_frame.pack(fill=tk.X, pady=5, ipady=5)
        
        color_frame = tk.Frame(appearance_frame, bg="#e0e0e0")
        color_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(color_frame, text="Color:", background="#e0e0e0").pack(side=tk.LEFT)
        self.color_btn = tk.Button(color_frame, bg=self.brush_color, width=10, relief=tk.FLAT, borderwidth=1, command=self.choose_color)
        self.color_btn.pack(side=tk.RIGHT)

        ttk.Label(appearance_frame, text="Stroke Thickness:", background="#e0e0e0").pack(anchor=tk.W, padx=5, pady=(5,0))
        self.slider = ttk.Scale(appearance_frame, from_=1, to=20, orient=tk.HORIZONTAL, command=self.change_thickness)
        self.slider.set(self.brush_size)
        self.slider.pack(fill=tk.X, padx=5, pady=2)

        # Transform Panel
        transform_frame = ttk.LabelFrame(self.right_panel, text="Transform", style="Panel.TLabelframe")
        transform_frame.pack(fill=tk.X, pady=5, ipady=5)

        # -- Move
        ttk.Label(transform_frame, text="Move (px):", background="#e0e0e0").pack(anchor=tk.W, padx=5)
        move_ctrl_frame = tk.Frame(transform_frame, bg="#e0e0e0")
        move_ctrl_frame.pack(pady=2)
        
        self.pixel_var = tk.StringVar(value="10")
        ttk.Entry(move_ctrl_frame, textvariable=self.pixel_var, width=5).grid(row=1, column=3, padx=10)
        
        ttk.Button(move_ctrl_frame, text="↖", width=2, command=lambda: self.move_object(-1, -1)).grid(row=0, column=0)
        ttk.Button(move_ctrl_frame, text="↑", width=2, command=lambda: self.move_object(0, -1)).grid(row=0, column=1)
        ttk.Button(move_ctrl_frame, text="↗", width=2, command=lambda: self.move_object(1, -1)).grid(row=0, column=2)
        ttk.Button(move_ctrl_frame, text="←", width=2, command=lambda: self.move_object(-1, 0)).grid(row=1, column=0)
        ttk.Button(move_ctrl_frame, text="●", width=2, command=self.deselect_object).grid(row=1, column=1)
        ttk.Button(move_ctrl_frame, text="→", width=2, command=lambda: self.move_object(1, 0)).grid(row=1, column=2)
        ttk.Button(move_ctrl_frame, text="↙", width=2, command=lambda: self.move_object(-1, 1)).grid(row=2, column=0)
        ttk.Button(move_ctrl_frame, text="↓", width=2, command=lambda: self.move_object(0, 1)).grid(row=2, column=1)
        ttk.Button(move_ctrl_frame, text="↘", width=2, command=lambda: self.move_object(1, 1)).grid(row=2, column=2)

        ttk.Separator(transform_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8, padx=5)

        # -- Rotate & Scale
        rs_frame = tk.Frame(transform_frame, bg="#e0e0e0")
        rs_frame.pack(fill=tk.X, padx=5)
        
        ttk.Label(rs_frame, text="Rotate (°):", background="#e0e0e0").grid(row=0, column=0, sticky=tk.W)
        self.rotate_var = tk.StringVar(value="45")
        r_entry = ttk.Entry(rs_frame, textvariable=self.rotate_var, width=6)
        r_entry.grid(row=0, column=1, padx=5)
        r_entry.bind('<Return>', lambda e: self.apply_rotation())
        ttk.Button(rs_frame, text="Apply", width=6, command=self.apply_rotation).grid(row=0, column=2)

        ttk.Label(rs_frame, text="Scale (%):", background="#e0e0e0").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.scale_var = tk.IntVar(value=100)
        s_entry = ttk.Spinbox(rs_frame, from_=10, to=500, increment=10, textvariable=self.scale_var, width=4)
        s_entry.grid(row=1, column=1, padx=5, pady=5)
        s_entry.bind('<Return>', lambda e: self.apply_absolute_scale())
        ttk.Button(rs_frame, text="Apply", width=6, command=self.apply_absolute_scale).grid(row=1, column=2, pady=5)

        ttk.Separator(transform_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8, padx=5)

        # -- Shear
        sh_frame = tk.Frame(transform_frame, bg="#e0e0e0")
        sh_frame.pack(fill=tk.X, padx=5)
        ttk.Label(sh_frame, text="Shear Factor:", background="#e0e0e0").pack(side=tk.LEFT)
        self.shear_var = tk.StringVar(value="0.5")
        ttk.Entry(sh_frame, textvariable=self.shear_var, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Button(sh_frame, text="X", width=2, command=lambda: self.apply_shear('x')).pack(side=tk.LEFT)
        ttk.Button(sh_frame, text="Y", width=2, command=lambda: self.apply_shear('y')).pack(side=tk.LEFT, padx=2)

        ttk.Separator(transform_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8, padx=5)

        # -- Reflect
        rf_frame = tk.Frame(transform_frame, bg="#e0e0e0")
        rf_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        ttk.Label(rf_frame, text="Mirror:", background="#e0e0e0").pack(side=tk.LEFT)
        ttk.Button(rf_frame, text="Horiz ↔", width=8, command=lambda: self.apply_reflection('x')).pack(side=tk.LEFT, padx=5)
        ttk.Button(rf_frame, text="Vert ↕", width=8, command=lambda: self.apply_reflection('y')).pack(side=tk.LEFT)

        # Event Bindings
        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.reset)
        
        # Highlight initial tool
        self.select_tool("select")

    def choose_color(self):
        color = colorchooser.askcolor(initialcolor=self.brush_color)[1]
        if color:
            self.brush_color = color
            self.color_btn.config(bg=color)

    def select_tool(self, tool):
        self.tool = tool
        self.deselect_object() # Deselect when changing tools
        for t, btn in self.tool_buttons.items():
            if t == tool:
                btn.state(['pressed'])
            else:
                btn.state(['!pressed'])

    def clear_canvas(self):
        self.canvas.delete("all")
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_scales.clear()
        self.deselect_object()

    def undo(self):
        if self.undo_stack:
            item = self.undo_stack.pop()
            self.canvas.delete(item)
            self.redo_stack.append(item)
            self.deselect_object()

    def redo(self):
        if self.redo_stack:
            item = self.redo_stack.pop()
            self.canvas.itemconfigure(item, state='normal')
            self.undo_stack.append(item)

    def change_thickness(self, val):
        self.brush_size = int(float(val))

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.start_time = time.time()
        self.temp_shape = None
        
        if self.tool != "select":
            self.deselect_object()

    def draw(self, event):
        if self.tool in ["line", "rect", "oval", "square", "circle", "triangle"]:
            if self.temp_shape:
                self.canvas.delete(self.temp_shape)
                
            if self.tool == "line":
                self.temp_shape = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                                          fill=self.brush_color, width=self.brush_size)
            elif self.tool == "rect":
                self.temp_shape = self.canvas.create_rectangle(self.last_x, self.last_y, event.x, event.y,
                                                               outline=self.brush_color, width=self.brush_size)
            elif self.tool == "oval":
                self.temp_shape = self.canvas.create_oval(self.last_x, self.last_y, event.x, event.y,
                                                          outline=self.brush_color, width=self.brush_size)
            elif self.tool == "square":
                size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                x1, y1 = self.last_x, self.last_y
                x2 = x1 + size if event.x > x1 else x1 - size
                y2 = y1 + size if event.y > y1 else y1 - size
                self.temp_shape = self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.brush_color, width=self.brush_size)
            elif self.tool == "circle":
                size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                x1, y1 = self.last_x, self.last_y
                x2 = x1 + size if event.x > x1 else x1 - size
                y2 = y1 + size if event.y > y1 else y1 - size
                self.temp_shape = self.canvas.create_oval(x1, y1, x2, y2, outline=self.brush_color, width=self.brush_size)
            elif self.tool == "triangle":
                size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                points = [
                    self.last_x, self.last_y - size, 
                    self.last_x - size, self.last_y + size,  
                    self.last_x + size, self.last_y + size   
                ]
                self.temp_shape = self.canvas.create_polygon(*points, outline=self.brush_color, fill="", width=self.brush_size)

    def reset(self, event):
        if self.tool in ["line", "rect", "oval", "square", "circle", "triangle"] and self.temp_shape:
            coords = self.canvas.coords(self.temp_shape)
            self.canvas.delete(self.temp_shape)
            
            fill_color = self.brush_color if (time.time() - self.start_time > 1) else ""
            item = None
            
            if self.tool == "line":
                item = self.canvas.create_line(*coords, fill=self.brush_color, width=self.brush_size, capstyle=tk.ROUND)
            
            elif self.tool == "rect":
                x1, y1, x2, y2 = coords
                points = [x1, y1, x2, y1, x2, y2, x1, y2]
                item = self.canvas.create_polygon(*points, outline=self.brush_color, fill=fill_color, width=self.brush_size)
                
            elif self.tool == "square":
                size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                x1, y1 = self.last_x, self.last_y
                x2 = x1 + size if event.x > x1 else x1 - size
                y2 = y1 + size if event.y > y1 else y1 - size
                points = [x1, y1, x2, y1, x2, y2, x1, y2]
                item = self.canvas.create_polygon(*points, outline=self.brush_color, fill=fill_color, width=self.brush_size)
                
            elif self.tool == "oval":
                x1, y1, x2, y2 = coords
                cx, cy = (x1+x2)/2, (y1+y2)/2
                rx, ry = abs(x2-x1)/2, abs(y2-y1)/2
                points = []
                # Render curve at 120 points for high-quality smoothness
                for i in range(120):
                    a = math.radians(i * 3)
                    points.extend([cx + rx * math.cos(a), cy + ry * math.sin(a)])
                item = self.canvas.create_polygon(*points, outline=self.brush_color, fill=fill_color, width=self.brush_size, smooth=True)

            elif self.tool == "circle":
                size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                x1, y1 = self.last_x, self.last_y
                x2 = x1 + size if event.x > x1 else x1 - size
                y2 = y1 + size if event.y > y1 else y1 - size
                cx, cy = (x1+x2)/2, (y1+y2)/2
                r = size / 2
                points = []
                for i in range(120):
                    a = math.radians(i * 3)
                    points.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
                item = self.canvas.create_polygon(*points, outline=self.brush_color, fill=fill_color, width=self.brush_size, smooth=True)

            elif self.tool == "triangle":
                size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                points = [
                    self.last_x, self.last_y - size,  
                    self.last_x - size, self.last_y + size,  
                    self.last_x + size, self.last_y + size   
                ]
                item = self.canvas.create_polygon(*points, outline=self.brush_color, fill=fill_color, width=self.brush_size, joinstyle=tk.ROUND)
            
            if item:
                self.undo_stack.append(item)
            self.temp_shape = None
            
        elif self.tool == "text":
            text = simpledialog.askstring("Input Text", "Enter text:")
            if text:
                item = self.canvas.create_text(event.x, event.y, text=text, fill=self.brush_color, font=("Segoe UI", 16, "bold"), anchor=tk.NW)
                self.undo_stack.append(item)
                
        elif self.tool == "select":
            items_at_click = self.canvas.find_overlapping(event.x - 2, event.y - 2, event.x + 2, event.y + 2)
            # Filter out selection visuals from being selected themselves
            valid_items = [item for item in items_at_click if item not in self.selection_visuals]
            
            if valid_items:
                self.selected_object = valid_items[-1]
                self.update_selection_box()
                self.scale_var.set(int(self.current_scales.get(self.selected_object, 1.0) * 100))
            else:
                self.deselect_object()

        self.last_x, self.last_y = None, None

    # --- ADVANCED SELECTION VISUALS ---
    def update_selection_box(self):
        """Draws Photoshop-style bounding box handles around the selected object"""
        self.clear_selection_visuals()
        if not self.selected_object: return
        
        bbox = self.canvas.bbox(self.selected_object)
        if not bbox: return
        
        pad = 4 # Padding around object
        x1, y1, x2, y2 = bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad
        
        # Draw bounding outline
        outline = self.canvas.create_rectangle(x1, y1, x2, y2, outline="#00aaff", width=1, dash=(4, 4))
        self.selection_visuals.append(outline)
        
        # Draw 8 handle nodes
        cx, cy = (x1+x2)/2, (y1+y2)/2
        handles = [
            (x1, y1), (cx, y1), (x2, y1), # Top row
            (x1, cy),           (x2, cy), # Middle row
            (x1, y2), (cx, y2), (x2, y2)  # Bottom row
        ]
        
        s = 3 # handle half-size
        for hx, hy in handles:
            h = self.canvas.create_rectangle(hx-s, hy-s, hx+s, hy+s, fill="white", outline="#00aaff")
            self.selection_visuals.append(h)

    def clear_selection_visuals(self):
        for v in self.selection_visuals:
            self.canvas.delete(v)
        self.selection_visuals.clear()

    def deselect_object(self):
        self.clear_selection_visuals()
        self.selected_object = None
        self.scale_var.set(100)

    # --- TRANSFORMATIONS ---
    def _post_transform(self):
        """Helper to call after any transformation to update UI"""
        self.update_selection_box()

    def move_object(self, dx, dy):
        if not self.selected_object: return
        try:
            pixels = int(self.pixel_var.get())
        except ValueError:
            pixels = 10
        self.canvas.move(self.selected_object, dx * pixels, dy * pixels)
        self._post_transform()

    def apply_shear(self, axis):
        if not self.selected_object: return
        try: factor = float(self.shear_var.get())
        except ValueError: return 

        item_type = self.canvas.type(self.selected_object)
        if item_type in ["polygon", "line"]:
            coords = self.canvas.coords(self.selected_object)
            if not coords: return
            bbox = self.canvas.bbox(self.selected_object)
            cx, cy = (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0

            new_coords = []
            for i in range(0, len(coords), 2):
                x, y = coords[i] - cx, coords[i+1] - cy
                nx = x + (factor * y) if axis == 'x' else x
                ny = y + (factor * x) if axis == 'y' else y
                new_coords.extend([nx + cx, ny + cy])
            self.canvas.coords(self.selected_object, *new_coords)
            self._post_transform()

    def apply_reflection(self, axis):
        if not self.selected_object: return
        item_type = self.canvas.type(self.selected_object)

        if item_type in ["polygon", "line"]:
            coords = self.canvas.coords(self.selected_object)
            if not coords: return
            bbox = self.canvas.bbox(self.selected_object)
            cx, cy = (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0

            new_coords = []
            for i in range(0, len(coords), 2):
                x, y = coords[i], coords[i+1]
                nx = 2 * cx - x if axis == 'x' else x
                ny = 2 * cy - y if axis == 'y' else y
                new_coords.extend([nx, ny])
            self.canvas.coords(self.selected_object, *new_coords)
            self._post_transform()

    def apply_rotation(self):
        if not self.selected_object: return
        try: angle_deg = float(self.rotate_var.get())
        except ValueError: return

        item_type = self.canvas.type(self.selected_object)
        angle_rad = math.radians(angle_deg)
        cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)

        if item_type in ["polygon", "line"]:
            coords = self.canvas.coords(self.selected_object)
            if not coords: return
            bbox = self.canvas.bbox(self.selected_object)
            cx, cy = (bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0

            new_coords = []
            for i in range(0, len(coords), 2):
                x, y = coords[i] - cx, coords[i+1] - cy
                nx = x * cos_a - y * sin_a
                ny = x * sin_a + y * cos_a
                new_coords.extend([nx + cx, ny + cy])
            self.canvas.coords(self.selected_object, *new_coords)
        elif item_type == "text":
            try: current_angle = float(self.canvas.itemcget(self.selected_object, 'angle'))
            except: current_angle = 0.0
            self.canvas.itemconfigure(self.selected_object, angle=current_angle - angle_deg)
            
        self._post_transform()

    def apply_absolute_scale(self):
        if not self.selected_object: return
        try: target_scale = float(self.scale_var.get()) / 100.0
        except ValueError: return
        
        current_scale = self.current_scales.get(self.selected_object, 1.0)
        if target_scale == current_scale: return
            
        relative_factor = target_scale / current_scale
        coords = self.canvas.coords(self.selected_object)
        if not coords: return
        
        x_coords, y_coords = coords[0::2], coords[1::2]
        center_x, center_y = sum(x_coords) / len(x_coords), sum(y_coords) / len(y_coords)
        
        self.canvas.scale(self.selected_object, center_x, center_y, relative_factor, relative_factor)
        if self.canvas.type(self.selected_object) == "text":
            new_size = int(16 * target_scale)
            self.canvas.itemconfigure(self.selected_object, font=("Segoe UI", max(1, new_size), "bold"))
            
        self.current_scales[self.selected_object] = target_scale
        self._post_transform()

    def save_canvas(self):
        self.deselect_object() # Ensure UI elements aren't saved
        self.root.update()
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if filepath:
            ImageGrab.grab().crop((x, y, x1, y1)).save(filepath)
            print(f"Saved to {filepath}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()