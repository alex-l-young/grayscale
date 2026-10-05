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

        # --- UI Layout ---
        # Control Panel (Left Side)
        self.control_frame = ttk.Frame(self.root, padding="10")
        self.control_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.load_btn = ttk.Button(self.control_frame, text="Load Photo", command=self.load_image)
        self.load_btn.pack(pady=10, fill=tk.X)

        self.save_btn = ttk.Button(self.control_frame, text="Save Result", command=self.save_image, state=tk.DISABLED)
        self.save_btn.pack(pady=10, fill=tk.X)

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

        self.image_label = tk.Label(self.canvas_frame, text="Load an image to begin", bg="gray")
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

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

        # Resize for performance and display (max 800x800)
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)

        self.original_image = img
        self.gray_array = np.array(self.original_image)
        self.save_btn.config(state=tk.NORMAL)

        self.update_sliders()

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
        self.tk_image = ImageTk.PhotoImage(self.display_image)
        self.image_label.config(image=self.tk_image, text="")

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