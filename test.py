# Import the required libraries
import tkinter as tk
from PIL import Image, ImageTk

# Create an instance of tkinter frame or window
win=tk.Tk()
frame = tk.Frame(master=win,width=700, height=600)
# Set the size of the window
win.geometry("700x600")
frame.pack()

# Create a canvas widget
canvas=tk.Canvas(master=frame, width=700, height=600)
canvas.pack()

# Load the image
img=ImageTk.PhotoImage(file="temp.png")

# Add the image in the canvas
canvas.create_image(350, 400, image=img, anchor="center")

win.mainloop()
