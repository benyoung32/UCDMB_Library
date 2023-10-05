from copy import copy
import os
import tkinter as tk
# import copy as copy
import tkinter.filedialog
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
    def __init__(self,parent,filepath=None):
        super().__init__(parent)
        self.title("Crop pdf")
        self.geometry("1000x1000")
        self.rotate_var = tk.IntVar(self)
        self.rightalign_var = tk.BooleanVar(self)
        self.fullsize_var = tk.BooleanVar(self)
        self.expand_var = tk.BooleanVar(self)
        self.twoinone_var = tk.BooleanVar(self)

        if not filepath:
            self.path = self.openFile()
        else:
            self.path = filepath
        # path = 'C:\\Users\\benyo\\Code\\UCDMB_Library\\pdfs\\Everybody Talks-Tenor_Saxophone.pdf'
        doc = reader.openDocuments(self.path)[self.path]
        page = doc[0]
        page_br = page.bound().br
        # set up canvases 
        self.cv_width, self.cv_height = (page_br.x * SCALE,page_br.y * SCALE)
        self.main_frame = tk.Frame(master=self,
                    width=self.cv_width * 2 + PADDING * 4, 
                    height = self.cv_height + PADDING * 4,bg='red')
        self.button_frame = tk.Frame(master=self.main_frame,
                    bg='green',height=10,width =self.cv_width)
        self.pdf_canvas = tk.Canvas(master=self.main_frame, 
                    width = self.cv_width, height=self.cv_height, bg='yellow')
        # preview_canvas= tk.Canvas(master=main_frame, width = cv_width, height = cv_height, bg = 'blue')
        
        self.pdf_canvas.grid(row=0,column=0,sticky='ew',padx=PADDING,pady=PADDING)
        # preview_canvas.grid(row=0,column=1,sticky='ew',padx=PADDING,pady=PADDING)
        self.preview_button = tk.Button(self.button_frame, command=self.createPreview,
                                width = 10, height = 1,text='Create Preview')
        self.export_button = tk.Button(self.button_frame, command=self.printSettingsString,
                                width = 10, height = 1,text='Export Settings')
        self.crop_folder_button = tk.Button(self.button_frame, command=self.cropFolder,
                                width = 20, height = 1, text = 'Apply to folder')
        self.rotate_entry = EntryWithLabel(self.button_frame,'Rotate?','')
        self.fullsize_box = CheckButtonWithLabel(self.button_frame, 
                                                'Full Size?',self.fullsize_var )
        self.expand_box = CheckButtonWithLabel(self.button_frame,
                                                'Expand?', self.expand_var)
        self.twoinone_box = CheckButtonWithLabel(self.button_frame,
                                                'Two in one?',self.twoinone_var)
        self.rightalign_box = CheckButtonWithLabel(self.button_frame, 
                                                'Right Align?', self.rightalign_var)
        self.button_frame.grid(row=0,column=1,sticky='nw',pady=PADDING,padx=PADDING)
        self.preview_button.grid(row=0,column=0,sticky='nwes')
        self.export_button.grid(row=0,column=1,sticky='nwes')
        self.crop_folder_button.grid(row=6,column=0,sticky='nwes')
        self.rotate_entry.grid(row=1,column=0,sticky='nwes',columnspan=2)
        self.fullsize_box.grid(row=2,column=0,sticky = 'nwes',columnspan=2)
        self.expand_box.grid(row=3,column=0,sticky = 'nwes',columnspan=2)
        self.twoinone_box.grid(row=4,column=0,sticky = 'nwes',columnspan=2)
        self.rightalign_box.grid(row=5,column=0,sticky = 'nwes',columnspan=2)
        self.main_frame.pack(padx=PADDING,pady=PADDING,fill='none')
        myimage = self.getPageScaledImage(page)
        self.pdf_canvas.create_image(2,2,image=myimage,anchor='nw')
        self.tl = fitz.Point(2,2)
        self.br = copy(page_br)
        self.drawCropBox()
        self.bind('<KeyPress>', self.onKeyPress)
        self.grab_set()
        self.mainloop()

    def openFile(self) -> str: 
        # get file info
        answer = tk.filedialog.askopenfile(parent=self,
                                initialdir=os.getcwd(),
                                title="Please select a file:",filetypes=[('Pdf File', '*.pdf')])
        # return filepath
        return answer.name

    # get page sized tk.PhotoImage from a fitz.Page 
    def getPageScaledImage(self, page: fitz.Page) -> tk.PhotoImage:
        # global page_image
        width, height = page.bound().br
        # print(width, height)
        self.savePageImage(page, IMAGE_PATH)
        page_image = Image.open(IMAGE_PATH)
        # page_image.load()
        page_image = page_image.resize(size=(int(width), int(height)))
        my_image = img = ImageTk.PhotoImage(page_image,master=self)
        # print(my_image)
        return my_image

    def savePageImage(self, page: fitz.Page, filepath:str)-> None:
        pixmap= page.get_pixmap(dpi=300)
        pixmap.save(filepath)

    # draw current cropbox onto pdf_canvas, replacing previous
    def drawCropBox(self) -> None:
        if (CROPBOX_ID):
            self.pdf_canvas.delete(CROPBOX_ID)
        self.CROPBOX_ID = self.pdf_canvas.create_rectangle(self.tl.x, 
                        self.tl.y, self.br.x, self.br.y,outline='dodger blue',width=1)
        # pdf_canvas.create_rectangle(10,10,100,100)

    def onKeyPress(self,event):
        tl, br = self.tl, self.br
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
        self.drawCropBox()

    def getSettingsDict(self) -> dict[str, any]:
        args = {}
        args['filename'] = self.path
        args['margins'] = (int(tl.x), int(tl.y), int(page_br.x - br.x), int(page_br.y - br.y))
        args['full_size'] = self.fullsize_var.get()
        args['two_in_one'] = self.twoinone_var.get()
        args['expand'] = self.expand_var.get()
        args['right_align'] = self.rightalign_var.get()
        args['rotate'] = self.getRotation()    
        # print(args)
        # print(fullsize_var.get())    
        return args

    def getSettingsString(self) -> str:
        global page_br
        args = self.getSettingsDict()
        out = '\"' + self.path + '\"' 
        for v in ['full_size','two_in_one','expand','right_align']:
            if args[v]:
                out += ' -' + v
        for n in args['margins']:
            out += ' ' + str(n)
        out += ' ' + str(args['rotate'])
        return out

    def printSettingsString(self) -> None:
        print(self.getSettingsString())

    # apply current settings to the folder where the sample came from
    def cropFolder(self) -> None:
        # print(path)
        folder= os.path.dirname(self.path)
        files = reader.getSubFiles(folder)
        # print(files)
        reader.processDocs(files, reader.prefix, **self.getSettingsDict())
    # get rotation from entry box, sanitize input
    def getRotation(self) -> int:
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

    def createPreview(self):
        args = self.getSettingsDict()
        # print(args)
        doc = reader.openDocuments(self.path,size='a4')[path]
        # alter document using settings 
        newdoc = reader.createCroppedDocument(doc,**args)
        # newdoc.save('hm.pdf',deflate = True, 
        #             deflate_images = True, garbage = 4, clean = True)
        new_br = newdoc[0].bound().br
        # create new window to show altered document
        preview_window = tk.Toplevel(master=self)
        preview_window.title('Crop preview')
        preview_window.geometry('{0}x{1}'.format(int(new_br.x), int(new_br.y)))
        preview_window.img = img = self.getPageScaledImage(newdoc[0])
        preview_canvas = tk.Canvas(preview_window,bg='pink',width=new_br.x,height=new_br.y)
        preview_canvas.create_image(2,2,image=img,anchor='nw')
        preview_canvas.pack()

    # rotate viewing frame to match with rotation value
    def updateRotation(self) -> None:
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
        self.drawCropBox()

class EntryWithLabel(tk.Frame):
    def __init__(self, parent, label, default="") -> None:
        tk.Frame.__init__(self, parent)
        self.label = tk.Label(self, text=label, anchor="w")
        self.entry = tk.Entry(self)
        self.entry.insert(0, default)
        self.label.pack(side="left", fill="x")
        self.entry.pack(side="right", fill="x", padx=4)
   
    def get(self) -> str:
        return self.entry.get()

class CheckButtonWithLabel(tk.Frame):
    def __init__(self, parent, label, var) -> None:
        tk.Frame.__init__(self, parent)
        self.label = tk.Label(self, text=label, anchor="w")
        self.checkbutton = tk.Checkbutton(self,variable=var)
        self.label.pack(side="left", fill="x")
        self.checkbutton.pack(side="right", fill="x", padx=4)

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    CropTool(root)
    root.destroy()    
# show preview