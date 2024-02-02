from turtle import width
import pdf_reader as reader
import pdf_grouper as grouper
import argparse
import tkinter as tk

my_font = ('Segoe UI', 20)
bold_font = ('Segoe UI', 20, 'bold')

def round_rectangle(parent:tk.Canvas, x1, y1, x2, y2, r=25, **kwargs):    
    points = (x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1)
    return parent.create_polygon(points, outline='black',width=5,**kwargs, smooth=True)

def add_background(widget:tk.Widget, color = 'black'):
    widget.configure(highlightbackground=color, highlightthickness=1)

class FileCard(tk.Frame):
    def __init__(self, parent, text = 'hi', w = 500, h = 100) -> None:
        tk.Frame.__init__(self, parent,width=w, height =h,)
        self.configure(background='orange')
        self.grid(row =1, column=1)
        self.grid_rowconfigure(1, weight = 1)
        self.columnconfigure(1, weight =1)
        self.canvas = tk.Canvas(self, background='orange')
        self.canvas.grid(row = 1, column = 1, sticky='nwes')
        self.label = tk.Label(self, text=text,font = my_font)
        self.canvas.create_window(100, 100, height = 100, width = 100,window = self.label)
        # self.canvas.grid_rowconfigure(1, weight =1)
        # self.canvas.grid_columnconfigure(1, weight = 1)
        border_rect = round_rectangle(self.canvas, 10, 10, 100, 100, r=25,fill ='')
        # border_rect.grid(row =1, column = 2, sticky='nwes')
        add_background(self)

    def create_border():
        pass


class packet_GUI(tk.Toplevel):
    def __init__(self, parent) -> None:
        tk.Toplevel.__init__(self, parent)
        # self.geometry('1000x1000')
        self.grid_rowconfigure(1, weight = 1)
        self.grid_columnconfigure(1, weight = 1)
        self.main_frame = tk.Frame(self, background='yellow',height = 500, width = 500)
        add_background(self.main_frame)
        self.main_frame.grid_rowconfigure(1, weight = 1)
        self.main_frame.grid_columnconfigure(1, weight = 1)
        self.tile_frame = tk.Frame(self.main_frame,height=500, width=500,background='green')
        self.tile_frame.grid(row=1, column=1)
        add_background(self.tile_frame)
        card1 = FileCard(self.tile_frame)
        card1.grid(row = 1, column = 1)
        self.tile_frame.grid_rowconfigure(1, weight =1)
        self.tile_frame.grid_columnconfigure(1, weight =1)
        # self.cards = []
        self.main_frame.grid(row = 1, column =1)
        self.bind("<Destroy>", self.kill_root)
        self.mainloop()
        pass


    def create_cards(text: list[str]):
        for s in text:
            pass


    def kill_root(self, event) -> None:
        if event.widget == self and self.master.winfo_exists():
            self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    packet_GUI(root)
