from curses.textpad import Textbox
from importlib.metadata import entry_points
from tkinter import Toplevel
from tkinter import *

import fitz
import os
import tkinter.simpledialog

class PrinterPrompt(tkinter.simpledialog.Dialog):
    win = None
    fndict = {}
    pixmaps = []
    current = 0
    
    def __init__(self, parent, title, filepath):
        doc = fitz.open(filepath)
        for page in doc:
            self.pixmaps.append(page.Pixmap())
        super(PrinterPrompt, self).__init__(parent, title)
        

    # override
    def body(self, parent):
        Label(parent, text= "Filename", side=LEFT, padx = 5)
        Textbox(parent, side=LEFT, padx=5)
        Button(parent, text='Next Page', command = next()).pack(
                    side=LEFT, padx=5)
        Canvas(parent, width = 500, height = 500, bg = "white", )
        return parent

    def next(self):
        # update fndict
        self.fndict[self.pixmaps[self.current]] =  
        self.current += 1
        self.drawPixmap(self.current)
        pass
    
    def drawPixmap(self, canvas, index):
        canvas.delete('image')
        canvas.create_img(PhotoImage(data= self.pixmaps[index], tags = ['image']))
    # override
    def ok(event = None):
        super(PrinterPrompt).ok(event)

    # def apply(self):
    #     print(self.entry_boxes)
    #     for e in self.entry_boxes:
    #         print(e)
    #         print(e.get())