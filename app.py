import tkinter as tk
from tkinter import colorchooser, filedialog, simpledialog
from PIL import ImageTk, Image, ImageGrab
import os
import random
import time
import math

class DrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Grafika Komputer - Advanced Drawing App")

        self.brush_color = "black"
        self.brush_size = 3
        self.tool = "pencil"

        self.last_x, self.last_y = None, None
        self.temp_shape = None
        self.start_time = 0

        self.icon_images = {}
        self.tool_buttons = {}
        self.tools = ["color", "pencil", "crayon", "eraser", "line", "rect", "oval", "square", "circle", "triangle", "text", "select", "clear", "save", "undo", "redo"]

        self.undo_stack = []
        self.redo_stack = []
        self.selected_object = None
        
        # Tracking scale
        self.current_scales = {}

        self.setup_ui()

    def setup_ui(self):
        self.toolbar = tk.Frame(self.root, bd=2, relief=tk.RAISED)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        for tool in self.tools:
            img_path = os.path.join("icons", f"{tool}.png")
            if not os.path.exists(img_path):
                img_path = os.path.join("icons", f"{tool}.jpg")
            if not os.path.exists(img_path):
                img_path = os.path.join("icons", f"{tool}.jpeg")
            if os.path.exists(img_path):
                img = Image.open(img_path).resize((32, 32))
                self.icon_images[tool] = ImageTk.PhotoImage(img)
                btn = tk.Button(self.toolbar, image=self.icon_images[tool],
                                command=lambda t=tool: self.select_tool(t))
                btn.pack(side=tk.LEFT, padx=4, pady=2)
                self.tool_buttons[tool] = btn
            else:
                btn = tk.Button(self.toolbar, text=tool.capitalize(), command=lambda t=tool: self.select_tool(t))
                btn.pack(side=tk.LEFT, padx=4, pady=2)
                self.tool_buttons[tool] = btn

        tk.Label(self.toolbar, text="Thickness:").pack(side=tk.LEFT, padx=(10, 2))
        self.slider = tk.Scale(self.toolbar, from_=1, to=20, orient=tk.HORIZONTAL, command=self.change_thickness)
        self.slider.set(self.brush_size)
        self.slider.pack(side=tk.LEFT)

        self.canvas = tk.Canvas(self.root, bg="white", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Translation Control Panel
        self.translation_frame = tk.Frame(self.root, bd=2, relief=tk.RAISED)
        self.translation_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        tk.Label(self.translation_frame, text="Translation (Move):").pack(side=tk.LEFT, padx=5)

        # Pixels input
        tk.Label(self.translation_frame, text="Pixels:").pack(side=tk.LEFT, padx=(10, 2))
        self.pixel_var = tk.StringVar(value="10")
        self.pixel_entry = tk.Entry(self.translation_frame, textvariable=self.pixel_var, width=5)
        self.pixel_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Direction buttons (8-directional)
        button_frame1 = tk.Frame(self.translation_frame)
        button_frame1.pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame1, text="↖", width=3, command=lambda: self.move_object(-1, -1)).grid(row=0, column=0, padx=1)
        tk.Button(button_frame1, text="↑", width=3, command=lambda: self.move_object(0, -1)).grid(row=0, column=1, padx=1)
        tk.Button(button_frame1, text="↗", width=3, command=lambda: self.move_object(1, -1)).grid(row=0, column=2, padx=1)

        tk.Button(button_frame1, text="←", width=3, command=lambda: self.move_object(-1, 0)).grid(row=1, column=0, padx=1)
        tk.Button(button_frame1, text="●", width=3, command=self.deselect_object, relief=tk.SUNKEN).grid(row=1, column=1, padx=1)
        tk.Button(button_frame1, text="→", width=3, command=lambda: self.move_object(1, 0)).grid(row=1, column=2, padx=1)

        tk.Button(button_frame1, text="↙", width=3, command=lambda: self.move_object(-1, 1)).grid(row=2, column=0, padx=1)
        tk.Button(button_frame1, text="↓", width=3, command=lambda: self.move_object(0, 1)).grid(row=2, column=1, padx=1)
        tk.Button(button_frame1, text="↘", width=3, command=lambda: self.move_object(1, 1)).grid(row=2, column=2, padx=1)
        
        tk.Label(self.translation_frame, text="(Select object with 'Select' tool)", font=("Arial", 8)).pack(side=tk.LEFT, padx=10)

        # Reflection Control Panel
        self.reflection_frame = tk.Frame(self.root, bd=2, relief=tk.RAISED)
        self.reflection_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        tk.Label(self.reflection_frame, text="Reflection (Mirror):").pack(side=tk.LEFT, padx=5)
        tk.Button(self.reflection_frame, text="Horizontal (↔)", command=lambda: self.apply_reflection('x')).pack(side=tk.LEFT, padx=5)
        tk.Button(self.reflection_frame, text="Vertical (↕)", command=lambda: self.apply_reflection('y')).pack(side=tk.LEFT, padx=5)
        tk.Label(self.reflection_frame, text="(Flips shape relative to its center)", font=("Arial", 8)).pack(side=tk.LEFT, padx=10)

        # Shear Control Panel (NEW)
        self.shear_frame = tk.Frame(self.root, bd=2, relief=tk.RAISED)
        self.shear_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        tk.Label(self.shear_frame, text="Shear Factor:").pack(side=tk.LEFT, padx=5)
        self.shear_var = tk.StringVar(value="0.5")  # Typical values are between -2.0 and 2.0
        self.shear_entry = tk.Entry(self.shear_frame, textvariable=self.shear_var, width=5)
        self.shear_entry.pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(self.shear_frame, text="Shear X", command=lambda: self.apply_shear('x')).pack(side=tk.LEFT, padx=5)
        tk.Button(self.shear_frame, text="Shear Y", command=lambda: self.apply_shear('y')).pack(side=tk.LEFT, padx=5)
        tk.Label(self.shear_frame, text="(Slants shape along axis. Try 0.5 or -0.5)", font=("Arial", 8)).pack(side=tk.LEFT, padx=10)

        # Rotation Control Panel
        self.rotation_frame = tk.Frame(self.root, bd=2, relief=tk.RAISED)
        self.rotation_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        tk.Label(self.rotation_frame, text="Rotation (Degrees):").pack(side=tk.LEFT, padx=5)
        self.rotate_var = tk.StringVar(value="45")
        self.rotate_entry = tk.Entry(self.rotation_frame, textvariable=self.rotate_var, width=5)
        self.rotate_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.rotate_entry.bind('<Return>', lambda e: self.apply_rotation())

        tk.Button(self.rotation_frame, text="Rotate Shape", command=self.apply_rotation).pack(side=tk.LEFT, padx=5)
        tk.Label(self.rotation_frame, text="(Rotates relative to current position)", font=("Arial", 8)).pack(side=tk.LEFT, padx=10)

        # Scaling Control Panel
        self.scale_frame = tk.Frame(self.root, bd=2, relief=tk.RAISED)
        self.scale_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

        tk.Label(self.scale_frame, text="Scaling:").pack(side=tk.LEFT, padx=5)
        self.scale_var = tk.DoubleVar(value=1.0)

        for s in range(25, 225, 25): 
            tk.Radiobutton(
                self.scale_frame, text=f"{s}%", variable=self.scale_var, value=s/100.0,
                command=self.apply_absolute_scale
            ).pack(side=tk.LEFT, padx=2)

        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.reset)

    def select_tool(self, tool):
        if tool == "color":
            color = colorchooser.askcolor()[1]
            if color:
                self.brush_color = color
        elif tool == "clear":
            self.canvas.delete("all")
            self.undo_stack.clear()
            self.current_scales.clear()
            self.deselect_object()
        elif tool == "save":
            self.save_canvas()
        elif tool == "undo":
            if self.undo_stack:
                item = self.undo_stack.pop()
                self.canvas.delete(item)
                self.redo_stack.append(item)
                self.deselect_object()
        elif tool == "redo":
            if self.redo_stack:
                item = self.redo_stack.pop()
                self.canvas.itemconfigure(item, state='normal')
                self.undo_stack.append(item)
        else:
            self.tool = tool
            for t, btn in self.tool_buttons.items():
                btn.config(relief=tk.SUNKEN if t == tool else tk.RAISED)

    def change_thickness(self, val):
        self.brush_size = int(val)

    def start_draw(self, event):
        self.last_x, self.last_y = event.x, event.y
        self.start_time = time.time()
        self.temp_shape = None

    def draw(self, event):
        if self.tool == "pencil":
            item = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                           fill=self.brush_color, width=self.brush_size,
                                           capstyle=tk.ROUND, smooth=True)
            self.undo_stack.append(item)
            self.last_x, self.last_y = event.x, event.y

        elif self.tool == "crayon":
            for _ in range(3):
                offset_x = random.randint(-2, 2)
                offset_y = random.randint(-2, 2)
                item = self.canvas.create_line(
                    self.last_x + offset_x, self.last_y + offset_y,
                    event.x + offset_x, event.y + offset_y,
                    fill=self.brush_color, width=max(1, self.brush_size - 1),
                    capstyle=tk.ROUND, smooth=True, stipple="gray50"
                )
                self.undo_stack.append(item)
            self.last_x, self.last_y = event.x, event.y

        elif self.tool == "eraser":
            item = self.canvas.create_line(self.last_x, self.last_y, event.x, event.y,
                                           fill="white", width=self.brush_size,
                                           capstyle=tk.ROUND, smooth=True)
            self.undo_stack.append(item)
            self.last_x, self.last_y = event.x, event.y

        elif self.tool in ["line", "rect", "oval", "square", "circle", "triangle"]:
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
            
            if self.tool == "line":
                item = self.canvas.create_line(*coords, fill=self.brush_color, width=self.brush_size)
            
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
                for i in range(72):
                    a = math.radians(i * 5)
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
                for i in range(72):
                    a = math.radians(i * 5)
                    points.extend([cx + r * math.cos(a), cy + r * math.sin(a)])
                item = self.canvas.create_polygon(*points, outline=self.brush_color, fill=fill_color, width=self.brush_size, smooth=True)

            elif self.tool == "triangle":
                size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                points = [
                    self.last_x, self.last_y - size,  
                    self.last_x - size, self.last_y + size,  
                    self.last_x + size, self.last_y + size   
                ]
                item = self.canvas.create_polygon(*points, outline=self.brush_color, fill=fill_color, width=self.brush_size)
            
            self.undo_stack.append(item)
            self.temp_shape = None
            
        elif self.tool == "text":
            text = simpledialog.askstring("Input Text", "Masukkan teks:")
            if text:
                item = self.canvas.create_text(event.x, event.y, text=text, fill=self.brush_color, font=("Arial", 14), anchor=tk.NW)
                self.undo_stack.append(item)
                
        elif self.tool == "select":
            items_at_click = self.canvas.find_overlapping(event.x - 2, event.y - 2, event.x + 2, event.y + 2)
            if items_at_click:
                self.selected_object = items_at_click[-1]  
                self.highlight_selected()
                self.scale_var.set(self.current_scales.get(self.selected_object, 1.0))
            else:
                self.deselect_object()

        self.last_x, self.last_y = None, None

    def apply_shear(self, axis):
        """Applies a shear transformation to the shape along the X or Y axis."""
        if not self.selected_object:
            return

        try:
            factor = float(self.shear_var.get())
        except ValueError:
            return  # Ignore if user enters non-numeric text

        item_type = self.canvas.type(self.selected_object)

        if item_type in ["polygon", "line"]:
            coords = self.canvas.coords(self.selected_object)
            if not coords: return
            
            bbox = self.canvas.bbox(self.selected_object)
            if not bbox: return
            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0

            new_coords = []
            for i in range(0, len(coords), 2):
                x = coords[i] - cx
                y = coords[i+1] - cy
                
                if axis == 'x':
                    nx = x + (factor * y)
                    ny = y
                else:  # axis == 'y'
                    nx = x
                    ny = y + (factor * x)
                    
                new_coords.extend([nx + cx, ny + cy])
            
            self.canvas.coords(self.selected_object, *new_coords)
            
        elif item_type == "text":
            print("Native Tkinter text cannot be sheared easily.")

    def apply_reflection(self, axis):
        if not self.selected_object:
            return

        item_type = self.canvas.type(self.selected_object)

        if item_type in ["polygon", "line"]:
            coords = self.canvas.coords(self.selected_object)
            if not coords: return
            
            bbox = self.canvas.bbox(self.selected_object)
            if not bbox: return
            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0

            new_coords = []
            for i in range(0, len(coords), 2):
                x = coords[i]
                y = coords[i+1]
                
                if axis == 'x':  
                    nx = 2 * cx - x
                    ny = y
                else:            
                    nx = x
                    ny = 2 * cy - y
                    
                new_coords.extend([nx, ny])
            
            self.canvas.coords(self.selected_object, *new_coords)
            
        elif item_type == "text":
            print("Native Tkinter text cannot be mirrored easily. Skipping text reflection.")

    def apply_rotation(self):
        if not self.selected_object:
            return
            
        try:
            angle_deg = float(self.rotate_var.get())
        except ValueError:
            return

        item_type = self.canvas.type(self.selected_object)
        angle_rad = math.radians(angle_deg)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        if item_type in ["polygon", "line"]:
            coords = self.canvas.coords(self.selected_object)
            if not coords: return
            
            bbox = self.canvas.bbox(self.selected_object)
            if not bbox: return
            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0

            new_coords = []
            for i in range(0, len(coords), 2):
                x = coords[i] - cx
                y = coords[i+1] - cy
                
                nx = x * cos_a - y * sin_a
                ny = x * sin_a + y * cos_a
                
                new_coords.extend([nx + cx, ny + cy])
            
            self.canvas.coords(self.selected_object, *new_coords)
            
        elif item_type == "text":
            try:
                current_angle = float(self.canvas.itemcget(self.selected_object, 'angle'))
            except:
                current_angle = 0.0
            self.canvas.itemconfigure(self.selected_object, angle=current_angle - angle_deg)
            
        self.rotate_entry.delete(0, tk.END)

    def apply_absolute_scale(self):
        if not self.selected_object: return
            
        target_scale = self.scale_var.get()
        current_scale = self.current_scales.get(self.selected_object, 1.0)
        
        if target_scale == current_scale: return
            
        relative_factor = target_scale / current_scale
        
        coords = self.canvas.coords(self.selected_object)
        if not coords: return
        
        x_coords = coords[0::2]
        y_coords = coords[1::2]
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        
        self.canvas.scale(self.selected_object, center_x, center_y, relative_factor, relative_factor)
        
        if self.canvas.type(self.selected_object) == "text":
            new_size = int(14 * target_scale)
            self.canvas.itemconfigure(self.selected_object, font=("Arial", max(1, new_size)))
            
        self.current_scales[self.selected_object] = target_scale

    def save_canvas(self):
        self.root.update()
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty()
        x1 = x + self.canvas.winfo_width()
        y1 = y + self.canvas.winfo_height()
        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if filepath:
            ImageGrab.grab().crop((x, y, x1, y1)).save(filepath)
            print(f"Saved to {filepath}")

    def highlight_selected(self):
        if self.selected_object:
            self.canvas.itemconfig(self.selected_object, dash=(2, 2), width=2)

    def deselect_object(self):
        if self.selected_object:
            self.canvas.itemconfig(self.selected_object, dash=())
        self.selected_object = None
        
        if hasattr(self, 'scale_var'):
            self.scale_var.set(1.0)

    def move_object(self, dx, dy):
        if not self.selected_object:
            return
        try:
            pixels = int(self.pixel_var.get())
        except ValueError:
            pixels = 10
        
        move_x = dx * pixels
        move_y = dy * pixels
        
        self.canvas.move(self.selected_object, move_x, move_y)


if __name__ == "__main__":
    root = tk.Tk()
    app = DrawingApp(root)
    root.mainloop()