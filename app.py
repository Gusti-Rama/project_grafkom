import tkinter as tk
from tkinter import colorchooser, filedialog, simpledialog
from PIL import ImageTk, Image, ImageGrab
import os
import random
import time

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
        
        # Dictionary to track the current scaling factor of each object
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
        self.translation_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

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

        # Scaling Control Panel
        self.scale_frame = tk.Frame(self.root, bd=2, relief=tk.RAISED)
        self.scale_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=0)

        tk.Label(self.scale_frame, text="Scaling:").pack(side=tk.LEFT, padx=5)
        self.scale_var = tk.DoubleVar(value=1.0)

        for s in range(25, 225, 25): # Loop generating 25 to 200 increments of 25
            tk.Radiobutton(
                self.scale_frame, text=f"{s}%", variable=self.scale_var, value=s/100.0,
                command=self.apply_absolute_scale
            ).pack(side=tk.LEFT, padx=2)
            
        tk.Label(self.scale_frame, text="(Select shape first to change size)", font=("Arial", 8)).pack(side=tk.LEFT, padx=10)

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
                x1 = self.last_x
                y1 = self.last_y
                x2 = self.last_x + size if event.x > self.last_x else self.last_x - size
                y2 = self.last_y + size if event.y > self.last_y else self.last_y - size
                self.temp_shape = self.canvas.create_rectangle(x1, y1, x2, y2,
                                                               outline=self.brush_color, width=self.brush_size)
            elif self.tool == "circle":
                size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                x1 = self.last_x
                y1 = self.last_y
                x2 = self.last_x + size if event.x > self.last_x else self.last_x - size
                y2 = self.last_y + size if event.y > self.last_y else self.last_y - size
                self.temp_shape = self.canvas.create_oval(x1, y1, x2, y2,
                                                          outline=self.brush_color, width=self.brush_size)
            elif self.tool == "triangle":
                size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                points = [
                    self.last_x, self.last_y - size, 
                    self.last_x - size, self.last_y + size,  
                    self.last_x + size, self.last_y + size   
                ]
                self.temp_shape = self.canvas.create_polygon(*points, outline=self.brush_color,
                                                             fill="", width=self.brush_size)

    def reset(self, event):
        if self.tool in ["line", "rect", "oval", "square", "circle", "triangle"] and self.temp_shape:
            coords = self.canvas.coords(self.temp_shape)
            self.canvas.delete(self.temp_shape)
            if time.time() - self.start_time > 1:
                item = self.canvas.create_rectangle(*coords, fill=self.brush_color)
            else:
                if self.tool == "line":
                    item = self.canvas.create_line(*coords, fill=self.brush_color, width=self.brush_size)
                elif self.tool == "rect":
                    item = self.canvas.create_rectangle(*coords, outline=self.brush_color, width=self.brush_size)
                elif self.tool == "oval":
                    item = self.canvas.create_oval(*coords, outline=self.brush_color, width=self.brush_size)
                elif self.tool == "square":
                    size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                    x1 = self.last_x
                    y1 = self.last_y
                    x2 = self.last_x + size if event.x > self.last_x else self.last_x - size
                    y2 = self.last_y + size if event.y > self.last_y else self.last_y - size
                    item = self.canvas.create_rectangle(x1, y1, x2, y2,
                                                       outline=self.brush_color, width=self.brush_size)
                elif self.tool == "circle":
                    size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                    x1 = self.last_x
                    y1 = self.last_y
                    x2 = self.last_x + size if event.x > self.last_x else self.last_x - size
                    y2 = self.last_y + size if event.y > self.last_y else self.last_y - size
                    item = self.canvas.create_oval(x1, y1, x2, y2,
                                                  outline=self.brush_color, width=self.brush_size)
                elif self.tool == "triangle":
                    size = max(abs(event.x - self.last_x), abs(event.y - self.last_y))
                    points = [
                        self.last_x, self.last_y - size,  
                        self.last_x - size, self.last_y + size,  
                        self.last_x + size, self.last_y + size   
                    ]
                    item = self.canvas.create_polygon(*points, outline=self.brush_color,
                                                     fill="", width=self.brush_size)
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
                
                # Fetch shape's current size state to update the radio button properly
                self.scale_var.set(self.current_scales.get(self.selected_object, 1.0))
            else:
                self.deselect_object()

        self.last_x, self.last_y = None, None

    def apply_absolute_scale(self):
        """Scale the object absolutely based on user selected percentage"""
        if not self.selected_object:
            return
            
        target_scale = self.scale_var.get()
        current_scale = self.current_scales.get(self.selected_object, 1.0)
        
        if target_scale == current_scale:
            return
            
        # Calculate exactly how much bigger/smaller it needs to get relative to current form
        relative_factor = target_scale / current_scale
        
        coords = self.canvas.coords(self.selected_object)
        if not coords: return
        
        # Calculate the mathematical center point of the object
        x_coords = coords[0::2]
        y_coords = coords[1::2]
        center_x = sum(x_coords) / len(x_coords)
        center_y = sum(y_coords) / len(y_coords)
        
        # Scale the coordinates relative to its center
        self.canvas.scale(self.selected_object, center_x, center_y, relative_factor, relative_factor)
        
        # Adjust text font size if text is scaled
        if self.canvas.type(self.selected_object) == "text":
            new_size = int(14 * target_scale)
            self.canvas.itemconfigure(self.selected_object, font=("Arial", max(1, new_size)))
            
        # Update the dictionary storing current shapes sizes
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
        
        # Reset the scaling radio buttons to 100% when no item is selected
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