from turtle import width

from traitlets import default
import fitz
import crop_tool as crop
import pdf_reader as reader
import pdf_grouper as grouper
import argparse
import tkinter as tk

my_font = ('Segoe UI', 20)
bold_font = ('Segoe UI', 20, 'bold')

def round_rectangle(parent:tk.Canvas, x1, y1, x2, y2, r=25, **kwargs):    
    width = 5
    # alter points with width so that rectangle draws within bounds
    x1 = x1 + width
    y1 = y1 + width
    x2 = x2 - width
    y2 = y2 - width
    points = (x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1)
    return parent.create_polygon(points, outline='orange',width=width,**kwargs, smooth=True)

def add_background(widget:tk.Widget, color = 'black'):
    widget.configure(highlightbackground=color, highlightthickness=1)

class CardContainer(tk.Frame):
    pass    

class FileCard(tk.Frame):
    def __init__(self, parent, text = 'hi', w = 500, h = 100) -> None:
        tk.Frame.__init__(self, parent,width=w, height =h,)
        self.canvas = tk.Canvas(self, width=w, height=h)
        self.entry_frame = tk.Frame(self, width = 100, height = h, background='red')
        self.init_entries(self.entry_frame)
        self.border_rect = round_rectangle(self.canvas, 0, 0, w, h, r=25,fill ='blue')
        self.entry_frame.pack(side='right', ipadx=5)
        self.canvas.pack(expand=True, side = 'left')
        self.canvas.bind('<Configure>', self.resize)
    
    def resize(self, event):
        self.canvas.delete(self.border_rect)
        self.border_rect = round_rectangle(self.canvas, 0, 0, 
                    event.width, event.height, r=25,fill ='blue')
        
    def init_entries(self, frame):
        frame.full_page_var = tk.BooleanVar(frame)
        frame.full_page_entry = crop.CheckButtonWithLabel(frame, 
                                    "Full page", frame.full_page_var)
        validate_cmd = frame.register(self.validate_input)
        self.count_entry = tk.Entry(frame, validate='key', 
                                    validatecommand=(validate_cmd, '%P'),width=5)
        self.count_entry.insert(0, '1')
        frame.count_label = tk.Label(frame, text='Count = ')
        frame.full_page_entry.pack(side='top',expand=True,fill='both')
        frame.count_label.pack(side='left')
        self.count_entry.pack(side='right')
    
    def validate_input(self, new_value: str) -> bool:
        if new_value == '': return True
        try:
            int(new_value)
            return True
        except ValueError:
            return False
    
    def self

class packet_GUI(tk.Toplevel):
    def __init__(self, parent) -> None:
        tk.Toplevel.__init__(self, parent)
        # self.geometry('1000x1000')
        self.grid_rowconfigure(1, weight = 1)
        self.grid_columnconfigure(1, weight = 1)
        self.main_frame = tk.Frame(self, background='yellow',height = 500, width = 500)
        # add_background(self.main_frame)
        self.main_frame.grid_rowconfigure(1, weight = 1)
        self.main_frame.grid_columnconfigure(1, weight = 1)
        self.tile_frame = tk.Frame(self.main_frame,height=500, width=500,background='green')
        self.tile_frame.grid(row=1, column=1)
        # add_background(self.tile_frame)
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
