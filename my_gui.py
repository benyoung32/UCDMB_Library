# -*- coding: utf-8 -*-
import os
import sys
import glob
import pathlib
from typing import List
import pdf_reader
from PIL import Image, ImageTk
from fitz import *
from tkinterdnd2 import *
import tkinter as tk

# dict linking filenames with their filepaths 
filedict = {}

root = TkinterDnD.Tk()
root.withdraw()
root.title('TkinterDnD demo')
root.minsize(width = 600, height = 400)
root.geometry("600x400")
root.grid_rowconfigure(1, weight=1, minsize=250)
root.grid_columnconfigure(0, weight=1, minsize=300)
root.grid_columnconfigure(1, weight=1, minsize=300)



tk.Label(root, text='Drag and drop files here:').grid(
                    row=0, column=0, padx=10, pady=5)
buttonbox = tk.Frame(root)
buttonbox.grid(row=2, column=0, columnspan=2, pady=5)

def add_files(filepaths: List[str]):
    if not type(filepaths) == list:
        filepaths = [filepaths]
    for f in filepaths:
        # print(f)
        if os.path.exists(f):
            if os.path.isdir(f):
                add_files(glob.glob(f + "/*.pdf"))
            if '.pdf' in f and (not os.path.basename(f) in filedict):
                listbox.insert('end', os.path.basename(f))
                filedict[os.path.basename(f)] = f

def remove_files(range, delete = False):
    paths = listbox.get(range[0], range[1])
    listbox.delete(range[0], range[1])
    for path in paths:
        filedict.pop(path)
        if delete:
            os.remove(path)
def get_sel(get_one = False):
    if len((sel := listbox.curselection())) > 0:
        if (get_one):
            if len(sel) == 1:
                return sel
            else:
                return -1
        return (min(sel), max(sel))
    return -1

def create_pdf():
    range = get_sel()
    print(range)
    prompt = printer_prompt.PrinterPrompt(root, 'how many', listbox.get(range[0], range[1]))
    print(prompt.result)

def conv_pdf():
    range = get_sel()
    files = listbox.get(range[0], range[1])
    paths = [filedict[file] for file in files]
    add_files(pdf_reader.process_docs(paths))

# open folder using system file explorer
def open_folder():
    answer = tk.filedialog.askdirectory(parent=root,
                                 initialdir=os.getcwd(),
                                 title="Please select a folder:")
    filenames = []
    if answer: # check if not empty 
        add_files([answer])
    return filenames

def draw_preview():
    range = get_sel()
    files = listbox.get(range[0], range[1])
    paths = [filedict[file] for file in files]
    docs = pdf_reader.openDocuments(paths)
    for path in paths:
        doc = docs[path]
        for page in doc:
            pixmap = page.get_pixmap(dpi = 300)
            pixmap = fitz.Pixmap(pixmap, 0)  # remove alpha 
            # print(pixmap.tobytes())
            pixmap.save('img.png')
            img = Image.open('img.png')
            img.resize((400,400), resample=1)
            # img.show()
            img = ImageTk.PhotoImage(file='img.png')
            preview.create_image(10, 10, image=img, anchor='nw')
            print(preview.children)

listbox = tk.Listbox(root, name='dnd_demo_listbox',
                    selectmode='extended', width=1, height=1)
listbox.grid(row=1, column=0, padx=5, pady=5, sticky='news')

tk.Button(buttonbox, text='Quit', command=root.quit).pack(
                    side=tk.LEFT, padx=5)
tk.Button(buttonbox, text='Delete Selected', command = (lambda : remove_files(get_sel(), True))).pack(
                    side=tk.LEFT, padx=5)
tk.Button(buttonbox, text='Remove Selected', command = (lambda : remove_files(get_sel()))).pack(
                    side=tk.LEFT, padx=5)
tk.Button(buttonbox, text='Preview', command=draw_preview).pack(
                    side=tk.LEFT, padx=5)
tk.Button(buttonbox, text='Create PDF', command=create_pdf).pack(
                    side=tk.LEFT, padx=5)
tk.Button(buttonbox, text='Convert PDF', command=conv_pdf).pack(
                    side=tk.LEFT, padx=5)
tk.Button(buttonbox, text='Split PDF', command=lambda : split_pdf([get_sel(True)])).pack(
                    side=tk.LEFT, padx=5)

preview = tk.Canvas(root, name='preview_box', width=100, height=100, bg='red')
preview.grid(row=1, column=1, padx=5, pady=5, sticky='news')
def drop_enter(event):
    event.widget.focus_force()
    # print('Entering widget: %s' % event.widget)
    #print_event_info(event)
    return event.action
    # pass

def drop_position(event):
    # print('Position: x %d, y %d' %(event.x_root, event.y_root))
    #print_event_info(event)
    return event.action
    # pass

def drop_leave(event):
    #print('Leaving %s' % event.widget)
    #print_event_info(event)
    return event.action

def drop(event):
    if event.data:
        #print_event_info(event)
        if event.widget == listbox:
            files = listbox.tk.splitlist(event.data)
            #print(files)
            add_files(files)
        else:
            print('Error: reported event.widget not known')
    return event.action


# now make the Listbox and Text drop targets
listbox.drop_target_register(DND_FILES)

listbox.dnd_bind('<<DropEnter>>', drop_enter)
listbox.dnd_bind('<<DropPosition>>', drop_position)
listbox.dnd_bind('<<DropLeave>>', drop_leave)
listbox.dnd_bind('<<Drop>>', drop)
    #widget.dnd_bind('<<Drop:DND_Files>>', drop)
    #widget.dnd_bind('<<Drop:DND_Text>>', drop)

# define drag callbacks

def split_pdf(index):
    
    pass

def drag_init_listbox(event):
    # print_event_info(event)
    # use a tuple as file list, this should hopefully be handled gracefully
    # by tkdnd and the drop targets like file managers or text editors
    data = ()
    if listbox.curselection():
        data = tuple([listbox.get(i) for i in listbox.curselection()])
        #print('Dragging :', data)
    # tuples can also be used to specify possible alternatives for
    # action type and DnD type:
    return ((ASK, COPY), (DND_FILES, DND_TEXT), data)

def drag_end(event):
    pass

# finally make the widgets a drag source

def print_event_info(event):
    print('\nAction:', event.action)
    print('Supported actions:', event.actions)
    print('Mouse button:', event.button)
    print('Type codes:', event.codes)
    print('Current type code:', event.code)
    print('Common source types:', event.commonsourcetypes)
    print('Common target types:', event.commontargettypes)
    print('Data:', event.data)
    print('Event name:', event.name)
    print('Supported types:', event.typess)
    print('Modifier keys:', event.modifiers)
    print('Supported source types:', event.supportedsourcetypes)
    print('Operation type:', event.type)
    print('Source types:', event.sourcetypes)
    print('Supported target types:', event.supportedtargettypes)
    print('Widget:', event.widget, '(type: %s)' % type(event.widget))
    print('X:', event.x_root)
    print('Y:', event.y_root, '\n')

listbox.drag_source_register(1, DND_TEXT, DND_FILES)

listbox.dnd_bind('<<DragInitCmd>>', drag_init_listbox)
listbox.dnd_bind('<<DragEndCmd>>', drag_end)

# skip the useless drag_end() binding for the text widget

if __name__ == "__main__":
    add_files('C:\\Users\\benyo\\Code\\UCDMB_Library\\pdfs')
    preview.create_rectangle(0, 0, 100, 100, fill='red')
    root.update_idletasks()
    root.deiconify()
    root.mainloop()