from importlib.metadata import entry_points
from tkinter import Toplevel
from tkinter import *
import os
import tkinter.simpledialog

class MyPrompt(tkinter.simpledialog.Dialog):
    win = None
    entries = []
    entry_boxes = []
    def __init__(self, parent, title, entries):
        self.entries = entries
        super(MyPrompt, self).__init__(parent, title)

    # override
    def body(self, parent):
        for i in range(len(self.entries)):
            Label(parent, text = os.path.basename(self.entries[i]).strip('.pdf').strip('alt_')).grid(row=i)
            self.entry_boxes.append(Entry(parent).grid(row = i, column = 1))
        return parent

    # override
    def ok(event = None):

        super(MyPrompt, self).ok(event)

    # def apply(self):
    #     print(self.entry_boxes)
    #     for e in self.entry_boxes:
    #         print(e)
    #         print(e.get())