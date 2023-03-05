from cmath import exp
from tkinter import * 
from PIL import Image, ImageTk

app = Tk()
app.geometry("400x400")

canvas = Canvas(app, bg='red')
canvas.pack(anchor='nw', fill='both', expand=1)

image = ImageTk.PhotoImage(file='img.png')
canvas.create_image(0, 0, image=image)

app.mainloop()