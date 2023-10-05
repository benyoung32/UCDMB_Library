from ast import List
from copy import copy
from ctypes import Array
from doctest import master
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

class CropTool(tk.Toplevel):
    def __init__(self,filepath=None):
        super().__init__()
        self.title("Crop pdf")
        self.geometry("1000x1000")
        if not filepath:
            self.path = self.openFile()
        else:
            self.path = filepath
        # path = 'C:\\Users\\benyo\\Code\\UCDMB_Library\\pdfs\\Everybody Talks-Tenor_Saxophone.pdf'
        doc = reader.openDocuments(path)[path]
        page = doc[0]
        page_br = page.bound().br
        # set up canvases 
        cv_width, cv_height = (page_br.x * SCALE,page_br.y * SCALE)
        self.main_frame = tk.Frame(master=root,width=cv_width * 2 + PADDING * 4, height = cv_height + PADDING * 4,bg='red')
        self.button_frame = tk.Frame(master=main_frame,bg='green',height=10,width =cv_width)
        self.pdf_canvas = tk.Canvas(master=main_frame, width = cv_width, height=cv_height, bg='yellow')
        # preview_canvas= tk.Canvas(master=main_frame, width = cv_width, height = cv_height, bg = 'blue')
        
        self.pdf_canvas.grid(row=0,column=0,sticky='ew',padx=PADDING,pady=PADDING)
        # preview_canvas.grid(row=0,column=1,sticky='ew',padx=PADDING,pady=PADDING)
        self.preview_button = tk.Button(button_frame, command=createPreview,
                                width = 10, height = 1,text='Create Preview')
        self.export_button = tk.Button(button_frame, command=printSettingsString,
                                width = 10, height = 1,text='Export Settings')
        self.crop_folder_button = tk.Button(button_frame, command=cropFolder,
                                width = 20, height = 1, text = 'Apply to folder')
        self.rotate_label = tk.Label(button_frame, text='Rotation')
        self.rotate_entry = tk.Entry(button_frame)
        self.fullsize_label = tk.Label(button_frame, text='Full Size?')
        self.fullsize_box = tk.Checkbutton(button_frame, variable = fullsize_var)
        self.expand_label = tk.Label(button_frame, text='Expand?')
        self.expand_box = tk.Checkbutton(button_frame, variable = expand_var)
        self.twoinone_label = tk.Label(button_frame, text='Two in one?')
        self.twoinone_box = tk.Checkbutton(button_frame, variable = twoinone_var)
        self.rightalign_label = tk.Label(button_frame, text='Right align?')
        self.rightalign_box = tk.Checkbutton(button_frame, variable = rightalign_var)
         # rotate_entry.insert(0,'0')
        self.button_frame.grid(row=0,column=1,sticky='nw',pady=PADDING,padx=PADDING)
        self.preview_button.grid(row=0,column=0,sticky='nwes')
        self.export_button.grid(row=0,column=1,sticky='nwes')
        self.crop_folder_button.grid(row=6,column=0,sticky='nwes')
        self.rotate_entry.grid(row=1,column=1,sticky='nwes')
        self.rotate_label.grid(row=1,column=0,sticky ='nwes')
        self.fullsize_label.grid(row=2,column=0,sticky = 'nwes')
        self.fullsize_box.grid(row=2,column=1,sticky = 'nwes')
        self.expand_label.grid(row=3,column=0,sticky = 'nwes')
        self.expand_box.grid(row=3,column=1,sticky = 'nwes')
        self.twoinone_label.grid(row=4,column=0,sticky = 'nwes')
        self.twoinone_box.grid(row=4,column=1,sticky = 'nwes')
        self.rightalign_label.grid(row=5,column=0,sticky = 'nwes')
        self.rightalign_box.grid(row=5,column=1,sticky = 'nwes')
        self.main_frame.pack(padx=PADDING,pady=PADDING,fill='none')
        myimage = getPageScaledImage(page)
        pdf_canvas.create_image(2,2,image=myimage,anchor='nw')
        tl = fitz.Point(2,2)
        br = copy(page_br)
        self.drawCropBox()
        self.bind('<KeyPress>', onKeyPress)
        self.mainloop()

    def openFile(self) -> str: 
        # get file info
        answer = tkinter.filedialog.askopenfile(parent=self,
                                initialdir=os.getcwd(),
                                title="Please select a file:",filetypes=[('Pdf File', '*.pdf')])
        # return filepath
        return answer.name

    # get page sized tk.PhotoImage from a fitz.Page 
    def getPageScaledImage(self, page: fitz.Page) -> tk.PhotoImage:
        # global page_image
        width, height = page.bound().br
        # print(width, height)
        savePageImage(page, IMAGE_PATH)
        page_image = Image.open(IMAGE_PATH)
        # page_image.load()
        page_image = page_image.resize(size=(int(width), int(height)))
        my_image = img = ImageTk.PhotoImage(page_image,master=root)
        # print(my_image)
        return my_image

    def savePageImage(self, page: fitz.Page, filepath:str)-> None:
        pixmap= page.get_pixmap(dpi=300)
        pixmap.save(filepath)

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

    def getSettingsDict() -> dict[str, any]:
        args = {}
        args['filename'] = path
        args['margins'] = (int(tl.x), int(tl.y), int(page_br.x - br.x), int(page_br.y - br.y))
        args['full_size'] = fullsize_var.get()
        args['two_in_one'] = twoinone_var.get()
        args['expand'] = expand_var.get()
        args['right_align'] = rightalign_var.get()
        args['rotate'] = getRotation()    
        # print(args)
        # print(fullsize_var.get())    
        return args

    def getSettingsString() -> str:
        global page_br
        args = getSettingsDict()
        out = '\"' + path + '\"' 
        for v in ['full_size','two_in_one','expand','right_align']:
            if args[v]:
                out += ' -' + v
        for n in args['margins']:
            out += ' ' + str(n)
        out += ' ' + str(args['rotate'])
        return out

    def printSettingsString() -> None:
        print(getSettingsString())

    # apply current settings to the folder where the sample came from
    def cropFolder() -> None:
        # print(path)
        folder= os.path.dirname(path)
        files = reader.getSubFiles(folder)
        # print(files)
        reader.processDocs(files, reader.prefix, **getSettingsDict())
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
        # print(args)
        doc = reader.openDocuments(path,size='a4')[path]
        # alter document using settings 
        newdoc = reader.createCroppedDocument(doc,**args)
        # newdoc.save('hm.pdf',deflate = True, 
        #             deflate_images = True, garbage = 4, clean = True)
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

class LabeledEntry():
    def __init__():


if __name__ == "__main__":
    CropTool()    
# show preview