from ast import List
from copy import copy
from ctypes import Array
import os
import tkinter as tk
import tkinter.filedialog
from turtle import color
from typing import Any
import fitz
from numpy import full, var
import pdf_reader as reader
from PIL import Image,ImageTk
PADDING = 10
RATIO = 8.5/11
SCALE = 1
SHIFT_HELD = 262145
IMAGE_PATH = "temp.png"
CROPBOX_ID = None
# ROTATE = 0

cv_width, cv_height = None, None
root = tk.Tk()
# temp init 
main_frame = tk.Frame(master=root)
pdf_canvas = tk.Canvas(root)
preview_canvas= tk.Canvas(root)
button_frame = tk.Frame(master=main_frame)
page:fitz.Page = None
# button temp vb init
preview_button = tk.Button()
export_button = tk.Button() 

rotate_var = tk.IntVar()
rotate_entry = tk.Entry()
fullsize_box = tk.Checkbutton()
expand_box = tk.Checkbutton()
twoinone_box = tk.Checkbutton()
fullsize_var = tk.BooleanVar()
expand_var = tk.BooleanVar()
twoinone_var = tk.BooleanVar()

path:str = None
tl = fitz.Point(5,5)
br = fitz.Point(100,100)
page_br = fitz.Point()
page_image = Image.Image()

# get filepath from dialog
def openFile() -> str: 
        # get file info
        answer = tkinter.filedialog.askopenfile(parent=root,
                                 initialdir=os.getcwd(),
                                 title="Please select a file:",filetypes=[('Pdf File', '*.pdf')])
        # return filepath
        return answer.name

# get page sized tk.PhotoImage from a fitz.Page 
def getPageScaledImage(page: fitz.Page) -> tk.PhotoImage:
    global page_image
    width, height = page.bound().br
    print(width, height)
    pixmap= page.get_pixmap(dpi=300)
    pixmap.save(IMAGE_PATH)
    page_image = Image.open(IMAGE_PATH)
    page_image = page_image.resize(size=(int(width), int(height)))
    return ImageTk.PhotoImage(page_image)

# draw current cropbox onto pdf_canvas, replacing previous
def drawCropBox() -> None:
    # clear previous box, if any
    global CROPBOX_ID
    if (CROPBOX_ID):
        pdf_canvas.delete(CROPBOX_ID)
    CROPBOX_ID = pdf_canvas.create_rectangle(tl.x, tl.y, br.x, br.y,outline='dodger blue',width=1)
    # pdf_canvas.create_rectangle(10,10,100,100)

def onKeyPress(event):
    global tl, br
    sym = event.keysym
    negative = False
    if event.state == SHIFT_HELD:
         negative = True
    if sym == 'Left':
        if negative:
            tl.x = tl.x - 1
        else:
            br.x = br.x - 1
    elif sym == 'Up':
        if negative:
            tl.y = tl.y - 1
        else:
            br.y = br.y - 1
    elif sym == 'Right':
        if negative:
            tl.x = tl.x  + 1
        else:
            br.x = br.x + 1
    elif sym == 'Down':
        if negative:
            tl.y = tl.y + 1
        else:
            br.y = br.y + 1
    else:
        return
    drawCropBox()

# using current settings, create settings string for processing module
def getSettingsDict() -> dict[str, any]:
    args = {}
    args['margins'] = (int(tl.x), int(tl.y), int(page_br.x - br.x), int(page_br.y - br.y))
    args['full_size'] = fullsize_var.get()
    args['two_in_one'] = twoinone_var.get()
    args['expand'] = expand_var.get()
    args['rotate'] = getRotation()    
    return args

def getSettingsString() -> str:
    global page_br
    args = getSettingsDict()
    out = ''
    for v in args.values():
        if  type(v) is tuple:
            for n in v:
                out += str(n) + ' '
        else: 
            out += str(v) + ' '
    return out

def printSettingsString() -> None:
    print(getSettingsString())

# get rotation from entry box, sanitize input
def getRotation() -> int:
    global rotate_entry
    rotation = rotate_entry.get()
    try:
        rotation = int(rotation)
        if not (rotation in [0,90,270]):
            raise Exception('invalid rotation value')
    except:
        # print('invalid rotation value')
        rotate_entry.delete(0)
        rotation = 0
    return rotation

def createPreview():
    global root, path
    args = getSettingsDict()
    doc = reader.openDocuments(path)[path]
    # alter document using settings 
    newdoc = reader.duplicateAndScale(doc,**args)
    new_br = newdoc[0].bound().br
    # create new window to show altered document
    preview_window = tk.Toplevel(master=root)
    preview_window.title('Crop preview')
    preview_window.geometry('{0}x{1}'.format(int(new_br.x), int(new_br.y)))
    preview_window.img = img = getPageScaledImage(newdoc[0])
    preview_canvas = tk.Canvas(preview_window,bg='pink',width=new_br.x,height=new_br.y)
    preview_canvas.create_image(2,2,image=img,anchor='nw')
    preview_canvas.pack()

# rotate viewing frame to match with rotation value
def updateRotation() -> None:
    # global main_frame, pdf_canvas, rotate_var,page_image,page_br
    # # rotate pdf_canvas width and height, repack gui elements
    # rotation = rotate_var.get()
    # pdf_canvas.delete('all')
    # if rotation == 90:
    #     pdf_canvas.config(width=page_br.y,height=page_br.x)
    #     rotated = page_image.rotate(90)
    # else:
    #     pdf_canvas.config(width=page_br.x,height=page_br.y)
    #     rotated = page_image.rotate(0)
    # # rotated.show()
    # new_photoimage = ImageTk.PhotoImage(rotated)
    # new_photoimage.
    # pdf_canvas.create_image(2,2,image=new_photoimage,anchor='nw')
    drawCropBox()

def init():
    global pdf_canvas, main_frame, root, tl, br, button_frame, path, cv_width, cv_height, page_br
    global rotate_var, rotate_entry, fullsize_box, fullsize_label, export_button, preview_button
    global twoinone_box
    print('creating window...')
    root.title("Crop pdf")
    root.geometry("1000x1000")
    path = openFile()
    # path = 'C:\\Users\\benyo\\Code\\UCDMB_Library\\pdfs\\Everybody Talks-Tenor_Saxophone.pdf'
    doc = reader.openDocuments(path)[path]
    page = doc[0]
    page_br = page.bound().br
    # set up canvases 
    cv_width, cv_height = (page_br.x * SCALE,page_br.y * SCALE)
    main_frame = tk.Frame(master=root,width=cv_width * 2 + PADDING * 4, height = cv_height + PADDING * 4,bg='red')
    button_frame = tk.Frame(master=main_frame,bg='green',height=10,width =cv_width)
    pdf_canvas = tk.Canvas(master=main_frame, width = cv_width, height=cv_height, bg='yellow')
    # preview_canvas= tk.Canvas(master=main_frame, width = cv_width, height = cv_height, bg = 'blue')
    
    pdf_canvas.grid(row=0,column=0,sticky='ew',padx=PADDING,pady=PADDING)
    # preview_canvas.grid(row=0,column=1,sticky='ew',padx=PADDING,pady=PADDING)
    preview_button = tk.Button(button_frame, command=createPreview,
                               width = 10, height = 1,text='Create Preview')
    export_button = tk.Button(button_frame, command=printSettingsString,
                              width = 10, height = 1,text='Export Settings')
    rotate_label = tk.Label(button_frame, text='Rotation')
    rotate_entry = tk.Entry(button_frame)
    fullsize_label = tk.Label(button_frame, text='Full Size?')
    fullsize_box = tk.Checkbutton(button_frame, variable = fullsize_var)
    expand_label = tk.Label(button_frame, text='Expand?')
    expand_box = tk.Checkbutton(button_frame, variable = expand_var)
    twoinone_label = tk.Label(button_frame, text='Two in one?')
    twoinone_box = tk.Checkbutton(button_frame, variable = twoinone_var)
    
    # rotate_entry.insert(0,'0')
    button_frame.grid(row=0,column=1,sticky='nw',pady=PADDING,padx=PADDING)
    preview_button.grid(row=0,column=0,sticky='nwes')
    export_button.grid(row=0,column=1,sticky='nwes')
    rotate_entry.grid(row=1,column=1,sticky='nwes')
    rotate_label.grid(row=1,column=0,sticky ='nwes')
    fullsize_label.grid(row=2,column=0,sticky = 'nwes')
    fullsize_box.grid(row=2,column=1,sticky = 'nwes')
    expand_label.grid(row=3,column=0,sticky = 'nwes')
    expand_box.grid(row=3,column=1,sticky = 'nwes')
    twoinone_label.grid(row=4,column=0,sticky = 'nwes')
    twoinone_box.grid(row=4,column=1,sticky = 'nwes')
    main_frame.pack(padx=PADDING,pady=PADDING,fill='none')
    # pdf_canvas.pack(padx=PADDING,pady=PADDING)

    # create buttons

    # draw page to the canvas
    page_image = getPageScaledImage(page)
    pdf_canvas.create_image(2,2,image=page_image,anchor='nw')
    tl = fitz.Point(2,2)
    br = copy(page_br)
    drawCropBox()
    root.bind('<KeyPress>', onKeyPress)
    root.mainloop()

if __name__ == "__main__":
    init()    
# translate points between canvas pixels and pdf points      
# show preview