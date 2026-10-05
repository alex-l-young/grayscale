import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk, ImageOps
import numpy as np


class ValueStudyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Artwork Value Study Tool")
        self.root.geometry("1000x700")

        # --- Variables ---
        self.original_image = None
        self.display_image = None
        self.gray_array = None
        self.tk_image = None
        self.sliders = []
        self.zoom = 1.0
        self.fit_mode = True
        self.img_offset = (0, 0)

        # --- UI Layout ---
        # Control Panel (Left Side)
        self.control_frame = ttk.Frame(self.root, padding="10")
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.load_btn = ttk.Button(self.control_frame, text="Load Photo", command=self.load_image)
        self.load_btn.pack(pady=10, fill=tk.X)

        self.save_btn = ttk.Button(self.control_frame, text="Save Result", command=self.save_image, state=tk.DISABLED)
        self.save_btn.pack(pady=10, fill=tk.X)

        ttk.Separator(self.control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Zoom controls
        zoom_frame = ttk.Frame(self.control_frame)
        zoom_frame.pack(fill=tk.X)
        ttk.Button(zoom_frame, text="\u2212", width=3, command=self.zoom_out).pack(side=tk.LEFT)
        self.zoom_label = ttk.Label(zoom_frame, text="100%", anchor=tk.CENTER, width=6)
        self.zoom_label.pack(side=tk.LEFT, expand=True)
        ttk.Button(zoom_frame, text="+", width=3, command=self.zoom_in).pack(side=tk.LEFT)
        ttk.Button(self.control_frame, text="Fit to Window", command=self.zoom_fit).pack(pady=(5, 0), fill=tk.X)
        ttk.Button(self.control_frame, text="Actual Size (100%)", command=self.zoom_actual).pack(pady=(5, 0), fill=tk.X)

        ttk.Separator(self.control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        self.stops_label = ttk.Label(self.control_frame, text="Number of Stops:")
        self.stops_label.pack()

        # Spinbox to choose number of stops (1 to 10)
        self.stops_var = tk.IntVar(value=3)
        self.stops_spinbox = ttk.Spinbox(
            self.control_frame, from_=1, to=10, textvariable=self.stops_var,
            command=self.update_sliders, width=5
        )
        self.stops_spinbox.pack(pady=5)

        # Frame to hold the dynamic sliders
        self.sliders_frame = ttk.Frame(self.control_frame)
        self.sliders_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Image Display Area (Right Side)
        self.canvas_frame = ttk.Frame(self.root)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="gray", highlightthickness=0)
        self.hbar = ttk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.vbar = ttk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.image_id = None
        self.hint_id = self.canvas.create_text(
            0, 0, text="Load an image to begin", fill="white", tags="hint")

        # Zoom / pan bindings. Command (macOS) or Control (Windows/Linux) + wheel zooms;
        # plain wheel scrolls; click-drag pans.
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Command-MouseWheel>", self.on_zoom_wheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.on_zoom_wheel(e, 1) if e.state & 0x4 else self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.on_zoom_wheel(e, -1) if e.state & 0x4 else self.canvas.yview_scroll(1, "units"))
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))
        for mod in ("Command", "Control"):
            self.root.bind(f"<{mod}-plus>", lambda e: self.zoom_in())
            self.root.bind(f"<{mod}-equal>", lambda e: self.zoom_in())
            self.root.bind(f"<{mod}-minus>", lambda e: self.zoom_out())
            self.root.bind(f"<{mod}-Key-0>", lambda e: self.zoom_fit())

    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not file_path:
            return

        # Load the raw image
        img = Image.open(file_path)

        # FIX: Read the EXIF data and rotate the image right-side up if needed
        img = ImageOps.exif_transpose(img)

        # Convert to grayscale
        img = img.convert("L")

        # Resize for performance and display (max 2000x2000)
        img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)

        self.original_image = img
        self.gray_array = np.array(self.original_image)
        self.save_btn.config(state=tk.NORMAL)

        self.fit_mode = True
        self.update_sliders()

    # --- Zoom -----------------------------------------------------------
    MIN_ZOOM, MAX_ZOOM = 0.1, 8.0

    def set_zoom(self, zoom, anchor=None):
        """Set zoom, keeping the image point under `anchor` (canvas x, y) fixed."""
        if self.display_image is None:
            return
        zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))
        old = self.zoom
        if anchor is None:
            anchor = (self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2)
        # Image coordinates under the anchor before zooming
        ix = (self.canvas.canvasx(anchor[0]) - self.img_offset[0]) / old
        iy = (self.canvas.canvasy(anchor[1]) - self.img_offset[1]) / old
        self.zoom = zoom
        self.render()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        # Scroll so the same image point sits under the anchor again
        self.scroll_to(self.img_offset[0] + ix * zoom - anchor[0],
                       self.img_offset[1] + iy * zoom - anchor[1])

    def scroll_to(self, x, y):
        _, _, w, h = (float(v) for v in self.canvas.cget("scrollregion").split())
        if w > 0:
            self.canvas.xview_moveto(max(0, x) / w)
        if h > 0:
            self.canvas.yview_moveto(max(0, y) / h)

    def zoom_in(self):
        self.fit_mode = False
        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self):
        self.fit_mode = False
        self.set_zoom(self.zoom / 1.25)

    def zoom_actual(self):
        self.fit_mode = False
        self.set_zoom(1.0)

    def zoom_fit(self):
        if self.display_image is None:
            return
        self.fit_mode = True
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        iw, ih = self.display_image.size
        self.set_zoom(min(cw / iw, ch / ih))

    def on_zoom_wheel(self, event, direction=None):
        if direction is None:
            direction = 1 if event.delta > 0 else -1
        self.fit_mode = False
        self.set_zoom(self.zoom * (1.1 ** direction), anchor=(event.x, event.y))

    def on_mousewheel(self, event):
        if event.state & 0x4 or event.state & 0x8:  # Ctrl / Command held
            return self.on_zoom_wheel(event)
        # macOS reports small deltas, Windows reports multiples of 120
        step = -event.delta if abs(event.delta) < 10 else -event.delta // 120
        if event.state & 0x1:  # Shift scrolls horizontally
            self.canvas.xview_scroll(step, "units")
        else:
            self.canvas.yview_scroll(step, "units")

    def on_canvas_resize(self, event):
        if self.display_image is None:
            self.canvas.coords(self.hint_id, event.width / 2, event.height / 2)
        elif self.fit_mode:
            self.zoom_fit()
        else:
            self.render()

    def render(self):
        """Draw display_image at the current zoom, centered if smaller than the canvas."""
        iw, ih = self.display_image.size
        w, h = max(1, round(iw * self.zoom)), max(1, round(ih * self.zoom))
        resample = Image.Resampling.NEAREST if self.zoom > 1 else Image.Resampling.BILINEAR
        shown = self.display_image.resize((w, h), resample)
        self.tk_image = ImageTk.PhotoImage(shown)

        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.img_offset = (max(0, (cw - w) // 2), max(0, (ch - h) // 2))
        self.canvas.delete("hint")
        if self.image_id is None:
            self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        else:
            self.canvas.itemconfig(self.image_id, image=self.tk_image)
        self.canvas.coords(self.image_id, *self.img_offset)
        self.canvas.configure(scrollregion=(
            0, 0, max(cw, w), max(ch, h)))
        self.zoom_label.config(text=f"{round(self.zoom * 100)}%")

    def update_sliders(self):
        # Clear existing sliders
        for widget in self.sliders_frame.winfo_children():
            widget.destroy()

        self.sliders.clear()

        try:
            num_stops = int(self.stops_var.get())
        except ValueError:
            num_stops = 3  # Default fallback

        # Create evenly spaced default values for the stops
        default_stops = np.linspace(0, 255, num_stops + 2)[1:-1]

        for i in range(num_stops):
            frame = ttk.Frame(self.sliders_frame)
            frame.pack(fill=tk.X, pady=2)

            lbl = ttk.Label(frame, text=f"Stop {i + 1}:")
            lbl.pack(side=tk.LEFT)

            # Slider mapping 1 to 254 (0 is pure black, 255 is pure white)
            slider = tk.Scale(
                frame, from_=1, to=254, orient=tk.HORIZONTAL,
                command=lambda val: self.process_image()
            )
            slider.set(int(default_stops[i]))
            slider.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            self.sliders.append(slider)

        self.process_image()

    def process_image(self):
        if self.gray_array is None:
            return

        # Get current values from all sliders and sort them
        stops = sorted([slider.get() for slider in self.sliders])

        # numpy.digitize bins the array.
        # e.g., if stops=[100], values < 100 get index 0, values >= 100 get index 1
        indices = np.digitize(self.gray_array, stops)

        # Calculate the output colors for the bins (evenly spaced grays from 0 to 255)
        num_bins = len(stops) + 1
        bin_colors = np.linspace(0, 255, num_bins).astype(np.uint8)

        # Map the binned indices to the actual gray color values
        quantized_array = bin_colors[indices]

        # Convert back to PIL Image and update UI
        self.display_image = Image.fromarray(quantized_array, mode="L")
        if self.fit_mode:
            self.root.update_idletasks()
            self.zoom_fit()
        else:
            self.render()

    def save_image(self):
        if self.display_image is None:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")]
        )
        if file_path:
            self.display_image.save(file_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = ValueStudyApp(root)
    root.mainloop()